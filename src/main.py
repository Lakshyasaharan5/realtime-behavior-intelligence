from datetime import datetime
import time
import queue
import threading

# Import .env and config file params
import sys
import os
from dotenv import load_dotenv

current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.abspath(os.path.join(current_script_dir, os.pardir))
sys.path.insert(0, project_root_dir)

# Import default configurations from your config file
from config import config as default_config

load_dotenv()

# InfluxDB Configuration
# os.getenv() retrieves an environment variable.
# The second argument is the fallback value if the environment variable is not set.
# We prioritize env vars, then fall back to config.py defaults.
INFLUXDB_URL = os.getenv("INFLUXDB_URL", default_config.INFLUXDB_URL)
INFLUXDB3_AUTH_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN", default_config.INFLUXDB3_AUTH_TOKEN)
INFLUXDB_DATABASE = os.getenv("INFLUXDB_DATABASE", default_config.INFLUXDB_DATABASE)

# --- Create configuration dictionaries/objects from resolved values ---
INFLUXDB_PARAMS = { # Using all caps to indicate it's treated as a constant
    "url": INFLUXDB_URL,
    "token": INFLUXDB3_AUTH_TOKEN,
    "database": INFLUXDB_DATABASE
}

# Import custom modules
from src.watcher.watcher import watcher_thread_func
from src.collector.collector import collector_thread_func
from src.db.influxdb_service import InfluxDBService

QUEUE_MAX_SIZE = 20

def wait_until_next_minute_mark():
    now = datetime.now()
    seconds = now.second + now.microsecond / 1_000_000
    wait_time = 60 - seconds
    time.sleep(wait_time)


def main():
    print(f"[{datetime.now()}] Starting network monitoring application (Watcher-Collector).")
    wait_until_next_minute_mark()

    # --- Create the shared in-memory queue and influxdb service
    data_queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)
    influxdb_service = InfluxDBService(INFLUXDB_PARAMS)

    # --- Start the Watcher thread ---
    watcher_thread = threading.Thread(
        target=watcher_thread_func, 
        args=(data_queue,),
        name="WatcherThread" # Give threads names for easier debugging
    )
    watcher_thread.daemon = True # Allows the main program to exit even if this thread is running
    watcher_thread.start()

    # --- Start the Collector thread ---
    collector_thread = threading.Thread(
        target=collector_thread_func, 
        args=(data_queue,influxdb_service,),
        name="CollectorThread"
    )
    collector_thread.daemon = True # Allows the main program to exit even if this thread is running
    collector_thread.start()    

    # --- Keep the main thread alive ---
    # Use KeyboardInterrupt (Ctrl+C) to exit gracefully.
    try:
        while True:
            # The main thread can do other things or just sleep,
            # waiting for the watcher and collector threads to perform their tasks.
            time.sleep(1) 
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Main thread received KeyboardInterrupt. Shutting down...")
    finally:
        print(f"[{datetime.now()}] Application finished.")

if __name__ == "__main__":
    main()

