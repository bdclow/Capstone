import argparse
from os import path, pardir
import logging
import yaml
from dataset import DataSet, data_dir

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
        data_dir = args.target_dir

    config = load_config("dataset.yml")
    print(config)
    starts = DataSet("skillshare_2022_starts.csv", config["starts"])
    by_trial_day = DataSet("watch_time_by_trial_day.csv", config["watchtime_by_trial_day"])
    print(starts.dataframe().info())
    print(by_trial_day.dataframe().info())

    #with open(os.path.join(data_dir, "cleaned/cleaned.csv")) as cleaned_csv:
    #
    #

main()
