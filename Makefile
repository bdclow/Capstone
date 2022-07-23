
by_trial_day := data/watch_time_by_trial_day.csv
cleaned := data/cleaned/clean.parquet

cleaned: $(by_trial_day)
	@. env/bin/activate; python src/clean/make_dataset.py

$(by_trial_day): | data
	@echo "Creating artifacts"
	@. env/bin/activate; python src/clean/by_trial_day.py

data: | env/touchfile
	@echo "Downloading data"
	@. env/bin/activate; python download.py

env/touchfile: 
	@echo "Setting up virtualenv"
	@test -d env || virtualenv env
	@. env/bin/activate; pip install -r requirements.txt
	@touch env/touchfile

