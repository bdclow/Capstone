import argparse
from os import path, mkdir
import logging
import yaml
from src.clean.dataset import DataSet
from src import data_dir, script_path, parent_dir
import pandas
pandas.options.mode.chained_assignment = None

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


def main():
    parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='created cleaned dataset for modeling')
    parser.add_argument('--output_directory')

    args = parser.parse_args()

    if args.output_directory:
        data_directory = args.target_dir
    else:
        data_directory = data_dir

    script_dir = parent_dir(script_path)
    config = load_config(path.join(script_dir, "dataset.yml"))
    starts = DataSet("skillshare_2022_starts.csv", config["starts"])
    views_by_trial_day = DataSet(
        "watch_time_by_trial_day.csv", config["watchtime_by_trial_day"])
    classes = DataSet("skillshare_2022_classes.csv", config["classes"])

    # CREATE TARGET
    starts_df = starts.dataframe(one_hot_categories=True)
    # add a successful conversion column.
    starts_df['success'] = 0
    # set to 1 if they paid
    starts_df['success'][starts_df['first_payment_time'].notnull()] = 1
    # return to 0 if they got a refund.
    starts_df['success'][starts_df['is_refunded'] == 1] = 0
    # drop leaky columns
    starts_df = starts_df.drop(['first_payment_time', 'is_refunded'], axis=1)

    final_df = pandas.merge(
        starts_df,
        views_by_trial_day.dataframe(),
        on="user_uid")

    cleaned_dir = path.join(data_directory, "cleaned")
    if not path.exists(cleaned_dir):
        mkdir(cleaned_dir)
    outfile = path.join(cleaned_dir, "cleaned.parquet")
    final_df.to_parquet(outfile)
    logging.info(f"Cleaned dataset saved to {outfile}")


main()
