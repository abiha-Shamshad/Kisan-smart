import pandas as pd
import numpy as np


def generate_synthetic_data(num_samples=10000):
    """
    Generates synthetic agricultural data for fertilizer recommendation.
    N, P, K levels, pH, moisture, temperature, crop type, fertilizer.
    """
    np.random.seed(42)

    crops = ["Wheat", "Rice", "Maize", "Cotton", "Sugarcane", "Pulse"]
    fertilizers = ["Urea", "DAP", "NPK 15-15-15", "NPK 10-26-26", "MOP"]
    stages = ["Initial", "Vegetative", "Flowering", "Maturity"]

    # Generate features
    nitrogen = np.random.randint(10, 150, num_samples)
    phosphorus = np.random.randint(5, 100, num_samples)
    potassium = np.random.randint(5, 100, num_samples)
    ph = np.random.uniform(5.5, 8.5, num_samples)
    moisture = np.random.uniform(10, 80, num_samples)
    temp = np.random.uniform(15, 35, num_samples)
    crop_choice = np.random.choice(crops, num_samples)
    growth_stage = np.random.choice(stages, num_samples)
    farm_area = np.random.uniform(0.5, 20.0, num_samples)  # hectares

    # Logic for Fertilizer Recommendation and Quantity
    fertilizer_choice = []
    quantity_choice = []
    for i in range(num_samples):
        n, p, k = nitrogen[i], phosphorus[i], potassium[i]
        area = farm_area[i]

        # Determine Type
        if n < 50 and p > 60:
            fert = "DAP"
            base_q = 50 + (100 - p) * 0.5  # More P deficiency -> more DAP
        elif n > 100 and p < 40 and k < 40:
            fert = "Urea"
            base_q = (
                40 + (n - 100) * 0.3
            )  # More N excess? No, Urea is for N deficiency usually.
            # Correction: Urea for low N
        elif n < 40:  # Better logic for Urea
            fert = "Urea"
            base_q = 60 + (40 - n) * 1.5
        elif k > 70 and n < 60:
            fert = "MOP"
            base_q = 30 + (100 - k) * 0.4
        elif n > 60 and p > 40 and k > 40:
            fert = "NPK 15-15-15"
            base_q = 100 + (200 - (n + p + k)) * 0.2
        else:
            fert = "NPK 10-26-26"
            base_q = 80 + (200 - (n + p + k)) * 0.2

        # Adjust quantity for Growth Stage
        stage_multipliers = {
            "Initial": 0.8,
            "Vegetative": 1.2,
            "Flowering": 1.0,
            "Maturity": 0.5,
        }
        q = base_q * stage_multipliers[growth_stage[i]]

        # Add noise
        q = q * np.random.uniform(0.9, 1.1)

        fertilizer_choice.append(fert)
        quantity_choice.append(round(q, 2))

    data = {
        "Nitrogen": nitrogen,
        "Phosphorus": phosphorus,
        "Potassium": potassium,
        "pH": ph,
        "Moisture": moisture,
        "Temperature": temp,
        "Crop_Type": crop_choice,
        "Growth_Stage": growth_stage,
        "Farm_Area": farm_area,
        "Fertilizer": fertilizer_choice,
        "Quantity": quantity_choice,
    }

    df = pd.DataFrame(data)

    # Introduce some missing values for cleaning demonstration
    for col in ["Nitrogen", "pH", "Moisture"]:
        indices = np.random.choice(
            df.index, size=int(num_samples * 0.05), replace=False
        )
        df.loc[indices, col] = np.nan

    # Introduce some outliers
    df.loc[0, "Nitrogen"] = 999

    return df


if __name__ == "__main__":
    print("Generating synthetic dataset with 10,000 samples...")
    df = generate_synthetic_data(10000)
    df.to_csv("data/raw/agricultural_data.csv", index=False)
    print("Saved to data/raw/agricultural_data.csv")
