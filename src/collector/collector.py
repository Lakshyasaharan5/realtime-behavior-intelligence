import queue
from src.db.influxdb_service import InfluxDBService


def collector_thread_func(q: queue.Queue, influxdb_service: InfluxDBService):

    batch_buffer = []
    buffer_limit = 2

    while True:
        timestamp, app_net_usage = q.get(timeout=120)
        print(f"\n{timestamp.strftime('%H:%M:%S')}")
        print(app_net_usage)
        batch_buffer.append((timestamp, app_net_usage))

        if len(batch_buffer) == buffer_limit:
            print("Storing data in dictionary----")
            influxdb_service.write_batch(batch_buffer)
            batch_buffer = []
        


