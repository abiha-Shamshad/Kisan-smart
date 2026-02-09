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
            # Map lowercase keys to expected CamelCase
            key_map = {
                "nitrogen": "Nitrogen",
                "phosphorus": "Phosphorus",
                "potassium": "Potassium",
                "ph": "pH",
                "moisture": "Moisture",
                "temperature": "Temperature",
                "crop_type": "Crop_Type",
                "growth_stage": "Growth_Stage",
                "farm_area": "Farm_Area"
            }
            mapped_data = {}
            # Defaults for all expected columns
            expected_defaults = {
                "Nitrogen": 0.0,
                "Phosphorus": 0.0,
                "Potassium": 0.0,
                "pH": 6.5,
                "Moisture": 0.0,
                "Temperature": 25.0,
                "Crop_Type": "Wheat",
                "Growth_Stage": "Vegetative",
                "Farm_Area": 1.0
            }
            mapped_data.update(expected_defaults)
            for k, v in input_data.items():
                mapped_data[key_map.get(k.lower(), k)] = v
            
            # Capitalize categorical values if they are strings
            for col in ["Crop_Type", "Growth_Stage"]:
                if isinstance(mapped_data[col], str):
                    mapped_data[col] = mapped_data[col].capitalize()

            df = pd.DataFrame([mapped_data])
            # Reorder columns to match expected order if necessary (optional but safe)
            column_order = ["Nitrogen", "Phosphorus", "Potassium", "pH", "Moisture", "Temperature", "Crop_Type", "Growth_Stage", "Farm_Area"]
            df = df[column_order]

            # Validation
            for nutrient in ["Nitrogen", "Phosphorus", "Potassium"]:
                if mapped_data[nutrient] < 0:
                    raise ValueError(f"{nutrient} cannot be negative")
            if mapped_data["pH"] < 0 or mapped_data["pH"] > 14:
                raise ValueError("pH must be between 0 and 14")
            
            # Crop/Growth Stage validation (optional but good for testing)
            supported_crops = ["Cotton", "Maize", "Rice", "Sugarcane", "Wheat"]
            supported_stages = ["Flowering", "Maturity", "Vegetative"]
            
            if mapped_data["Crop_Type"] not in supported_crops:
                raise ValueError(f"Unsupported crop: {mapped_data['Crop_Type']}")
            
            if mapped_data["Growth_Stage"] not in supported_stages:
                raise ValueError(f"Unsupported growth stage: {mapped_data['Growth_Stage']}")

        else:
            df = input_data

        # 1. Preprocess
        try:
            # print(f"DEBUG: df.columns={df.columns.tolist()}")
            # print(f"DEBUG: df.head()=\n{df.head()}")
            X_transformed = self.preprocessor.transform(df)
        except Exception as te:
            print(f"ERROR during transform: {te}")
            print(f"DF columns sent: {df.columns.tolist()}")
            print(f"DF values sent: {df.values.tolist()}")
            raise te

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
            "quantity": round(float(quantity), 2),
            "quantity_unit": "kg/hectare",
            "confidence": {
                "fertilizer_type_confidence": round(float(type_conf), 2),
                "quantity_confidence": round(float(quant_conf), 2),
                "overall_confidence": round(float(overall_conf), 2),
                "level": conf_level
            },
            "inference_time_ms": round(latency, 2),
            "model_version": self.version,
            "explanation": f"Based on {mapped_data.get('Crop_Type', 'Unknown')} requirement and current {mapped_data.get('Growth_Stage', 'Unknown')} stage.",
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
