from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler
from sklearn.impute import SimpleImputer
import pandas as pd
import joblib
import os

class FeatureEngineer:
    def __init__(self):
        self.pipeline = None
        self.feature_names = None

    def create_pipeline(self, numerical_cols, categorical_cols):
        """Creates an sklearn Pipeline for preprocessing."""
        num_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', RobustScaler()) # Robust to outliers like the ones we generated
        ])

        cat_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        self.pipeline = ColumnTransformer(
            transformers=[
                ('num', num_transformer, numerical_cols),
                ('cat', cat_transformer, categorical_cols)
            ]
        )
        return self.pipeline

    def fit_transform(self, X):
        """Fits the pipeline and transforms the data."""
        X_transformed = self.pipeline.fit_transform(X)
        
        # Get feature names after one-hot encoding
        try:
            cat_features = self.pipeline.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out()
            num_features = self.pipeline.named_transformers_['num'].feature_names_in_ if hasattr(self.pipeline.named_transformers_['num'], 'feature_names_in_') else []
            self.feature_names = list(num_features) + list(cat_features)
        except:
            pass # Fallback if feature names can't be retrieved
            
        return X_transformed

    def transform(self, X):
        """Transforms data using the fitted pipeline."""
        return self.pipeline.transform(X)

    def save_pipeline(self, path='saved_models/preprocessor.pkl'):
        """Saves the fitted pipeline artifact."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.pipeline, path)
        print(f"Preprocessor pipeline saved to {path}")

if __name__ == "__main__":
    # Example usage
    fe = FeatureEngineer()
    num_cols = ['Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'Moisture', 'Temperature', 'Farm_Area']
    cat_cols = ['Crop_Type', 'Growth_Stage']
    fe.create_pipeline(num_cols, cat_cols)
    print("Pipeline created successfully.")

    @staticmethod
    def load_pipeline(path='saved_models/preprocessor.pkl'):
        """Loads a pre-trained pipeline."""
        if os.path.exists(path):
            return joblib.load(path)
        return None
