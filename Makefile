randomforest: data/features/features.parquet
	@. env/bin/activate; python -m src.models.model_tuning

data/features/features.parquet: featureset
	@. env/bin/activate; python -m src.features.make_featureset

featureset: cleaned_data 

cleaned_data: data/cleaned/cleaned.parquet data/cleaned/cleaned.parquet

data/cleaned/cleaned.parquet: | data/watch_time_by_trial_day.csv
	@. env/bin/activate; python -m src.clean.make_dataset

data/watch_time_by_trial_day.csv: | data
	@echo "Creating artifacts"
	@. env/bin/activate; python -m src.clean.by_trial_day

update_data:
	@echo "Downloading data"
	@. env/bin/activate; python -m src.download

data: | env/touchfile
	@echo "Downloading data"
	@. env/bin/activate; python -m src.download

env/touchfile: 
	@echo "Setting up virtualenv"
	@test -d env || virtualenv env
	@. env/bin/activate; pip install -r requirements.txt
	@touch env/touchfile

update_requirements:
	@echo "Install new pip packages"
	@. env/bin/activate; pip install -r requirements.txt

clean: clean_artifacts
	rm -rf env

clean_artifacts:
	rm -rf data/cleaned
	rm -rf data/features
	rm -rf saved_models

