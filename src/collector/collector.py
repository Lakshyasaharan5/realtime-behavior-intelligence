import datetime
import time
import queue
import json
import sys


def collector_thread_func(q: queue.Queue):
    while True:
        try:
            timestamp, app_net_usage = q.get(timeout=120)
            print(f"\n{timestamp.strftime('%H:%M:%S')}")
            print(app_net_usage)
            
            q.task_done()
        except Exception as e:
            q.task_done() 

