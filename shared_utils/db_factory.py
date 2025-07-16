import os
from dotenv import load_dotenv

from src.db.influxdb_service import InfluxDBService
from config import config as default_config

load_dotenv()

def create_influxdb_service():
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
    db = InfluxDBService(INFLUXDB_PARAMS)
    return db

if __name__=="__main__":
    create_influxdb_service()