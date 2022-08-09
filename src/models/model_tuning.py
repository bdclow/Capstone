import pandas
from numpy import unique as np_unique
from tqdm import tqdm
from os import path, mkdir
from src import *
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import class_weight
from sklearn.metrics import precision_recall_fscore_support
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
            'max_depth':range(5,8), 
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
    features = load_featureset('features.parquet')
    
    # Separate into two different models
    # One for week-long trials
    # another for month-long trials
    week_trials, month_trials = separate_trials(features)
    model_types = ["week", "month"]
    split_features = [week_trials, month_trials]

    # Create directory for pickled models
    save_model_dir = "saved_models"
    if not path.exists(save_model_dir):
        mkdir(save_model_dir)

    for split_of_featureset, model_type in tqdm(
            zip(split_features, model_types),
            total=len(split_features),
            desc="TRAINING RANDOM FOREST CLASSIERS"):

        model = RandomForestClassifier()
        X_train, y_train, X_test, y_test = preprocess_data(split_of_featureset)

        n_estimators, max_depth, min_samples_split, min_samples_leaf = tune_model(X_train, y_train)

        logging.info("Grid Search Results")
        logging.info("----------------------")
        logging.info(f"For {model_type}, using:")
        logging.info(f"number of decision trees: {n_estimators}")
        logging.info(f"max tree depth: {max_depth}")
        logging.info(f"minimum samples needed to split node: {min_samples_split}")
        logging.info(f"minimum samples needed at leaf node: {min_samples_leaf}")

        # Calculate class weights for imbalanced dataset
        classes=np_unique(y_train)
        class_weights = class_weight.compute_class_weight(
                'balanced',
                classes=classes,
                y=y_train)
        class_weights = dict(zip(classes, class_weights))
        
        model = RandomForestClassifier(
                n_estimators=n_estimators,
                min_samples_split=min_samples_split,
                max_depth=max_depth,
                min_samples_leaf=min_samples_leaf,
                class_weight=class_weights,
                random_state=RANDOM_SEED)

        logging.info(f"Fitting final model")
        model.fit(X_train, y_train)

        accuracy = model.score(
            X_test.values, 
            y_test.values)
        y_pred = model.predict(X_test.values)
        precision, recall, f1_score, _support = precision_recall_fscore_support(y_test, y_pred)

        logging.info("----------------------")
        logging.info(f"Model accuracy: {accuracy}")
        logging.info(f"Model F1-score: {f1_score}")
        logging.info(f"Model recall: {recall}")
        logging.info(f"Model precision: {precision}")
        
        # Save model
        modelpath = path.join(save_model_dir, f"model_{model_type}")
        with open(modelpath, 'wb') as picklefile:
            pickle.dump(model, picklefile)

main()
