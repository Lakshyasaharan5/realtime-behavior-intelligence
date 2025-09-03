"""
This file is responsible for fetching N days of data 
from database and creating matrix of each day for the autoencoder model.
"""
from datetime import datetime, timedelta
from src.db.influxdb_service import InfluxDBService
import pandas as pd
import numpy as np

DEFAULT_DAYS = 4

class DataProcessor:
    def __init__(self, influxdb: InfluxDBService = None, days: int = DEFAULT_DAYS):
        self.influxdb = influxdb
        self.days = days

        # Fixed top 5 apps (keep it simple)
        self.app_names = ['Google Chrome H', 'Slack', 'zoom.us', 'Music', 'Safari']

        # Get start of today, then go back N days
        # today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_start = datetime(2025, 7, 4).replace(hour=0, minute=0, second=0, microsecond=0)        
        self.end_date = today_start  # End at start of today (exclude today)
        self.start_date = self.end_date - timedelta(days=self.days)  # Go back N complete days

    def get_data_from_db(self) ->  pd.DataFrame:                
        print(f"Getting data from {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')} (excluding today)")
        
        # Query data
        query = f"""
        SELECT DATE_TRUNC('hour', time) AS hour,
            process_name,
            SUM("in") + SUM("out") AS total_usage
        FROM network_traffic
        WHERE time >= TIMESTAMP '{self.start_date.strftime('%Y-%m-%d %H:%M:%S')}'
        AND time < TIMESTAMP '{self.end_date.strftime('%Y-%m-%d %H:%M:%S')}'
        GROUP BY hour, process_name
        ORDER BY hour ASC, process_name
        """
        
        result = self.influxdb.client.query(query)
        df = result.to_pandas()

        return df

    def create_matrices(self, df: pd.DataFrame):
        daily_matrices = []
    
        for day_offset in range(self.days):
            target_date = self.start_date + timedelta(days=day_offset)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Filter day data
            day_data = df[(df['hour'] >= start_of_day) & (df['hour'] < end_of_day)]
            
            # Create 24x5 matrix
            matrix = np.zeros((24, 5))
            
            for _, row in day_data.iterrows():
                hour = row['hour'].hour
                app = row['process_name']
                
                if app in self.app_names:
                    app_index = self.app_names.index(app)
                    matrix[hour, app_index] = row['total_usage']
            
            daily_matrices.append(matrix)
            print(f"Day {day_offset + 1}: {target_date.strftime('%Y-%m-%d')} - {np.sum(matrix)/1024/1024:.1f} MB total")
        
        return daily_matrices
    
    def scale(self, baseline_days, test_day):
        baseline_days_flatten = np.array([matrix.flatten() for matrix in baseline_days])
        test_day_flatten = np.array([matrix.flatten() for matrix in test_day])
        max_value = baseline_days_flatten.max()
        baseline_days_scaled = baseline_days_flatten / max_value if max_value > 0 else baseline_days_flatten
        test_day_scaled = test_day_flatten / max_value if max_value > 0 else test_day_flatten
        return baseline_days_scaled, test_day_scaled, max_value

    
