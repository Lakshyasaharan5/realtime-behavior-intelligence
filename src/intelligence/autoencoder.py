"""
Simple autoencoder for network behavior anomaly detection
"""

import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from datetime import datetime


def create_autoencoder():
    """
    Create a simple autoencoder for 24x5 daily matrices
    
    Input: 120 features (24 hours × 5 apps)
    Architecture: 120 → 60 → 30 → 10 → 30 → 60 → 120
    """
    model = Sequential([
        # Encoder: Compress to smaller representation
        Dense(60, activation='relu', input_shape=(120,)),
        Dense(30, activation='relu'),
        Dense(10, activation='relu'),  # Bottleneck - forces learning of patterns
        
        # Decoder: Reconstruct back to original size
        Dense(30, activation='relu'),
        Dense(60, activation='relu'),
        Dense(120, activation='linear')  # Linear output for reconstruction
    ])
    
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model


def prepare_training_data(daily_matrices):
    """
    Convert list of 24x5 matrices to training format
    
    Args:
        daily_matrices: List of 24x5 numpy arrays
        
    Returns:
        X_train: Normalized training data (n_days, 120)
        max_value: Maximum value for denormalization
    """
    # Flatten each day into 120 features
    X_train = np.array([matrix.flatten() for matrix in daily_matrices])
    
    # Simple normalization (divide by max to keep 0-1 range)
    max_value = X_train.max()
    X_train_scaled = X_train / max_value if max_value > 0 else X_train
    
    print(f"📊 Training data shape: {X_train_scaled.shape}")
    print(f"📏 Max value for scaling: {max_value:.0f}")
    
    return X_train_scaled, max_value


def train_autoencoder(autoencoder, X_train, epochs=100):
    """
    Train the autoencoder
    
    Args:
        autoencoder: Keras model
        X_train: Training data
        epochs: Number of training epochs
        
    Returns:
        training_history: Training loss history
    """
    print(f"🚀 Training autoencoder for {epochs} epochs...")
    
    history = autoencoder.fit(
        X_train, X_train,  # Input = Output (reconstruction task)
        epochs=epochs,
        batch_size=1,      # Small batch since we have few days
        verbose=1,
        shuffle=True
    )
    
    final_loss = history.history['loss'][-1]
    print(f"✅ Training complete! Final loss: {final_loss:.6f}")
    
    return history


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


def set_threshold(autoencoder, training_matrices, max_value, multiplier=1.5):
    """
    Set anomaly detection threshold based on training data
    
    Args:
        autoencoder: Trained model
        training_matrices: List of training matrices
        max_value: Scaling factor
        multiplier: Threshold multiplier (higher = less sensitive)
        
    Returns:
        threshold: Anomaly detection threshold
    """
    training_errors = []
    
    for matrix in training_matrices:
        error = calculate_reconstruction_error(autoencoder, matrix, max_value)
        training_errors.append(error)
    
    max_training_error = max(training_errors)
    threshold = max_training_error * multiplier
    
    print(f"📈 Training errors: {training_errors}")
    print(f"🎯 Threshold set to: {threshold:.6f} ({multiplier}x max training error)")
    
    return threshold


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

def create_anomaly_test_data(influxdb_service, anomaly_type="movies_at_work"):
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
        anomaly_matrix = create_anomaly_test_data(None, anomaly_type)
        
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

if __name__ == "__main__":
    # Example of how to use it
    from src.intelligence.data_aggregator import get_daily_matrices
    from src.intelligence.autoencoder import *
    from src.db.influxdb_service import InfluxDBService

    # Get training data
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
    influxdb_service = InfluxDBService(INFLUXDB_PARAMS)
    daily_matrices, app_names = get_daily_matrices(influxdb_service, days=3)

    # Prepare and train
    X_train, max_value = prepare_training_data(daily_matrices)
    autoencoder = create_autoencoder()
    history = train_autoencoder(autoencoder, X_train)

    # Set threshold
    threshold = set_threshold(autoencoder, daily_matrices, max_value)

    # Test on new day
    test_matrix, _ = get_daily_matrices(influxdb_service, days=1)
    is_anomaly, error = detect_anomaly(autoencoder, test_matrix[0], max_value, threshold)

    test_anomaly_detection(autoencoder, max_value, threshold)