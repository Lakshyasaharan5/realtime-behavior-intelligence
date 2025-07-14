#!/usr/bin/env python3
"""
Generate dummy network data and insert into InfluxDB
Creates N days of realistic network usage patterns
"""

from datetime import datetime, timedelta
from shared_utils.db_factory import create_influxdb_service
import numpy as np


def create_hourly_pattern(hour):
    """Create realistic network pattern for a specific hour"""
    apps = ['Google Chrome H', 'Slack', 'zoom.us', 'Music', 'Safari']
    
    # Define patterns by hour
    if 0 <= hour <= 8:  # Sleep hours
        patterns = {
            'Google Chrome H': (0, 20),    # Occasional background sync
            'Slack': (0, 0),
            'zoom.us': (0, 0), 
            'Music': (0, 0),
            'Safari': (0, 0)
        }
    elif 9 <= hour <= 17:  # Work hours
        patterns = {
            'Google Chrome H': (200000, 400000),  # 200-400KB per minute
            'Slack': (30000, 80000),              # 30-80KB per minute  
            'zoom.us': (50000, 150000) if hour in [10, 14, 16] else (0, 30000),  # Meeting hours
            'Music': (0, 0),
            'Safari': (0, 0)
        }
    else:  # Evening hours (18-23)
        patterns = {
            'Google Chrome H': (800000, 1500000),  # Heavy streaming
            'Slack': (0, 0),
            'zoom.us': (0, 0),
            'Music': (100000, 300000),
            'Safari': (50000, 200000)
        }
    
    # Generate app usage for this hour
    hour_data = {}
    for app, (min_bytes, max_bytes) in patterns.items():
        if max_bytes > 0 and np.random.random() > 0.3:  # 70% chance app is active
            in_bytes = np.random.randint(min_bytes, max_bytes + 1)
            out_bytes = int(in_bytes * np.random.uniform(0.2, 0.6))  # out < in generally
            
            if in_bytes > 0 or out_bytes > 0:
                hour_data[app] = {
                    "in": in_bytes,
                    "out": out_bytes
                }
    
    return hour_data

def generate_dummy_data(days=7):
    """Generate N days of dummy data"""
    
    influxdb_service = create_influxdb_service()
    
    # Generate data starting from N days ago
    base_date = datetime.now() - timedelta(days=days)
    
    print(f"🚀 Generating {days} days of dummy network data...")
    
    for day in range(days):
        current_date = base_date + timedelta(days=day)
        print(f"📅 Day {day + 1}/{days}: {current_date.strftime('%Y-%m-%d')}")
        
        # Generate 24 hours of data for this day
        day_batch = []
        
        for hour in range(24):
            # Create multiple data points per hour (simulate your 1-minute collection)
            for minute in range(0, 60, 5):  # Every 5 minutes to simulate realistic collection
                timestamp = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Generate network usage for this time period
                app_net_usage = create_hourly_pattern(hour)
                
                if app_net_usage:  # Only add if there's some network activity
                    day_batch.append((timestamp, app_net_usage))
        
        # Insert day's data in batches
        batch_size = 50  # Match your collector buffer pattern
        for i in range(0, len(day_batch), batch_size):
            batch = day_batch[i:i + batch_size]
            try:
                influxdb_service.write_batch(batch)
                print(f"  ✓ Inserted batch {i//batch_size + 1} ({len(batch)} records)")
            except Exception as e:
                print(f"  ✗ Error inserting batch: {e}")
                continue
        
        print(f"  📊 Total records for {current_date.strftime('%Y-%m-%d')}: {len(day_batch)}")
    
    print(f"\n🎉 Successfully generated {days} days of dummy data!")
    print(f"📈 Data covers: {base_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate dummy network data")
    parser.add_argument("--days", type=int, default=7, help="Number of days to generate (default: 7)")
    args = parser.parse_args()
    
    generate_dummy_data(args.days)