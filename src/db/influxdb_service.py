from influxdb_client_3 import InfluxDBClient3, Point


class InfluxDBService:
    def __init__(self, config: dict):
        self.client = InfluxDBClient3(host=config["url"],
                         database=config["database"],
                         token=config["token"])
    
    def write_batch(self, batch_data: list):
        """
        Converts a list of raw (timestamp, app_net_usage) tuples into InfluxDB Points
        and writes them to the configured bucket in a batch.
        """
        if not batch_data:
            return

        points = []
        for timestamp, app_net_usage in batch_data:
            for process_name, metrics in app_net_usage.items():
                point = Point("network_traffic") \
                    .tag("process_name", process_name) \
                    .field("in", metrics["in"]) \
                    .field("out", metrics["out"]) \
                    .time(timestamp)
                points.append(point)

        if points:
            self.client.write(points)

