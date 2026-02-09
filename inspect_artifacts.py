import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

model_path = "models/v1.0.0"
preprocessor = joblib.load(f"{model_path}/preprocessor.pkl")

def find_categories(transformer):
    if hasattr(transformer, "categories_"):
        return transformer.categories_
    if isinstance(transformer, Pipeline):
        for name, step in transformer.steps:
            res = find_categories(step)
            if res is not None:
                return res
    return None

if isinstance(preprocessor, ColumnTransformer):
    for name, transformer, cols in preprocessor.transformers_:
        print(f"\nTransformer {name} for {cols}")
        cats = find_categories(transformer)
        if cats is not None:
            for i, col in enumerate(cols):
                print(f"  {col}: {list(cats[i])}")
