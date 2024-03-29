'''
Class to wrap our specific CSV datasets
'''
import pandas
import logging
from os import path
from tqdm import tqdm
from src import data_dir

PREFIX = "skillshare_2022_"
SUFFIX = ".csv"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class DataSet:
    '''
    Class with info about each dataset
    columns parameter takes dict with datatype info
        and optional filtering parameter
        given by config file
    dataframe method returns Pandas DF
    filter method filters column by value
    '''
    def __init__(self, filepath: str, columns: dict, log: bool = True):
        self.name = filepath.replace(PREFIX, "").replace(SUFFIX, "")
        self.columns = columns
        self.filepath = path.join(data_dir, filepath)
        self.df = None
        self.log_output = log

    def __repr__(self):
        return f"'{self.name}' dataset"

    def dataframe(self, one_hot_categories=False):
        '''
        Load CSV to Pandas DataFrame if not loaded
        Use column dtype info to ensure correct datatypes
        (e.g. for starts df mem usage 62 Mb -> 48 Mb)
        Returns Pandas DataFrame
        '''
        if self.df is None:
            # If DF not loaded yet, load
            if self.log_output:
                logging.info(f"Loading {self} to Pandas DataFrame")
            self.df = pandas.read_csv(
                    self.filepath,
                    usecols=self.columns.keys(),
                    index_col=0)
            # Column datatype
            for column in self.df.columns:
                if self.columns[column] == "datetime64[ns]":
                    self.df[column] = pandas.to_datetime(self.df[column], format=DATE_FORMAT)
                if str(self.df[column].dtype) != self.columns[column]['dtype']:
                    # if column datatype not correct, set to correct type
                    if self.log_output:
                        logging.info(
                                f"""converting datatype of {column} """
                                f"""from {self.df[column].dtype} """
                                f"""to {self.columns[column]['dtype']} for {self}""")
                    try:
                        if "int" in self.columns[column]['dtype']:
                            self.df = self.df.dropna(subset=column)
                        self.df[column] = self.df[column].astype(
                                self.columns[column]['dtype'])
                    except KeyError:
                        logging.error(f"dtype not specified for {column} column")
        for column, item in self.columns.items():
            # apply filtering method based on configuration values
            try:
                filter_by = item["filter"]
                self.filter(column, filter_by)
            except KeyError:
                pass
        if one_hot_categories:
            # if one hot encoding needed, create necessary cols
            df = self.df.copy()
            for column, value in tqdm(self.columns.items(), 
                    desc="Creating one-hot encodings"):
                dtype = value['dtype']
                if dtype == "object":
                    df = pandas.merge(
                        df.drop(column, axis=1),
                        pandas.get_dummies(df[column]),
                        left_index=True,
                        right_index=True)
            return df
        return self.df

    def filter(self, column, value):
        '''
        Filters dataframe based on parameter
        This is pretty simple, if most complicated needed
        Would just Pandas DF methods as usual
        '''
        if self.df is None:
            _ = self.dataframe()
        if isinstance(value, list):
            self.df = self.df[self.df[column].isin(value)]
        else:
            self.df = self.df[self.df[column] == value]
