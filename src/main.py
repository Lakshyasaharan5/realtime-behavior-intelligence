from datetime import datetime
import time
import queue
import threading
import sys

# Import the thread functions from your modules
from src.watcher.watcher import watcher_thread_func
from src.collector.collector import collector_thread_func

QUEUE_MAX_SIZE = 20

def wait_until_next_minute_mark():
    now = datetime.now()
    seconds = now.second + now.microsecond / 1_000_000
    wait_time = 60 - seconds
    time.sleep(wait_time)


def main():
    print(f"[{datetime.now()}] Starting network monitoring application (Watcher-Collector).")
    wait_until_next_minute_mark()

    # --- Create the shared in-memory queue ---
    # This single queue instance will be passed to both threads
    data_queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)

    # --- Start the Watcher thread ---
    # The watcher produces data and puts it into 'data_queue'
    watcher_thread = threading.Thread(
        target=watcher_thread_func, 
        args=(data_queue,),
        name="WatcherThread" # Give threads names for easier debugging
    )
    watcher_thread.daemon = True # Allows the main program to exit even if this thread is running
    

    # --- Start the Collector thread ---
    # The collector consumes data from 'data_queue'
    collector_thread = threading.Thread(
        target=collector_thread_func, 
        args=(data_queue,),
        name="CollectorThread"
    )
    collector_thread.daemon = True # Allows the main program to exit even if this thread is running
    collector_thread.start()
    watcher_thread.start()

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

