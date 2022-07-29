import pandas
import argparse
from os import path, mkdir
from src import *
from tqdm import tqdm

cleaned_dataset = "cleaned.parquet"

def load_cleaned_dataset(file: str) -> pandas.DataFrame:
    filepath = path.join(data_dir, "cleaned", file)
    return pandas.read_parquet(filepath)

def final_conversions(df: pandas.DataFrame) -> pandas.DataFrame:
    df.drop(
        columns=[
            "create_time", # not using datetime obj in model training
            "user_uid", # not using unique identifiers for training
            "is_active", # TODO not sure what to do with this, so dropping for now
            "is_scholarship", # already filtered on this, all zeros
            "is_direct_to_paid", # already filtered on this, all zeros
            "plan_length", # alerady filtered on this, all 12s
            "was_upgraded", # already filtered on this, all zeros
            "had_trial", # already filtered on this, all zeros
            "is_team"], # already filtered on this, all zeros
        inplace=True)

    logging.info("Converting boolean datatypes to 1s and 0s")
    for column in tqdm(df.columns):
        if df[column].dtype == "bool":
            df[column] = df[column].astype("int8")
        elif "float" in str(df[column].dtype):
            df[column] = df[column].fillna(0.0)
    return df

def main():
    # take CLI arguments
    parser = argparse.ArgumentParser(
        allow_abbrev=True,
        description='Create featureset for modeling')
    parser.add_argument('--output_directory', 
        help="where to put file")

    args = parser.parse_args()

    if args.output_directory:
        data_directory = args.target_dir
    else:
        data_directory = data_dir

    df = load_cleaned_dataset(cleaned_dataset)

    # drop unwanted cols
    # convert bools to ints
    df = final_conversions(df)

    # Save dataset to parquet file within data dir
    filename = "features.parquet"
    features_dir = path.join(data_directory, "features")
    if not path.exists(features_dir):
        mkdir(features_dir)
    outfilepath = path.join(features_dir, filename)
    df.to_parquet(outfilepath)
    logging.info(f"Features dataset saved to {outfilepath}")

main()
