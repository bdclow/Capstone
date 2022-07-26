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
pandas.options.mode.chained_assignment = None


# console logging setup
logging.basicConfig(
    format='%(asctime)s %(message)s',
    encoding='utf-8',
    level=logging.DEBUG)


def load_config(filepath: str):
    '''
    Loads Column information from YAML
    YAML specifies columns to use, along with datatype
    Optional filter parameter as well 
        (filters based on matching of value)
    '''
    with open(filepath, "r") as file:
        return yaml.safe_load(file)

def open_starts_and_create_target(config: dict):
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

def combine_datasets(config: dict):
    '''
    Series of joins to make full cleaned dataset
    '''
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

    views_by_trial_day = DataSet(
        "watch_time_by_trial_day.csv", 
        config["watch_time_by_trial_day"])

    #classes = DataSet("skillshare_2022_classes.csv", config["classes"])
    
    # Merge with video views
    final_df = pandas.merge(
        starts_df,
        views_by_trial_day.dataframe().fillna(0.0),
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

    args = parser.parse_args()

    if args.output_directory:
        data_directory = args.target_dir
    else:
        data_directory = data_dir

    # Find YAML file and load
    script_path = path.abspath(__file__)
    script_dir = parent_dir(script_path)
    config = load_config(path.join(script_dir, "dataset.yml"))

    # Load and combine datasets
    cleaned_df = combine_datasets(config)

    # Save dataset to parquet file within data dir
    cleaned_dir = path.join(data_directory, "cleaned")
    if not path.exists(cleaned_dir):
        mkdir(cleaned_dir)
    outfile = path.join(cleaned_dir, "cleaned.parquet")
    cleaned_df.to_parquet(outfile)
    logging.info(f"Cleaned dataset saved to {outfile}")


main()
