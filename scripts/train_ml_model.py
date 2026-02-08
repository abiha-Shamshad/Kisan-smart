from models.ml_models.data_loader import DataLoader
from models.ml_models.feature_engineering import FeatureEngineer
from models.ml_models.model_trainer import ModelTrainer
from models.ml_models.model_evaluator import ModelEvaluator
from models.ml_models.hyperparameter_tuner import HyperparameterTuner
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np
import joblib
import os

def run_pipeline(version='v1.0.0'):
    print(f"--- Starting Kisan Smart ML Pipeline ({version}) ---")
    
    # 1. Load Data
    print("\n--- 1. Data Loading ---")
    loader = DataLoader('data/raw/agricultural_data.csv')
    df = loader.load_data()
    
    # We will do Classification first (Fertilizer Type)
    X_train, X_val, X_test, y_train_type, y_val_type, y_test_type = loader.split_data(target_col='Fertilizer')
    
    # Then Regression (Fertilizer Quantity)
    _, _, _, y_train_quant, y_val_quant, y_test_quant = loader.split_data(target_col='Quantity')

    # Encode Classification Target
    le = LabelEncoder()
    y_train_type_enc = le.fit_transform(y_train_type)
    y_val_type_enc = le.transform(y_val_type)
    os.makedirs(f'models/{version}', exist_ok=True)
    joblib.dump(le, f'models/{version}/label_encoder.pkl')
    labels_enc = sorted(np.unique(y_train_type_enc))

    # 2. Feature Engineering
    print("\n--- 2. Feature Engineering ---")
    fe = FeatureEngineer()
    num_cols = ['Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'Moisture', 'Temperature', 'Farm_Area']
    cat_cols = ['Crop_Type', 'Growth_Stage']
    fe.create_pipeline(num_cols, cat_cols)
    
    X_train_transformed = fe.fit_transform(X_train)
    X_val_transformed = fe.transform(X_val)
    fe.save_pipeline(f'models/{version}/preprocessor.pkl')

    # 3. Classification Training
    print("\n--- 3. Classification Training (Type) ---")
    clf_trainer = ModelTrainer(mode='classification')
    clf_trainer.train_all(X_train_transformed, y_train_type_enc)
    clf_results = clf_trainer.evaluate_all(X_val_transformed, y_val_type_enc)
    print(clf_results)
    
    clf_tuner = HyperparameterTuner(mode='classification')
    best_clf = clf_tuner.tune_random_forest(X_train_transformed, y_train_type_enc)
    clf_tuner.save_best_model('RandomForest', version=version)

    # 4. Regression Training
    print("\n--- 4. Regression Training (Quantity) ---")
    reg_trainer = ModelTrainer(mode='regression')
    reg_trainer.train_all(X_train_transformed, y_train_quant)
    reg_results = reg_trainer.evaluate_all(X_val_transformed, y_val_quant)
    print(reg_results)
    
    reg_tuner = HyperparameterTuner(mode='regression')
    best_reg = reg_tuner.tune_xgboost(X_train_transformed, y_train_quant)
    reg_tuner.save_best_model('XGBoost', version=version)

    # 5. Advanced Evaluation
    print("\n--- 5. Advanced Evaluation & Plots ---")
    evaluator = ModelEvaluator()
    
    # Classification Plots for Best Model
    evaluator.save_report(y_val_type_enc, best_clf.predict(X_val_transformed), 'best_classifier', mode='classification')
    evaluator.plot_confusion_matrix(y_val_type_enc, best_clf.predict(X_val_transformed), 'best_classifier', labels_enc)
    evaluator.plot_roc_curve(best_clf, X_val_transformed, y_val_type_enc, 'best_classifier', labels_enc)
    
    # Regression Plots for Best Model
    y_pred_quant = best_reg.predict(X_val_transformed)
    evaluator.save_report(y_val_quant, y_pred_quant, 'best_regressor', mode='regression')
    evaluator.plot_regression_results(y_val_quant, y_pred_quant, 'best_regressor')
    evaluator.plot_residuals(y_val_quant, y_pred_quant, 'best_regressor')

    print(f"\nML Pipeline Completed. Artifacts saved in models/{version}/ and results/visualizations/")

if __name__ == "__main__":
    run_pipeline()
