from influxdb_client_3 import InfluxDBClient3, Point


class InfluxDBService:
    def __init__(self, config: dict):
        self.client = InfluxDBClient3(host=config["url"],
                         database=config["database"],
                         token=config["token"])
    
