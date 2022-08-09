import pandas
from tqdm import tqdm
from os import path, mkdir
from src import *
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
import pickle

RANDOM_SEED=42

def load_featureset(file: str) -> pandas.DataFrame:
    filepath = path.join(data_dir, "features", file)
    return pandas.read_parquet(filepath)

def preprocess_data(df) -> tuple:
    X = df.drop(["success"], axis = 1)
    y = df['success']
    logging.info(f"DF SIZE::::::: {len(X)}")
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=RANDOM_SEED)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    return X_train, y_train, X_test, y_test

def separate_trials(df) -> tuple:
    week_trials = df[df['trial_length_days'] == 7]
    month_trials = df[df['trial_length_days'] == 31]
    logging.info(f"NUMBER OF WEEK LONG TRIALS = {len(week_trials)}")
    logging.info(f"NUMBER OF MONTH LONG TRIALS = {len(month_trials)}")
    return week_trials, month_trials

def tune_model(X_train, y_train):
    '''
    takes training data
    fits RFC
    returns best model parameters
    '''

    param_test1 = {'n_estimators': range(50, 251, 50)}

    gsearch1 = GridSearchCV(
            estimator = RandomForestClassifier(random_state=RANDOM_SEED), 
            param_grid = param_test1, 
            scoring='roc_auc', 
            verbose=4,
            n_jobs=-1,
            cv=5)

    gsearch1.fit(X_train,y_train)
    best_params = gsearch1.best_params_
    n_estimators = best_params['n_estimators']
    logging.info(f"Best n_estimators: {n_estimators}")
    
    param_test2 = {
            'max_depth':range(1,18,4), 
            'min_samples_split':range(2,11,2)}

    gsearch2 = GridSearchCV(
            estimator = RandomForestClassifier(n_estimators=n_estimators, random_state=RANDOM_SEED), 
            param_grid = param_test2, 
            scoring='roc_auc', 
            verbose=4,
            n_jobs=-1,
            cv=5)

    gsearch2.fit(X_train, y_train)
    best_params2 = gsearch2.best_params_
    max_depth = best_params2['max_depth']
    min_samples_split = best_params2['min_samples_split']
    logging.info(f"Best max_depth, min_samples: {max_depth} {min_samples_split}")
    
    param_test3 = {'min_samples_leaf':range(1,11,2)}

    gsearch3 = GridSearchCV(
            estimator = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth, 
                min_samples_split=min_samples_split, 
                random_state=RANDOM_SEED), 
            param_grid = param_test3, 
            scoring='roc_auc', 
            verbose=4,
            n_jobs=-1,
            cv=5)

    gsearch3.fit(X_train,y_train)
    best_params3 = gsearch3.best_params_
    min_samples_leaf = best_params3['min_samples_leaf']
    logging.info(f"Best min samples leaf: {min_samples_leaf}")
    
    return n_estimators, max_depth, min_samples_split, min_samples_leaf


def main():
    df = load_featureset('features.parquet')
    
    # Separate into two different models
    # One for week-long trials
    # another for month-long trials
    week_trials, month_trials = separate_trials(df)
    model_types = ["week", "month"]
    dfs = [week_trials, month_trials]

    # Create directory for pickled models
    save_model_dir = "saved_models"
    if not path.exists(save_model_dir):
        mkdir(save_model_dir)

    for i in tqdm(range(len(dfs)), desc="TRAINING RANDOM FOREST CLASSIERS"):
        model = RandomForestClassifier()

        X_train, y_train, X_test, y_test = preprocess_data(dfs[i])

        n_estimators, max_depth, min_samples_split, min_samples_leaf = tune_model(X_train, y_train)
        
        model = RandomForestClassifier(
                n_estimators=n_estimators,
                min_samples_split=min_samples_split,
                max_depth=max_depth,
                min_samples_leaf=min_samples_leaf,
                random_state=RANDOM_SEED)
        
        # Save model
        modelpath = path.join(save_model_dir, f"model_{model_types[i]}")
        with open(modelpath, 'wb') as picklefile:
            pickle.dump(model, picklefile)

main()
