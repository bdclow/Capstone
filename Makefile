
data: 
	source env/bin/activate; python download.py

data/watch_time_by_trial_day.csv: data
	source env/bin/activate; python clean/by_trial_day.py

install: 
	source env/bin/activate; pip install -r requirements.txt

