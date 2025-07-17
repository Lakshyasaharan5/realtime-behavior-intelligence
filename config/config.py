NETTOP_DELAY = 60

# InfluxDB Configuration Defaults
INFLUXDB_URL = "http://localhost:8181"
INFLUXDB_ORG = "my_org"
INFLUXDB_BUCKET = ""
INFLUXDB_DATABASE = "realtime_network_metrics"

# Application-specific parameters
COLLECTION_INTERVAL_SECONDS = 60
QUEUE_MAX_SIZE = 20

# Add a placeholder for the token, but it should ideally be overridden by an env var
# This ensures a default exists if the env var isn't loaded (e.g., during tests without a .env)
# But a warning might be good if it's used in production.
INFLUXDB3_AUTH_TOKEN = "default_placeholder_token_do_not_use_in_prod"

# You can also add more complex configuration structures if needed
APP_NAME = "realtime_behavior_intelligence"
LOG_LEVEL = "INFO"

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC_NETWORK_DATA = "network-metrics"
KAFKA_CONSUMER_GROUP = "network-collector"