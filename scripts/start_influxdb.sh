#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Robustly determine the script's own directory ---
# BASH_SOURCE[0] is the path to the script itself.
# dirname gets the directory part.
# cd "$(dirname ...)" changes to that directory.
# pwd gets the absolute path of the current directory.
# &> /dev/null redirects stdout/stderr to null to suppress 'No such file or directory' errors.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# --- Derive the Project Root ---
# Assuming 'start_influxdb.sh' is in 'scripts/' and 'scripts/' is directly under the project root.
# If your script is directly in the project root, just use SCRIPT_DIR for PROJECT_ROOT.
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")" # Go up one level from 'scripts/' to get to project root

#TODO: Fix this. Currently not able to load env variables
# --- Load .env file for environment variables ---
# Set -a: Automatically exports all subsequent variables to the environment.
set -a
# Source the .env file if it exists in the project root.
if [ -f "$PROJECT_ROOT/.env" ]; then
  echo "Loading environment variables from $PROJECT_ROOT/.env"
  . "$PROJECT_ROOT/.env" # The '.' command is a POSIX standard way to source a file
else
  echo "Warning: .env file not found at $PROJECT_ROOT/.env. Ensure it exists if needed."
fi
set +a # Turn off automatic export after .env is loaded

# --- Configuration ---
NODE_ID="host01"
CLUSTER_ID="cluster01"

# Define DATA_DIR relative to the determined PROJECT_ROOT
DATA_DIR="$PROJECT_ROOT/data/influxdb3_data"

echo "Starting InfluxDB 3 server..."
echo "Data will be stored in: $DATA_DIR"
echo "Running from Project Root: $PROJECT_ROOT" # For debugging confirmation

# Create the data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Run the InfluxDB 3 server command
# 'exec' replaces the current shell process with influxdb3, so CTRL+C works directly
exec influxdb3 serve \
  --node-id "$NODE_ID" \
  --cluster-id "$CLUSTER_ID" \
  --object-store file \
  --data-dir "$DATA_DIR"

