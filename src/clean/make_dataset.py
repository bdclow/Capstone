'''
Script to create our basic cleaned dataset
'''
import argparse
from os import path, mkdir, listdir
import logging
import yaml
import pandas
from src.clean.dataset import DataSet
from src import data_dir, parent_dir
from tqdm import tqdm

pandas.options.mode.chained_assignment = None


def load_config(filepath: str) -> dict:
    '''
    Loads Column information from YAML
    YAML specifies columns to use, along with datatype
    Optional filter parameter as well 
        (filters based on matching of value)
    '''
    with open(filepath, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def open_starts_and_create_target(csv_prefix, config: dict) -> pandas.DataFrame:
    '''
    open and filter skillshare starts
    this is our first table which everything else
        gets joined to
    '''
    filepath = f"{csv_prefix}_starts.csv"
    starts = DataSet(filepath, config["starts"])
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

def list_of_data_files():
    '''
    Walk dir and return files
    '''
    return [ file for file in listdir(data_dir) ]


def convert_cols(
        row: pandas.Series, 
        prev_col: str, 
        day: int
    ) -> pandas.Series:
    '''
    Wrapper to figure out relative day of trial
        day in integer form, takes negative days / indexes
        (e.g. takes "-1" and returns 6 if trial length 7)
    '''
    day_converted = row["trial_length_days"] + day
    return row[(prev_col, day_converted)]


def open_video_views(
        csv_prefix: str,
        config: dict
    ) -> pandas.DataFrame:
    '''
    Open all files with video view information
    Find by string matching
    Ensures correct data types for columns
    Returns concatenated whole for dataset as Pandas DF
    '''
    data_files = list_of_data_files()
    vviews_files = [ file for file in data_files if f"{csv_prefix}_vviews" in str(file) ]
    video_views = [
            DataSet(
                file,
                config["video_views"],
                log=False)
            for file in vviews_files
    ]
    return pandas.concat([vv.dataframe() 
        for vv in tqdm(video_views, desc="Loading video views dataset")])

def get_watchtime_by_subcategory(
        video_views: pandas.DataFrame,
        config: dict
    ) -> pandas.DataFrame:
    '''
    Takes video view information and calculates average time spent
    in each subcategory ('Photography', 'Illustration', 'Culinary', 
    'Graphic Design', 'Marketing', 'Creative Writing', etc)
    '''
    classes = DataSet(
            "skillshare_2022_classes.csv",
            config["classes"])\
                    .dataframe()\
                    .reset_index()

    # tack on class subcategory info onto video views
    video_views = pandas.merge(
        video_views.reset_index(),
        classes[["class_id", "subcategory"]],
        on="class_id",
        how="left")

    watchtime_by_subcategory = video_views.groupby([
        "uid",
        "subcategory"])\
        .sum()["sum"]\
        .reset_index()\
        .pivot(
            index="uid",
            columns="subcategory",
            values="sum")\
        .fillna(0.0)

    # for memory purposes, immediately drop table
    del classes

    # Sum for total watchtime
    watchtime_by_subcategory["total_video_watchtime"] = watchtime_by_subcategory\
            .sum(axis=1)

    # Convert to percentage
    for col in watchtime_by_subcategory.columns[:-2]:
        watchtime_by_subcategory[col] = watchtime_by_subcategory[col] / \
            watchtime_by_subcategory["total_video_watchtime"]

    return watchtime_by_subcategory.reset_index()\
            .fillna(0.0)\
            .drop(columns="total_video_watchtime")\
            .rename(columns={
                "uid": "user_uid",              # rename for consistency
                "Other": "other_subcategory"})  # avoid conflict with payer source column

# Progress bar for pandas .apply()
tqdm.pandas(desc="Converting day of trial to relative day")

def get_by_day_of_trial(
        starts: pandas.DataFrame,
        video_views: pandas.DataFrame
    ) -> pandas.DataFrame:
    '''
    Group video views by day of trial
    '''
    # JOIN starts and views
    account_and_views_info = pandas.merge(
        starts,
        video_views,
        left_on="user_uid",
        right_on="uid",
        how="left")

    # Create column for watch data, corresponds to the day after trial start
    account_and_views_info["day_of_trial"] = account_and_views_info.view_date - \
        account_and_views_info.create_time
    account_and_views_info.dropna(subset=["day_of_trial"], inplace=True)

    # Cut back on DF size, only using these days anyway
    account_and_views_info = account_and_views_info[
        (account_and_views_info.day_of_trial.dt.days < 31) &
        (account_and_views_info.day_of_trial.dt.days > 0)]

    # Truncate day of trial from timedelta to just an integer
    account_and_views_info.day_of_trial = account_and_views_info\
            .day_of_trial.dt.days

    # finally pivot days for both time watched (sum) and length of video
    views_by_trial_day = account_and_views_info.groupby([
        "user_uid",
        "day_of_trial"])\
        .agg({"sum": "sum", "video_duration": "sum"})\
        .reset_index()\
        .pivot(
            index="user_uid",
            columns="day_of_trial",
            values=["sum", "video_duration"])

    # Add trial length col back to pivoted table
    views_by_trial_day = pandas.merge(
        views_by_trial_day.reset_index(),
        starts[["trial_length_days", "user_uid"]],
        left_on="user_uid",
        right_on="user_uid")

    # Only use the first 3 days and the last 3 days of trial
    days = [1, 2, 3]
    last_days = [-3, -2, -1]

    for day in days:
        views_by_trial_day[f"total_watchtime_day_{day}"] = views_by_trial_day[(
            'sum', day)]
        views_by_trial_day[f"watched_video_length_day_{day}"] = views_by_trial_day[(
            'video_duration', day)]

    for day in last_days:
        views_by_trial_day[f"total_watchtime_day_{day}"] = views_by_trial_day\
                .progress_apply(
                    lambda row: convert_cols(row, "sum", day), 
                    axis=1)
        views_by_trial_day[f"watched_video_length_day_{day}"] = views_by_trial_day\
                .progress_apply(
                    lambda row: convert_cols(row, "video_duration", day), 
                    axis=1)

    cols_to_keep = [col for col in views_by_trial_day.columns
                    if "total_watchtime" in col or "video_length" in col]
    cols_to_keep.insert(0, "user_uid")

    return views_by_trial_day[cols_to_keep].fillna(0.0)



def combine_datasets(
        csv_prefix: str,
        config: dict) -> pandas.DataFrame:
    '''
    Series of joins to make full cleaned dataset
    '''
    # Subscription sign-ups/starts dataframe, starting point
    starts_df = open_starts_and_create_target(csv_prefix, config)
    video_views_df = open_video_views(csv_prefix, config)
    views_by_cat = get_watchtime_by_subcategory(video_views_df, config)
    views_by_day = get_by_day_of_trial(starts_df, video_views_df)

    del video_views_df
    views_info = pandas.merge(
        views_by_day,
        views_by_cat,
        on="user_uid",
        how="inner"
    )

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
    # NOTE: chose INNER join here
    # otherwise NaN rows for views info
    final_df = pandas.merge(
        starts_df,
        views_info,
        how="inner",
        on="user_uid")

    # Merge with demographic information 
    # NOTE: chose INNER join here
    # otherwise NaN rows for meta info
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

    parser.add_argument(
            '--csv_prefix',
            help='prefix to csv file (e.g. skillshare, new, etc.)')
    parser.add_argument('--output_directory')
    args = parser.parse_args()

    if args.output_directory:
        data_directory = args.target_dir
    else:
        data_directory = data_dir

    if args.csv_prefix:
        csv_prefix = args.csv_prefix
        outfile = f"{csv_prefix}_cleaned.parquet"
    else:
        csv_prefix = 'skillshare_2022'
        outfile = "cleaned.parquet"

    # Find YAML file and load
    script_path = path.abspath(__file__)
    script_dir = parent_dir(script_path)
    config = load_config(path.join(script_dir, "dataset.yml"))

    logging.info("LOADING DATASETS, JOINING...")

    # Load and combine datasets
    cleaned_df = combine_datasets(csv_prefix, config)

    # Save dataset to parquet file within data dir
    cleaned_dir = path.join(data_directory, "cleaned")
    if not path.exists(cleaned_dir):
        mkdir(cleaned_dir)
    outfilepath = path.join(cleaned_dir, outfile)
    cleaned_df.to_parquet(outfilepath)
    logging.info(f"Cleaned dataset ({csv_prefix}) saved to {outfilepath}")


main()
