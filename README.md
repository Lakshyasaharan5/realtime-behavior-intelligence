# REALTIME NETWORK BEHAVIOR INTELLIGENCE

Watches your network usage per app and creates time series dataset. Uses ML to detect anomaly in current day based on previous N days of baseline data.

## How to run on local?
- Currently it only works on macbook because it uses `nettop` 
- You must have Docker installed on your system

Clone my github repo and just start the script
```shell
$ scripts/start.sh
```

## Architecture
Watcher----Kafka pipeline-----Collector
				|
				|
				|
	    Dashboard-------Database------Intelligence

### Watcher
Wraps `nettop` macos ultility to track network usage per application. It triggers nettop in 1 minute interval and loads parsed data into Kafka pipeline.

### Collector
It takes data from Kafka pipeline and stores in InfluxDB in batches.

### Intelligence
This module includes complete Machine Learning pipeline for detecting anomaly. Loads last N days of data from database, preprocess and feeds into Autoencoder model for anomaly detection. Whole pipeline runs everyday as cron job for daily detection. It detects previous day's behavior based on N days prior to previous day because current day is still on going.   

#### Why Autoencoder model?
We want a model that can learn complete day pattern with bettern generalization and some tolerance to noise. One class SVM can’t handle noise at all. Z-score and Isolation forest are not good because they will start screaming if I use 10 minute of Facebook during work hours but Autoencoder will be able to tolerate this noise nicely and only trigger incase of significant change.

### Dashboard
I integrated Grafana for showing live metrics and alerts because its industry standard and fits very well with time series data.


