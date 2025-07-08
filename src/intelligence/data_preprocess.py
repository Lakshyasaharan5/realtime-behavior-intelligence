"""
Simple data aggregation for network behavior analysis
"""

from datetime import datetime, timedelta
import numpy as np
from src.db.influxdb_service import InfluxDBService


def get_daily_matrices(influxdb_service: InfluxDBService, days: int = 3):
    """
    Get N days of network data as 24x5 matrices (previous complete days only)
    
    Returns:
        - daily_matrices: List of 24x5 numpy arrays  
        - app_names: ['Google Chrome H', 'Slack', 'zoom.us', 'Music', 'Safari']
    """
    # Fixed top 5 apps (keep it simple)
    app_names = ['Google Chrome H', 'Slack', 'zoom.us', 'Music', 'Safari']
    
    # Get start of today, then go back N days
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today_start  # End at start of today (exclude today)
    start_date = end_date - timedelta(days=days)  # Go back N complete days
    
    print(f"📅 Getting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (excluding today)")
    
    # Query data
    query = f"""
    SELECT DATE_TRUNC('hour', time) AS hour,
           process_name,
           SUM("in") + SUM("out") AS total_usage
    FROM network_traffic
    WHERE time >= TIMESTAMP '{start_date.strftime('%Y-%m-%d %H:%M:%S')}'
      AND time < TIMESTAMP '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
    GROUP BY hour, process_name
    ORDER BY hour ASC, process_name
    """
    
    result = influxdb_service.client.query(query)
    df = result.to_pandas()
    
    # Create matrices
    daily_matrices = []
    
    for day_offset in range(days):
        target_date = start_date + timedelta(days=day_offset)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Filter day data
        day_data = df[(df['hour'] >= start_of_day) & (df['hour'] < end_of_day)]
        
        # Create 24x5 matrix
        matrix = np.zeros((24, 5))
        
        for _, row in day_data.iterrows():
            hour = row['hour'].hour
            app = row['process_name']
            
            if app in app_names:
                app_index = app_names.index(app)
                matrix[hour, app_index] = row['total_usage']
        
        daily_matrices.append(matrix)
        print(f"Day {day_offset + 1}: {target_date.strftime('%Y-%m-%d')} - {np.sum(matrix)/1024/1024:.1f} MB total")
    
    return daily_matrices, app_names


def get_today_matrix(influxdb_service: InfluxDBService):
    """
    Get today's data as 24x5 matrix
    """
    matrices, app_names = get_daily_matrices(influxdb_service, days=1)
    return matrices[0], app_names



if __name__ == "__main__":
    # Import .env and config file params
    import sys
    import os
    from dotenv import load_dotenv

    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_dir = os.path.abspath(os.path.join(current_script_dir, os.pardir))
    sys.path.insert(0, project_root_dir)

    # Import default configurations from your config file
    from config import config as default_config

    load_dotenv()

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
    matrices, apps = get_daily_matrices(db, days=1)
    print(matrices, apps)
