import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KisanDataPipeline:
    def __init__(self, raw_path='data/raw/agricultural_data.csv', processed_path='data/processed/cleaned_data.csv'):
        self.raw_path = raw_path
        self.processed_path = processed_path
        self.df = None
        self.engine = None
        
    def load_data(self):
        """Loads data and displays basic information."""
        print(f"--- Loading data from {self.raw_path} ---")
        if not os.path.exists(self.raw_path):
            raise FileNotFoundError(f"Raw data file not found at {self.raw_path}")
        self.df = pd.read_csv(self.raw_path)
        print(f"Dataset Shape: {self.df.shape}")
        return self.df

    def inspect_data(self):
        """Performs initial data inspection."""
        print("\n--- Data Inspection ---")
        print("\nColumn Information:")
        print(self.df.info())
        print("\nMissing Values:")
        print(self.df.isnull().sum())
        print("\nDuplicate Rows:", self.df.duplicated().sum())
        print("\nStatistical Summary:")
        print(self.df.describe())
        return self.df

    def exploratory_data_analysis(self, output_dir='static/plots'):
        """Generates EDA visualizations."""
        print(f"\n--- Generating EDA Plots in {output_dir} ---")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 1. Distribution of Soil Parameters
        numerical_cols = ['Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'Moisture', 'Temperature']
        plt.figure(figsize=(15, 10))
        for i, col in enumerate(numerical_cols, 1):
            plt.subplot(2, 3, i)
            sns.histplot(self.df[col].dropna(), kde=True)
            plt.title(f'Distribution of {col}')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/feature_distributions.png')
        plt.close()

        # 2. Correlation Heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(self.df[numerical_cols].corr(), annot=True, cmap='coolwarm', fmt=".2f")
        plt.title('Feature Correlation Heatmap')
        plt.savefig(f'{output_dir}/correlation_heatmap.png')
        plt.close()

        # 3. Crop Type Distribution
        plt.figure(figsize=(10, 6))
        sns.countplot(data=self.df, x='Crop_Type')
        plt.title('Crop Type Counts')
        plt.xticks(rotation=45)
        plt.savefig(f'{output_dir}/crop_distribution.png')
        plt.close()

        print("EDA completed and plots saved.")

    def clean_data(self):
        """Handles missing values and outliers."""
        print("\n--- Cleaning Data ---")
        # 1. Impute missing values with median for numerical columns
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            self.df[col] = self.df[col].fillna(self.df[col].median())

        # 2. Outlier removal/capping for Nitrogen (example)
        # Using 1.5 * IQR rule
        Q1 = self.df['Nitrogen'].quantile(0.25)
        Q3 = self.df['Nitrogen'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Capping outliers
        self.df['Nitrogen'] = np.where(self.df['Nitrogen'] > upper_bound, upper_bound, 
                                     np.where(self.df['Nitrogen'] < lower_bound, lower_bound, self.df['Nitrogen']))
        
        print("Data cleaning completed.")
        return self.df

    def transform_data(self):
        """Feature engineering and encoding."""
        print("\n--- Transforming Data ---")
        # Example: NPK Ratio
        self.df['Total_Nutrients'] = self.df['Nitrogen'] + self.df['Phosphorus'] + self.df['Potassium']
        
        # Encode categorical variables for ML (demonstration)
        # Note: We keep original columns for DB loading if needed, or save a separate version for training
        self.df.to_csv(self.processed_path, index=False)
        print(f"Cleaned and transformed data saved to {self.processed_path}")
        return self.df

    def load_to_postgresql(self):
        """Batch loads cleaned data into PostgreSQL database."""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("DATABASE_URL not found in environment. Skipping database load.")
            return

        print("\n--- Loading Data to PostgreSQL ---")
        try:
            self.engine = create_engine(db_url)
            # We will load into a staging table 'raw_agricultural_data'
            # In a real scenario, we'd map this to our schema tables
            self.df.to_sql('raw_agricultural_data', con=self.engine, if_exists='replace', index=False)
            print("Successfully loaded data into table 'raw_agricultural_data'.")
        except Exception as e:
            print(f"Error loading to database: {e}")

if __name__ == "__main__":
    pipeline = KisanDataPipeline()
    pipeline.load_data()
    pipeline.inspect_data()
    pipeline.exploratory_data_analysis()
    pipeline.clean_data()
    pipeline.transform_data()
    # pipeline.load_to_postgresql() # Requires active DB connection
