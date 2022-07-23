import pandas
from datetime import datetime
from os import path, pardir
import logging
from tqdm import tqdm

def parent_dir(directory: str):
    return path.abspath(path.join(directory, pardir))

prefix = "skillshare_2022_"
suffix = ".csv"
script_path = path.abspath(__file__)
root_dir = parent_dir(parent_dir(parent_dir(script_path)))
data_dir = path.join(root_dir, "data")
date_format = "%Y-%m-%d %H:%M:%S"
parse_dt = lambda dt_str: datetime.strptime(dt_str, date_format)

class DataSet:
    '''
    Class with info about each dataset
    dataframe method returns Pandas DF
    filter method filters column by value
    '''
    def __init__(self, filepath: str, columns: dict):
        self.name = filepath.replace(prefix, "").replace(suffix, "")
        self.columns = columns
        self.filepath = path.join(data_dir, filepath)
        self.df = None
        
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
            logging.info(f"Loading {self} to Pandas DataFrame")
            self.df = pandas.read_csv(
                    self.filepath, 
                    usecols=self.columns.keys(), 
                    index_col=0)
            # Column datatype
            for column in self.df.columns:
                if self.columns[column] == "datetime64[ns]":
                    self.df[column] = pandas.to_datetime(self.df[column], format=date_format)
                if str(self.df[column].dtype) != self.columns[column]['dtype']:
                    # if column datatype not correct, set to correct type
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
            try:
                filter_by = item["filter"]
                self.filter(column, filter_by)
            except KeyError:
                pass
        if one_hot_categories:
            df = self.df.copy()
            logging.info("Creating one-hot encodings")
            for column, dtype in tqdm(self.columns.items()):
                if dtype == "object":
                    df = pandas.merge(
                        df.drop(column, axis=1), 
                        pandas.get_dummies(df[column]),
                        left_index=True,
                        right_index=True)
            return df
        else:
            return self.df

    def filter(self, column, value):
        if self.df is None:
            _ = self.dataframe()
        if type(value) is list:
            self.df = self.df[self.df[column].isin(value)]
        else:
            self.df = self.df[self.df[column] == value]
