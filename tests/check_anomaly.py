"""
This files runs the anomaly detection pipeline flow. 
It will call the data processor and then autoencoder model to check anomaly of the previous day.
"""

from shared_utils.db_factory import create_influxdb_service
from src.intelligence.data_processor import DataProcessor
from src.intelligence.autoencoder import Autoencoder

import numpy as np

def create_anomaly_test_data(anomaly_type="movies_at_work"):
    """
    Create and insert anomalous data for testing
    
    Args:
        anomaly_type: "movies_at_work" or "work_at_night" or "all_night_streaming"
    """
    from datetime import datetime, timedelta
    
    # Use yesterday as our anomaly day
    anomaly_date = datetime.now() - timedelta(days=1)
    
    if anomaly_type == "movies_at_work":
        print("🎬 Creating 'Movies at Work' anomaly...")
        # High Chrome streaming + Music during work hours (9-17)
        anomaly_matrix = np.zeros((24, 5))
        
        # Sleep hours (0-8): Normal minimal usage
        for hour in range(9):
            anomaly_matrix[hour] = [50000, 0, 0, 0, 0]  # Just Chrome background
        
        # Work hours (9-17): HIGH entertainment usage (ANOMALY!)
        for hour in range(9, 18):
            anomaly_matrix[hour] = [12000000, 5000, 0, 2000000, 500000]  # Massive streaming + music during work
        
        # Evening (18-23): Normal evening usage
        for hour in range(18, 24):
            anomaly_matrix[hour] = [8000000, 0, 0, 1500000, 800000]
    
    elif anomaly_type == "work_at_night":
        print("🌙 Creating 'Work at Night' anomaly...")
        anomaly_matrix = np.zeros((24, 5))
        
        # Sleep hours (0-8): Normal
        for hour in range(9):
            anomaly_matrix[hour] = [50000, 0, 0, 0, 0]
        
        # Work hours (9-17): Very light usage
        for hour in range(9, 18):
            anomaly_matrix[hour] = [500000, 20000, 0, 0, 0]
        
        # Evening (18-23): WORK APPS ACTIVE (ANOMALY!)
        for hour in range(18, 24):
            anomaly_matrix[hour] = [3000000, 600000, 800000, 0, 0]  # Work apps at night
    
    elif anomaly_type == "all_night_streaming":
        print("🌃 Creating 'All Night Streaming' anomaly...")
        anomaly_matrix = np.zeros((24, 5))
        
        # ALL HOURS: High streaming (ANOMALY!)
        for hour in range(24):
            anomaly_matrix[hour] = [15000000, 0, 0, 3000000, 1000000]  # 24/7 streaming
    
    return anomaly_matrix

def calculate_reconstruction_error(autoencoder, matrix, max_value):
    """
    Calculate reconstruction error for a single day
    
    Args:
        autoencoder: Trained model
        matrix: 24x5 daily matrix
        max_value: Scaling factor
        
    Returns:
        error: Reconstruction error (MSE)
    """
    # Flatten and normalize
    flattened = matrix.flatten()
    normalized = flattened / max_value if max_value > 0 else flattened
    
    # Reshape for prediction
    input_data = normalized.reshape(1, -1)
    
    # Get reconstruction
    reconstruction = autoencoder.predict(input_data, verbose=0)
    
    # Calculate MSE
    error = np.mean((normalized - reconstruction.flatten())**2)
    
    return error

def detect_anomaly(autoencoder, matrix, max_value, threshold):
    """
    Detect if a day is anomalous
    
    Args:
        autoencoder: Trained model
        matrix: 24x5 daily matrix to test
        max_value: Scaling factor
        threshold: Anomaly threshold
        
    Returns:
        is_anomaly: Boolean
        error: Reconstruction error
    """
    error = calculate_reconstruction_error(autoencoder, matrix, max_value)
    is_anomaly = error > threshold
    
    status = "ANOMALY" if is_anomaly else "NORMAL"
    print(f"🔍 Reconstruction error: {error:.6f} - {status}")
    
    return is_anomaly, error

def test_anomaly_detection(autoencoder, max_value, threshold):
    """
    Test the autoencoder with different anomaly types
    """
    print("\n" + "="*50)
    print("🧪 TESTING ANOMALY DETECTION")
    print("="*50)
    
    anomaly_types = ["movies_at_work", "work_at_night", "all_night_streaming"]
    
    for anomaly_type in anomaly_types:
        print(f"\n--- Testing {anomaly_type.replace('_', ' ').title()} ---")
        
        # Create anomaly matrix
        anomaly_matrix = create_anomaly_test_data(anomaly_type)
        
        # Test it
        is_anomaly, error = detect_anomaly(autoencoder, anomaly_matrix, max_value, threshold)
        
        # Show total usage for context
        total_mb = np.sum(anomaly_matrix) / (1024 * 1024)
        print(f"📊 Total usage: {total_mb:.1f} MB")
        print(f"🎯 Expected: ANOMALY, Got: {'ANOMALY' if is_anomaly else 'NORMAL'}")
        
        if not is_anomaly:
            print("⚠️  This should have been detected as anomaly!")
        else:
            print("✅ Correctly detected as anomaly!")

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
    autoencoder.set_threshold(baseline_days_scaled, 1)

    # 4. check anomaly of test day
    autoencoder.detect_anomaly(test_day_scaled)

    # ==================== Test anomaly ===========================
    test_anomaly_detection(autoencoder.model, max_value, autoencoder.threshold)

    
if __name__=="__main__":
    main()