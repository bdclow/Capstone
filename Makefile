
.SECONDARY: data/features/features.parquet data/features/cleaned.parquet  saved_models  data/skillshare_2022_starts.csv

.PHONY: predictions

predictions:
	$(data/predictions)

dashboard: data/predictions
	@echo "Starting dashboard"
	@. env/bin/activate; python -m src.dashboard.run

data/predictions: saved_models 
	@. env/bin/activate; python -m src.clean.make_dataset --csv_prefix "new_trialers"
	@. env/bin/activate; python -m src.features.make_featureset --cleaned_data "new_trialers_cleaned.parquet"
	@. env/bin/activate; python -m src.models.inference --parquet "new_trialers_features.parquet"

# Targets for sample data
# -----------------------
sample: saved_models data/features/sample_features.parquet
	@echo "Making predictions"
	@. env/bin/activate; python -m src.models.inference --parquet "sample_features.parquet"

data/features/sample_features.parquet: data/cleaned/sample_cleaned.parquet
	@echo "Making featureset"
	@. env/bin/activate; python -m src.features.make_featureset --cleaned_data "sample_cleaned.parquet"

data/cleaned/sample_cleaned.parquet: sample_data/cleaned/sample_cleaned.parquet env/touchfile
	@echo "Copying sample csv to data dir"
	mkdir -p data/cleaned
	cp -v sample_data/cleaned/sample_cleaned.parquet data/cleaned/sample_cleaned.parquet 

sample_data/cleaned/sample_cleaned.parquet:
	@echo "No sample dataset available, email team"

# Intermediate files (cleaned and uncleaned datasets, etc.)
#------------------------

saved_models:
	@echo "Tuning models"
	$(data/features/features.parquet)
	@. env/bin/activate; python -m src.models.model_tuning

data/features/features.parquet: data data/skillshare_2022_starts.csv
	@echo "Making featureset"
	echo $(.INTERMEDIATES)
	@. env/bin/activate; python -m src.clean.make_dataset
	@. env/bin/activate; python -m src.features.make_featureset

data/skillshare_2022_starts.csv:
	$(update_data)

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

# CLEAN scripts
# ---------------------------
clean: 
	$(clean_artifacts)
	rm -rf env

clean_artifacts:
	rm -rf data/cleaned
	rm -rf data/features

clean_predictions:
	rm -rf data/predictions
