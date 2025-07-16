from datetime import datetime
import time
import queue
import threading

# Import custom modules
from src.watcher.watcher import watcher_thread_func
from src.collector.collector import collector_thread_func
from shared_utils.db_factory import create_influxdb_service

QUEUE_MAX_SIZE = 20

def wait_until_next_minute_mark():
    now = datetime.now()
    seconds = now.second + now.microsecond / 1_000_000
    wait_time = 60 - seconds
    time.sleep(wait_time)


def main():
    print(f"[{datetime.now()}] Starting network monitoring application (Watcher-Collector).")
    wait_until_next_minute_mark()

    data_queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)
    influxdb_service = create_influxdb_service()

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

