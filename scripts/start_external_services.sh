#!/bin/bash

# Resolve script location (even if called via symlink)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker/compose.yaml"

echo "Starting InfluxDB, Kafka and Grafana via Docker Compose..."
exec docker compose -f "$COMPOSE_FILE" up 

if [ $? -eq 0 ]; then
  echo "✅ External services started successfully."
else
  echo "❌ Failed to start external services."
  exit 1
fi

