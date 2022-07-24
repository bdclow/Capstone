
data/cleaned/cleaned.parquet: | data/watch_time_by_trial_day.csv
	@. env/bin/activate; python -m src.clean.make_dataset

data/watch_time_by_trial_day.csv: | data
	@echo "Creating artifacts"
	@. env/bin/activate; python -m src.clean.by_trial_day

data: | env/touchfile
	@echo "Downloading data"
	@. env/bin/activate; python -m src.download

env/touchfile: 
	@echo "Setting up virtualenv"
	@test -d env || virtualenv env
	@. env/bin/activate; pip install -r requirements.txt
	@touch env/touchfile

clean:
	rm -rf env
	rm -rf data/cleaned
