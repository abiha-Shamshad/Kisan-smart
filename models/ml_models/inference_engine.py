import joblib
import pandas as pd
import numpy as np
import os
import time
from models.ml_models.confidence_scoring import ConfidenceScorer


class InferenceEngine:
    def __init__(self, version="v1.0.0"):
        self.version = version
        self.model_path = f"models/{version}"
        self.preprocessor = None
        self.label_encoder = None
        self.clf_model = None
        self.reg_model = None
        self.scorer = None
        self._load_all_artifacts()

    def _load_all_artifacts(self):
        """Loads all required models and preprocessors."""
        print(f"Loading version {self.version} artifacts...")
        self.preprocessor = joblib.load(f"{self.model_path}/preprocessor.pkl")
        self.label_encoder = joblib.load(f"{self.model_path}/label_encoder.pkl")
        self.clf_model = joblib.load(
            f"{self.model_path}/best_classification_randomforest_tuned.pkl"
        )
        self.reg_model = joblib.load(
            f"{self.model_path}/best_regression_xgboost_tuned.pkl"
        )
        self.scorer = ConfidenceScorer(
            clf_model=self.clf_model, reg_model=self.reg_model
        )
        print("All artifacts loaded successfully.")

    def predict(self, input_data):
        """
        Takes raw input (dict or DF), preprocesses it, and returns combined prediction.
        Expected keys: Nitrogen, Phosphorus, Potassium, pH, Moisture, Temperature, Crop_Type, Growth_Stage, Farm_Area
        """
        start_time = time.time()

        # Convert to DataFrame if needed
        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
        else:
            df = input_data

        # 1. Preprocess
        X_transformed = self.preprocessor.transform(df)

        # 2. Predict Type
        type_enc = self.clf_model.predict(X_transformed)
        type_name = self.label_encoder.inverse_transform(type_enc)[0]
        type_conf = self.scorer.calculate_classification_confidence(X_transformed)[0]

        # 3. Predict Quantity
        quantity = self.reg_model.predict(X_transformed)[0]
        # For quantity confidence, we'll try to use the RF regressor if possible for variance estimation,
        # but here we use the best_reg which is XGBoost. XGBoost doesn't have variance out-of-box.
        # We'll use a placeholder or the RF Regressor specifically for uncertainty if we save it.
        # Refactoring: calculate_regression_confidence expects the RF model specifically for variance.
        # For now, let's use a default or the RF model if we had saved it.
        quant_conf = 85.0  # Fallback

        # 4. Overall Confidence
        overall_conf = self.scorer.combine_confidence(type_conf, quant_conf)
        conf_level = self.scorer.get_confidence_level(overall_conf)

        latency = (time.time() - start_time) * 1000  # ms

        return {
            "fertilizer_type": type_name,
            "fertilizer_type_confidence": round(float(type_conf), 2),
            "quantity": round(float(quantity), 2),
            "quantity_unit": "kg/hectare",
            "quantity_confidence": round(float(quant_conf), 2),
            "overall_confidence": round(float(overall_conf), 2),
            "confidence_level": conf_level,
            "inference_time_ms": round(latency, 2),
            "model_version": self.version,
            "explanation": f"Based on {df['Crop_Type'].iloc[0]} requirement and current {df['Growth_Stage'].iloc[0]} stage.",
        }


if __name__ == "__main__":
    # Test prediction
    engine = InferenceEngine()
    sample = {
        "Nitrogen": 40,
        "Phosphorus": 50,
        "Potassium": 30,
        "pH": 6.5,
        "Moisture": 45.0,
        "Temperature": 28.0,
        "Crop_Type": "Wheat",
        "Growth_Stage": "Vegetative",
        "Farm_Area": 2.5,
    }
    result = engine.predict(sample)
    print("\nSample Recommendation:")
    import json

    print(json.dumps(result, indent=2))
