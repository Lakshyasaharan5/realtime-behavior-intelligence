"""
Simple autoencoder for network behavior anomaly detection
"""

import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from datetime import datetime


class Autoencoder:
    def __init__(self):
        """
        Create a simple autoencoder for 24x5 daily matrices
        
        Input: 120 features (24 hours × 5 apps)
        Architecture: 120 → 60 → 30 → 10 → 30 → 60 → 120
        """
        self.model = Sequential([
            # Encoder: Compress to smaller representation
            Dense(60, activation='relu', input_shape=(120,)),
            Dense(30, activation='relu'),
            Dense(10, activation='relu'),  # Bottleneck - forces learning of patterns
            
            # Decoder: Reconstruct back to original size
            Dense(30, activation='relu'),
            Dense(60, activation='relu'),
            Dense(120, activation='linear')  # Linear output for reconstruction
        ])
        self.model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

        self.threshold = None

    def fit(self, X_train):
        print(f"Training autoencoder....")
        
        history = self.model.fit(
            X_train, X_train,  # Input = Output (reconstruction task)
            epochs=100,
            batch_size=1,      # Small batch since we have few days
            verbose=1,
            shuffle=True
        )
        
        final_loss = history.history['loss'][-1]
        print(f"Training complete! Final loss: {final_loss:.6f}")  

    def evaluate(self, X_test):
        # Get reconstruction
        reconstruction = self.model.predict(X_test, verbose=0)
        
        # Calculate MSE
        error = np.mean((X_test.flatten() - reconstruction.flatten())**2)
        
        return error
    
    def set_threshold(self, training_matrices, tolerance: int = 1.5):
        training_errors = []
    
        for matrix in training_matrices:
            matrix = matrix.reshape(1, -1)
            error = self.evaluate(matrix)
            training_errors.append(error)
        
        max_training_error = max(training_errors)
        self.threshold = max_training_error * tolerance
        
        print(f"Training errors: {training_errors}")
        print(f"Threshold set to: {self.threshold:.6f} ({tolerance}x max training error)")    

    def detect_anomaly(self, test_day):
        error = self.evaluate(test_day)
        is_anomaly = error > self.threshold

        status = "ANOMALY" if is_anomaly else "NORMAL"
        print(f"Reconstruction error: {error:.6f} - {status}")
        
        return is_anomaly
