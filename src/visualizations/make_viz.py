from altair import Chart
from pandas import read_parquet
from os import path
from src import data_dir, parent_dir, script_path

cleaned = "cleaned.parquet"

def open_cleaned_data():
    cleaned_full_path = path.join(data_dir, "cleaned", cleaned)
    return read_parquet(cleaned_full_path)

print(open_cleaned_data())

