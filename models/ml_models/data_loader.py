import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os

class DataLoader:
    def __init__(self, data_path='data/raw/agricultural_data.csv'):
        self.data_path = data_path
        self.df = None

    def load_data(self):
        """Loads and performs initial verification of the dataset."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found at {self.data_path}")
        
        self.df = pd.read_csv(self.data_path)
        print(f"Dataset loaded successfully. Shape: {self.df.shape}")
        
        # Basic quality check
        missing = self.df.isnull().sum().sum()
        if missing > 0:
            print(f"Warning: {missing} missing values detected. These should be handled in preprocessing.")
            
        return self.df

    def split_data(self, target_col='Fertilizer', test_size=0.15, val_size=0.15, random_state=42):
        """Splits data into train, validation, and test sets with stratification if applicable."""
        if self.df is None:
            self.load_data()
            
        if target_col not in self.df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset.")
            
        X = self.df.drop(columns=['Fertilizer', 'Quantity']) # Drop both possible targets
        y = self.df[target_col]
        
        # Use stratification only for classification (discrete targets)
        is_classification = self.df[target_col].dtype == 'object'
        stratify = y if is_classification else None
        
        # First split: Train vs (Val + Test)
        X_train, X_rem, y_train, y_rem = train_test_split(
            X, y, test_size=(test_size + val_size), random_state=random_state, stratify=stratify
        )
        
        # Second split: Validation vs Test
        test_ratio_of_rem = test_size / (test_size + val_size)
        
        # Adjust stratify for second split if needed
        stratify_rem = y_rem if is_classification else None
        
        X_val, X_test, y_val, y_test = train_test_split(
            X_rem, y_rem, test_size=test_ratio_of_rem, random_state=random_state, stratify=stratify_rem
        )
        
        print(f"Data split ratios for {target_col}: Train({len(X_train)}), Val({len(X_val)}), Test({len(X_test)})")
        return X_train, X_val, X_test, y_train, y_val, y_test

if __name__ == "__main__":
    loader = DataLoader()
    X_train, X_val, X_test, y_train, y_val, y_test = loader.split_data()
