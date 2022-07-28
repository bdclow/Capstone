'''
Script to create our basic cleaned dataset
'''
import argparse
from os import path, mkdir
import logging
import yaml
from src.clean.dataset import DataSet
from src import data_dir, parent_dir
import pandas
from tqdm import tqdm
pandas.options.mode.chained_assignment = None


def load_config(filepath: str) -> dict:
    '''
    Loads Column information from YAML
    YAML specifies columns to use, along with datatype
    Optional filter parameter as well 
        (filters based on matching of value)
    '''
    with open(filepath, "r") as file:
        return yaml.safe_load(file)

def open_starts_and_create_target(config: dict) -> pandas.DataFrame:
    '''
    open and filter skillshare starts
    this is our first table which everything else
        gets joined to
    '''
    starts = DataSet("skillshare_2022_starts.csv", config["starts"])
    starts_df = starts.dataframe(one_hot_categories=True)
    # add a successful conversion column.
    starts_df['success'] = 0
    # set to 1 if they paid
    starts_df['success'][starts_df['first_payment_time'].notnull()] = 1
    # return to 0 if they got a refund.
    starts_df['success'][starts_df['is_refunded'] == 1] = 0
    # drop leaky columns
    starts_df = starts_df.drop(['first_payment_time', 'is_refunded'], axis=1)

    return starts_df

def open_video_views(config: dict) -> pandas.DataFrame:
    '''
    Open all 62 files with video view information
    Ensures correct data types for columns
    Returns concatenate whole for dataset as Pandas DF
    '''
    video_views = [
            DataSet(f"skillshare_2022_vviews_{i}.csv",
                config["video_views"])
            for i in range(0, 63)
            # files are numbered from 0 to 62
    ]
    return pandas.concat([vv.dataframe() 
        for vv in tqdm(video_views, desc="Loading video views dataset")])

def get_watchtime_by_subcategory(config: dict) -> pandas.DataFrame:
    '''
    Takes video view information and calculates average time spent
    in each subcategory ('Photography', 'Illustration', 'Culinary', 'Graphic Design',
       'Marketing', 'Creative Writing', etc)
    '''
    classes = DataSet(
            "skillshare_2022_classes.csv", 
            config["classes"])\
                    .dataframe()\
                    .reset_index()

    video_views_df = open_video_views(config)
    # tack on class subcategory info onto video views
    video_views_df = pandas.merge(
        video_views_df.reset_index(),
        classes[["class_id", "subcategory"]],
        on="class_id",
        how="left")

    watchtime_by_subcategory = video_views_df.groupby([
        "uid",
        "subcategory"])\
        .sum()["sum"]\
        .reset_index()\
        .pivot(
            index="uid",
            columns="subcategory",
            values="sum")\
        .fillna(0.0)

    # for memory purposes, immediately drop tables
    del video_views_df
    del classes

    watchtime_by_subcategory["total_video_watchtime"] = watchtime_by_subcategory.sum(axis=1)

    # Convert to percentage
    for col in watchtime_by_subcategory.columns[:-2]:
        watchtime_by_subcategory[col] = watchtime_by_subcategory[col] / \
            watchtime_by_subcategory["total_video_watchtime"]

    return watchtime_by_subcategory.reset_index()\
            .rename(columns={
                "uid": "user_uid",              # rename for consistency
                "Other": "other_subcategory"})  # avoid conflict with payer source column


def combine_datasets(
        config: dict, 
        categories: bool
    ) -> pandas.DataFrame:
    '''
    Series of joins to make full cleaned dataset
    '''
    if categories:
        views_info = get_watchtime_by_subcategory(config)
    else:
        views_by_trial_day = DataSet(
            "watch_time_by_trial_day.csv", 
            config["watch_time_by_trial_day"])
        views_info = views_by_trial_day.dataframe().fillna(0.0)

    # Subscription sign-ups/starts dataframe, starting point
    starts_df = open_starts_and_create_target(config)

    # Load demographic data with OHEs, but only
    # keep english-speaking countries as otherwise
    # gets a bit sparse
    subscription_metainformation = DataSet(
        "skillshare_subs_meta.csv", 
        config["subs_meta"])

    anglophone_countries = config['countries_to_keep']
    subs_df = subscription_metainformation.dataframe(
            one_hot_categories=True)[anglophone_countries]

    # Merge with video views
    final_df = pandas.merge(
        starts_df,
        views_info,
        how="left",
        on="user_uid")

    # Merge with demographic information 
    final_df = pandas.merge(
        final_df,
        subs_df,
        how="left",
        on="user_uid")

    return final_df
    

def main():
    # take CLI arguments
    parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='created cleaned dataset for modeling')
    parser.add_argument('--output_directory')
    parser.add_argument('--categories',
        action='store_true', 
        help="whether to group video view info by categories")

    args = parser.parse_args()

    if args.output_directory:
        data_directory = args.target_dir
    else:
        data_directory = data_dir

    # Find YAML file and load
    script_path = path.abspath(__file__)
    script_dir = parent_dir(script_path)
    config = load_config(path.join(script_dir, "dataset.yml"))

    if args.categories:
        logging.info("Adding on category info as well")
        filename = "cleaned_w_video_views_breakdowns.parquet"
    else:
        filename = "cleaned.parquet"

    # Load and combine datasets
    cleaned_df = combine_datasets(config, args.categories)

    # Save dataset to parquet file within data dir
    cleaned_dir = path.join(data_directory, "cleaned")
    if not path.exists(cleaned_dir):
        mkdir(cleaned_dir)
    outfilepath = path.join(cleaned_dir, filename)
    cleaned_df.to_parquet(outfilepath)
    logging.info(f"Cleaned dataset saved to {outfilepath}")


main()
