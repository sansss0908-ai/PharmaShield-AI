"""
Trains a simple Random Forest classifier on synthetic shipment data
and saves it to engine/breach_predictor.joblib.
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator.generate_shipment import generate_shipment_data

def train_and_save_model():
    data_frames = []
    # Generate datasets with various failure points & severities
    for failure_start in [None, 1, 2, 3]:
        for severity in [0.8, 1.0, 1.5, 2.0]:
            df = generate_shipment_data(failure_start_index=failure_start, failure_severity=severity)
            data_frames.append(df)
            
    full_df = pd.concat(data_frames, ignore_index=True)
    
    full_df["temp_delta_1"] = full_df["temperature"].diff().fillna(0)
    full_df["temp_delta_3_avg"] = full_df["temperature"].diff().rolling(3).mean().fillna(0)
    full_df["temp_current"] = full_df["temperature"]
    
    # Target: temperature > 8.0 or temp rising fast (delta_1 > 0.3)
    full_df["breach_target"] = ((full_df["temperature"] > 8.0) | (full_df["temp_delta_1"] > 0.3)).astype(int)
    
    features = ["temp_current", "temp_delta_1", "temp_delta_3_avg", "humidity"]
    X = full_df[features]
    y = full_df["breach_target"]
    
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    os.makedirs("engine", exist_ok=True)
    model_path = os.path.join(os.path.dirname(__file__), "breach_predictor.joblib")
    joblib.dump(model, model_path)
    print(f"Successfully trained and saved model to {model_path}")

if __name__ == "__main__":
    train_and_save_model()
