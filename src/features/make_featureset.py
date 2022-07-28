import pandas
from os import path
from src import *
from tqdm import tqdm

cleaned_dataset_filepath = "cleaned.parquet"
nmf_classes_dataset_filepath = "nmf_classes.parquet"

def load_cleaned_dataset() -> pandas.DataFrame:
    filepath = path.join(data_dir, "cleaned", cleaned_dataset_filepath)
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

print(df)
print(df.columns)
