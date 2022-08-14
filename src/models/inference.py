import argparse
from pickle import load as pickleload
from pandas import read_parquet
from pandas import concat as pd_concat
from datetime import datetime
from src import *
from os import path, mkdir

def load_model(picklefile):
    '''
    Takes file path
    Returns pickled model
    '''
    picklefilepath = path.join("saved_models", picklefile)
    logging.info(f"Loading model from {picklefilepath}")
    with open(picklefilepath, "rb") as picklefile:
        model = pickleload(picklefile)
    return model

def load_and_split(parquet_file):
    '''
    Load preprocessed dataset
    Ensure has all correct columns for model
    Divide into month and week groups
    '''
    parquet_file_path = path.join(data_dir, "features", parquet_file)
    df = read_parquet(parquet_file_path)
    columns_file_path = path.join(root_dir, "src", "models", "columns.txt")
    with open(columns_file_path, "r") as col_file:
        needed_columns = col_file.readlines()

    # Making sure all OHE columns present
    for column in needed_columns:
        if column.strip() not in df.columns:
            logging.info(f"adding {column} to new dataset")
            df[column.strip()] = 0

    month_data = df[df.trial_length_days == 31]
    week_data = df[df.trial_length_days == 7]
    return month_data.copy(), week_data.copy(), df

def main():
    parser = argparse.ArgumentParser(
            allow_abbrev=True,
            description="Create predictions from new data")
    parser.add_argument(
            '--model', 
            help='which model to use, defaults to RFC')
    parser.add_argument(
            '--parquet', 
            required=True,
            help='location of parquet file to run predictions on')

    args = parser.parse_args()

    if args.model and "XGB" in args.model:
        logging.info("Using XGBClassifier")
        modeltype = "XGBClassifier"
    else:
        logging.info("Using default RandomForestClassifier")
        modeltype = "RandomForestClassifier"

    month_model = load_model(f"model_{modeltype}_month.pkl")
    week_model = load_model(f"model_{modeltype}_week.pkl")

    month_data, week_data, df = load_and_split(args.parquet)

    month_predictions = month_model.predict(
            month_data.drop(columns=["success", "user_uid"]))
    week_predictions = week_model.predict(
            week_data.drop(columns=["success", "user_uid"]))

    month_pred_probabilities = month_model.predict_proba(
            month_data.drop(columns=["success", "user_uid"]))
    week_pred_probabilities = week_model.predict_proba(
            week_data.drop(columns=["success", "user_uid"]))

    print("BEFORE")
    print(len(month_data))
    print(len(week_data))
    month_data["Prediction"] = month_predictions
    month_data["ChurnProb"] = month_pred_probabilities[:, 0]

    week_data["Prediction"] = week_predictions
    week_data["ChurnProb"] = week_pred_probabilities[: , 0]
    print("AFTER")
    print(len(month_data))
    print(len(week_data))


    final = pd_concat([week_data, month_data])
    print("final")
    print(len(final))
    print("df")
    print(len(df))

    print(final)
    # Save output
    preds_dir = path.join(
            data_dir, 
            "predictions")
    predictions_filepath = path.join(
            preds_dir,
            datetime.today().strftime("%m-%d-%y_%H%M_predictions.csv"))
    if not path.isdir(preds_dir):
        mkdir(preds_dir)
    final.to_csv(predictions_filepath)


main()
