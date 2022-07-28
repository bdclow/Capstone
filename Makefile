
cleaned_data: data/cleaned/cleaned.parquet data/cleaned/cleaned_w_video_views_breakdowns.parquet

data/cleaned/cleaned.parquet: | data/watch_time_by_trial_day.csv
	@. env/bin/activate; python -m src.clean.make_dataset

data/cleaned/cleaned_w_video_views_breakdowns.parquet:
	@. env/bin/activate; python -m src.clean.make_dataset --categories

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

clean_cleaned:
	rm -rf data/cleaned

clean:
	rm -rf env
	rm -rf data/cleaned
