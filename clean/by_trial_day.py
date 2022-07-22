#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import os

starts_file = 'skillshare_2022_starts.csv'
# numbered from 0 to 62
vviews_files = [f"skillshare_2022_vviews_{i}.csv" for i in range(0, 63)]
# cwd
script_dir = os.path.dirname(__file__)
# data directory
data_dir = os.path.abspath(os.path.join(script_dir, "..", "data"))


def load_csv_to_df(filepath):
    '''
    wrap pandas method for our csvs
    '''
    return pd.read_csv(data_dir + filepath, index_col=0)


def convert_cols(row: pd.Series, prev_col: str, day: int):
    '''
    figure out relative day of trial
    day in integer form, takes negative days / indexes
    '''
    trial_length = 30 if row["trial_length_offer"] == "One Month" else 7
    day_converted = trial_length + (day + 1)
    return row[(prev_col, day_converted)]


def main():
    # Load datafames with video watch days (time spent, etc)
    vviews = pd.DataFrame()
    for file in vviews_files:
        vviews = pd.concat([vviews, load_csv_to_df(file)])

    # new trial starts data
    starts = load_csv_to_df(starts_file)

    # convert str to datetime
    for column in starts.columns:
        if "time" in column:
            starts[column] = pd.to_datetime(starts[column])
    vviews.view_date = pd.to_datetime(vviews.view_date)

    # JOIN starts and views
    account_and_views_info = pd.merge(
        vviews, starts,
        left_on="uid",
        right_on="user_uid",
        how="outer")

    # LIMIT to desired trials
    account_and_views_info = account_and_views_info[
        account_and_views_info.trial_length_offer.isin(["One Month", "One Week"])]
    # Create column for watch data, corresponds to the day after trial start
    account_and_views_info["day_of_trial"] = account_and_views_info.view_date - \
        account_and_views_info.create_time
    account_and_views_info.dropna(subset=["day_of_trial"], inplace=True)
    # Cut back on DF size, only using these days anyway
    account_and_views_info = account_and_views_info[
        (account_and_views_info.day_of_trial.dt.days < 31) &
        (account_and_views_info.day_of_trial.dt.days > 0)]
    # Truncate day of trial from timedelta to just an integer
    account_and_views_info.day_of_trial = account_and_views_info.day_of_trial.dt.days
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
    views_by_trial_day = pd.merge(
        views_by_trial_day.reset_index(),
        starts[["trial_length_offer", "user_uid"]],
        left_on="user_uid",
        right_on="user_uid")
    # Only use the first 3 days and the last 3 days of trial
    first_days = [1, 2, 3]
    last_days = [-3, -2, -1]

    for day in first_days:
        views_by_trial_day[f"day_{day}_total_watchtime"] = views_by_trial_day[(
            'sum', day)]
        views_by_trial_day[f"day_{day}_watched_video_length"] = views_by_trial_day[(
            'video_duration', day)]

    for day in last_days:
        views_by_trial_day[f"day_{day}_total_watchtime"] = views_by_trial_day.apply(
            lambda row: convert_cols(row, "sum", day), axis=1)
        views_by_trial_day[f"day_{day}_watched_video_length"] = views_by_trial_day.apply(
            lambda row: convert_cols(row, "video_duration", day), axis=1)

    cols_to_keep = [col for col in views_by_trial_day.columns
                    if "total_watchtime" in col or "video_length" in col]
    cols_to_keep.insert(0, "user_uid")

    # Fix final issues with datatypes and missing values
    views_by_trial_day.user_uid = views_by_trial_day.user_uid.astype(int)
    for col in cols_to_keep:
        views_by_trial_day[col] = views_by_trial_day[col].fillna(0.0)
    # Save
    views_by_trial_day[cols_to_keep].to_csv(
        "../data/watch_time_by_trial_day.csv")


#main()

