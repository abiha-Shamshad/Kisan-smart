import os
import joblib
import pandas as pd
import numpy as np

def verify():
    # Load artifacts
    preprocessor_path = "saved_models/preprocessor.pkl"
    model_path = "models/v1.0.0/classification_xgboost.pkl"
    le_path = "models/v1.0.0/label_encoder.pkl"
    
    preprocessor = joblib.load(preprocessor_path)
    model = joblib.load(model_path)
    le = joblib.load(le_path)
    
    # Create a mock input
    # Temparature,Humidity ,Moisture,Soil Type,Crop Type,Nitrogen,Potassium,Phosphorous
    mock_data = pd.DataFrame([{
        "Temparature": 26,
        "Humidity ": 52,
        "Moisture": 38,
        "Soil Type": "Sandy",
        "Crop Type": "Maize",
        "Nitrogen": 37,
        "Potassium": 0,
        "Phosphorous": 0
    }])
    
    print("Pre-processing mock input...")
    X_transformed = preprocessor.transform(mock_data)
    
    print("Performing inference...")
    y_pred_encoded = model.predict(X_transformed)
    y_pred_decoded = le.inverse_transform(y_pred_encoded)
    
    print(f"Prediction: {y_pred_decoded[0]}")
    print("Verification successful!")

if __name__ == "__main__":
    verify()
