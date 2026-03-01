import os
import sys
import pandas as pd
from models.ml_models.data_loader import DataLoader
from models.ml_models.feature_engineering import FeatureEngineer
from models.ml_models.model_trainer import ModelTrainer

def main():
    # 1. Load Data
    loader = DataLoader(data_path="data/raw/agricultural_data.csv")
    df = loader.load_data()
    
    # 2. Preprocess Data
    # Define columns based on the dataset structure
    num_cols = ["Temparature", "Humidity ", "Moisture", "Nitrogen", "Potassium", "Phosphorous"]
    cat_cols = ["Soil Type", "Crop Type"]
    target_col = "Fertilizer Name"
    
    fe = FeatureEngineer()
    fe.create_pipeline(num_cols, cat_cols)
    
    X_train, X_val, X_test, y_train, y_val, y_test = loader.split_data(target_col=target_col)
    
    # Fit and transform
    X_train_transformed = fe.fit_transform(X_train)
    X_val_transformed = fe.transform(X_val)
    X_test_transformed = fe.transform(X_test)
    
    # Save the pipeline
    fe.save_pipeline("saved_models/preprocessor.pkl")
    
    # 3. Train Models
    trainer = ModelTrainer(mode="classification")
    trainer.train_all(X_train_transformed, y_train)
    
    # 4. Evaluate Models
    results = trainer.evaluate_all(X_val_transformed, y_val)
    print("\nValidation Results:")
    print(results)
    
    # 5. Save the best model (e.g., XGBoost if it's available and performs well)
    # For now, let's save RandomForest
    trainer.save_model("RandomForest", version="v1.0.0")
    trainer.save_model("XGBoost", version="v1.0.0")

if __name__ == "__main__":
    main()
