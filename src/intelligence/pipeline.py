"""
This files runs the anomaly detection pipeline flow. 
It will call the data processor and then autoencoder model to check anomaly of the previous day.
"""

from shared_utils.db_factory import create_influxdb_service
from src.intelligence.data_processor import DataProcessor
from src.intelligence.autoencoder import Autoencoder

import numpy as np

def main():
    # ==================== Preprocessing ====================
    # 1. Load data
    data_processor = DataProcessor(create_influxdb_service(), 7)
    data = data_processor.get_data_from_db()
    matrices = data_processor.create_matrices(data)

    # 2. Train-test split 
    baseline_days = matrices[:-1]
    test_day = matrices[-1:]

    # 3. Simple normalization (divide by max to keep 0-1 range)    
    baseline_days_scaled, test_day_scaled, max_value = data_processor.scale(baseline_days, test_day)

    # ==================== Autoencoder model ===========================
    # 1. create model
    autoencoder = Autoencoder()

    # 2. train on baseline days
    autoencoder.fit(baseline_days_scaled)

    # 3. set threshold
    autoencoder.set_threshold(baseline_days_scaled)

    # 4. check anomaly of test day
    autoencoder.detect_anomaly(test_day_scaled)


    
if __name__=="__main__":
    main()