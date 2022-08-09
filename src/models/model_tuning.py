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
from xgboost import XGBClassifier
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

def tune_model(X_train, y_train, Estimator):
    '''
    takes training data
    fits RFC
    returns best model parameters
    '''

    param_test1 = {
            'n_estimators': range(50, 251, 50),
            'max_depth':range(5,8)} 
    if Estimator is XGBClassifier:
        param_test1["reg_alpha"] = [0.1, 0.3, 0.6]
        param_test1["learning_rate"] = [0.05, 0.10, 0.15, 0.3]
    else:
        param_test1["min_samples_split"] = range(2,11,2)

    gsearch1 = GridSearchCV(
            estimator = Estimator(
                random_state=RANDOM_SEED),
            param_grid = param_test1, 
            scoring='precision', 
            verbose=4,
            n_jobs=-1,
            cv=5)

    gsearch1.fit(X_train,y_train)
    best_params = gsearch1.best_params_
    n_estimators = best_params['n_estimators']
    for param in param_test1.keys():
        logging.info(f"Best {param} : {best_params[param]}")
    
    #param_test2 = {
    #        'max_depth':range(5,8), 
    #        'min_samples_split':range(2,11,2)}

    #gsearch2 = GridSearchCV(
    #        estimator = Estimator(
    #            n_estimators=n_estimators, 
    #            **additional_args,
    #            random_state=RANDOM_SEED), 
    #        param_grid = param_test2, 
    #        scoring='precision', 
    #        verbose=4,
    #        n_jobs=-1,
    #        cv=5)

    #gsearch2.fit(X_train, y_train)
    #best_params2 = gsearch2.best_params_
    #max_depth = best_params2['max_depth']
    #min_samples_split = best_params2['min_samples_split']
    #logging.info(f"Best max_depth, min_samples: {max_depth} {min_samples_split}")
    #
    #param_test3 = {'min_samples_leaf':range(1,11,2)}

    #gsearch3 = GridSearchCV(
    #        estimator = Estimator(
    #            n_estimators=n_estimators,
    #            max_depth=max_depth, 
    #            min_samples_split=min_samples_split, 
    #            random_state=RANDOM_SEED,
    #            **additional_args), 
    #        param_grid = param_test3, 
    #        scoring='precision', 
    #        verbose=4,
    #        n_jobs=-1,
    #        cv=5)

    #gsearch3.fit(X_train,y_train)
    #best_params3 = gsearch3.best_params_
    #min_samples_leaf = best_params3['min_samples_leaf']
    
    return best_params


def main():
    features = load_featureset('features.parquet')
    
    # Separate into two different models
    # One for week-long trials
    # another for month-long trials
    week_trials, month_trials = separate_trials(features)
    trial_lengths = ["week", "month"]
    split_features = [week_trials, month_trials]

    # Create directory for pickled models
    save_model_dir = "saved_models"
    if not path.exists(save_model_dir):
        mkdir(save_model_dir)

    estimators = [RandomForestClassifier, XGBClassifier]

    for Estimator in estimators:
        for split_of_featureset, trial_length in tqdm(
                zip(split_features, trial_lengths),
                total=len(split_features),
                desc=f"TRAINING {Estimator.__name__}"):

            model = Estimator()
            X_train, y_train, X_test, y_test = preprocess_data(split_of_featureset)

            #n_estimators, max_depth, min_samples_split, min_samples_leaf 
            best_params = tune_model(X_train, y_train, Estimator)

            # Calculate class weights for imbalanced dataset
            classes=np_unique(y_train)
            class_weights = class_weight.compute_class_weight(
                    'balanced',
                    classes=classes,
                    y=y_train)
            class_weights = dict(zip(classes, class_weights))
            
            model = Estimator(
                    **best_params,
                    class_weight=class_weights,
                    random_state=RANDOM_SEED)

            logging.info(f"Fitting final model")
            model.fit(X_train, y_train)

            accuracy = model.score(
                X_test.values, 
                y_test.values)
            y_pred = model.predict(X_test.values)
            precision, recall, f1_score, _support = precision_recall_fscore_support(y_test, y_pred)

            logging_text = []
            logging_text.append(f"model_{Estimator.__name__}_{trial_length}\n")
            logging_text.append("----------------------\n")
            logging_text.append(f"Model accuracy: {accuracy}\n")
            logging_text.append(f"Model F1-score: {f1_score}\n")
            logging_text.append(f"Model recall: {recall}\n")
            logging_text.append(f"Model precision: {precision}\n\n")

            for text in logging_text:
                logging.info(text)
            
            # Save model and metainfo
            modelpath = path.join(
                    save_model_dir, 
                    f"model_{Estimator.__name__}_{trial_length}.pkl")

            modelinfopath = path.join(save_model_dir, "meta_info.txt")

            with open(modelinfopath, 'a') as metafile:
                metafile.writelines(logging_text)
            with open(modelpath, 'wb') as picklefile:
                pickle.dump(model, picklefile)

main()
