from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC, SVR
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import (
    accuracy_score,
    r2_score,
    mean_absolute_error,
    mean_squared_error,
)
import joblib
import pandas as pd
import numpy as np
import os


class ModelTrainer:
    def __init__(self, mode="classification"):
        self.mode = mode
        if mode == "classification":
            self.models = {
                "LogisticRegression": LogisticRegression(
                    max_iter=1000, random_state=42
                ),
                "RandomForest": RandomForestClassifier(
                    n_estimators=100, random_state=42
                ),
                "SVM": SVC(probability=True, random_state=42),
                "XGBoost": XGBClassifier(
                    use_label_encoder=False, eval_metric="mlogloss", random_state=42
                ),
            }
        else:  # regression
            self.models = {
                "LinearRegression": LinearRegression(),
                "RandomForest": RandomForestRegressor(
                    n_estimators=100, random_state=42
                ),
                "SVR": SVR(kernel="rbf"),
                "XGBoost": XGBRegressor(
                    objective="reg:squarederror", n_estimators=100, random_state=42
                ),
            }
        self.trained_models = {}

    def train_all(self, X_train, y_train):
        """Trains all configured models."""
        print(f"--- Starting {self.mode.capitalize()} Model Training ---")
        for name, model in self.models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            self.trained_models[name] = model
        print("Training completed.")

    def evaluate_all(self, X_val, y_val):
        """Evaluates all trained models on validation set."""
        results = []
        print(f"\n--- {self.mode.capitalize()} Evaluation Results ---")
        for name, model in self.trained_models.items():
            y_pred = model.predict(X_val)
            if self.mode == "classification":
                score = accuracy_score(y_val, y_pred)
                print(f"{name} Accuracy: {score:.4f}")
                results.append({"Model": name, "Accuracy": score})
            else:
                r2 = r2_score(y_val, y_pred)
                mae = mean_absolute_error(y_val, y_pred)
                rmse = np.sqrt(mean_squared_error(y_val, y_pred))
                print(f"{name} R2: {r2:.4f}, MAE: {mae:.2f}, RMSE: {rmse:.2f}")
                results.append({"Model": name, "R2": r2, "MAE": mae, "RMSE": rmse})

        return pd.DataFrame(results)

    def save_model(self, model_name, version="v1.0.0", path=None):
        """Saves a specific trained model with versioning."""
        if path is None:
            path = f"models/{version}/{self.mode}_{model_name.lower()}.pkl"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.trained_models[model_name], path)
        print(f"Model {model_name} saved to {path}")


if __name__ == "__main__":
    print("ModelTrainer module initialized.")
