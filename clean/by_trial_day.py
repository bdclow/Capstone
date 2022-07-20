#!/usr/bin/env python
# coding: utf-8
import pandas as pd

starts_file = 'skillshare_2022_starts.csv'

vviews_files = ['skillshare_2022_vviews_0.csv',
                 'skillshare_2022_vviews_10.csv',
                 'skillshare_2022_vviews_11.csv',
                 'skillshare_2022_vviews_12.csv',
                 'skillshare_2022_vviews_13.csv',
                 'skillshare_2022_vviews_14.csv',
                 'skillshare_2022_vviews_15.csv',
                 'skillshare_2022_vviews_16.csv',
                 'skillshare_2022_vviews_17.csv',
                 'skillshare_2022_vviews_18.csv',
                 'skillshare_2022_vviews_19.csv',
                 'skillshare_2022_vviews_1.csv',
                 'skillshare_2022_vviews_20.csv',
                 'skillshare_2022_vviews_21.csv',
                 'skillshare_2022_vviews_22.csv',
                 'skillshare_2022_vviews_23.csv',
                 'skillshare_2022_vviews_24.csv',
                 'skillshare_2022_vviews_25.csv',
                 'skillshare_2022_vviews_26.csv',
                 'skillshare_2022_vviews_27.csv',
                 'skillshare_2022_vviews_28.csv',
                 'skillshare_2022_vviews_29.csv',
                 'skillshare_2022_vviews_2.csv',
                 'skillshare_2022_vviews_30.csv',
                 'skillshare_2022_vviews_31.csv',
                 'skillshare_2022_vviews_32.csv',
                 'skillshare_2022_vviews_33.csv',
                 'skillshare_2022_vviews_34.csv',
                 'skillshare_2022_vviews_35.csv',
                 'skillshare_2022_vviews_36.csv',
                 'skillshare_2022_vviews_37.csv',
                 'skillshare_2022_vviews_38.csv',
                 'skillshare_2022_vviews_39.csv',
                 'skillshare_2022_vviews_3.csv',
                 'skillshare_2022_vviews_40.csv',
                 'skillshare_2022_vviews_41.csv',
                 'skillshare_2022_vviews_42.csv',
                 'skillshare_2022_vviews_43.csv',
                 'skillshare_2022_vviews_44.csv',
                 'skillshare_2022_vviews_45.csv',
                 'skillshare_2022_vviews_46.csv',
                 'skillshare_2022_vviews_47.csv',
                 'skillshare_2022_vviews_48.csv',
                 'skillshare_2022_vviews_49.csv',
                 'skillshare_2022_vviews_4.csv',
                 'skillshare_2022_vviews_50.csv',
                 'skillshare_2022_vviews_51.csv',
                 'skillshare_2022_vviews_52.csv',
                 'skillshare_2022_vviews_53.csv',
                 'skillshare_2022_vviews_54.csv',
                 'skillshare_2022_vviews_55.csv',
                 'skillshare_2022_vviews_56.csv',
                 'skillshare_2022_vviews_57.csv',
                 'skillshare_2022_vviews_58.csv',
                 'skillshare_2022_vviews_59.csv',
                 'skillshare_2022_vviews_5.csv',
                 'skillshare_2022_vviews_60.csv',
                 'skillshare_2022_vviews_61.csv',
                 'skillshare_2022_vviews_62.csv',
                 'skillshare_2022_vviews_6.csv',
                 'skillshare_2022_vviews_7.csv',
                 'skillshare_2022_vviews_8.csv',
                 'skillshare_2022_vviews_9.csv']

def load_csv_to_df(filepath):
    '''
    wrap pandas method for our csvs
    '''
    return pd.read_csv("../data/" + filepath, index_col=0)

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
    account_and_views_info = pd.merge(vviews, starts, left_on="uid", right_on="user_uid", how="outer")
    # LIMIT to desired trials
    account_and_views_info = account_and_views_info[account_and_views_info.trial_length_offer.isin(["One Month", "One Week"])]
    # Create column for watch data, corresponds to the day after trial start
    account_and_views_info["day_of_trial"] = account_and_views_info.view_date - account_and_views_info.create_time
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
        .agg({"sum": "sum", "video_duration":"sum"})\
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
        views_by_trial_day[f"day_{day}_total_watchtime"] = views_by_trial_day[('sum', day)]
        views_by_trial_day[f"day_{day}_watched_video_length"] = views_by_trial_day[('video_duration', day)]
        
    for day in last_days:
        views_by_trial_day[f"day_{day}_total_watchtime"] = views_by_trial_day.apply(lambda row: convert_cols(row, "sum", day), axis=1)
        views_by_trial_day[f"day_{day}_watched_video_length"] = views_by_trial_day.apply(lambda row: convert_cols(row, "video_duration", day), axis=1)
        
    cols_to_keep = [ col for col in views_by_trial_day.columns if "total_watchtime" in col or "video_length" in col ]
    cols_to_keep.insert(0, "user_uid")

    # Fix final issues with datatypes and missing values
    views_by_trial_day.user_uid = views_by_trial_day.user_uid.astype(int)
    for col in cols_to_keep:
        views_by_trial_day[col] = views_by_trial_day[col].fillna(0.0)
    # Save
    views_by_trial_day[cols_to_keep].to_csv("../data/watch_time_by_trial_day.csv")

main()
