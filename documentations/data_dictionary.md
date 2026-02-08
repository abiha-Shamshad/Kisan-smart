# Kisan Smart - Data Dictionary

This document describes the features used in the fertilizer recommendation system.

| Feature Name | Description | Data Type | Range/Categories |
| :--- | :--- | :--- | :--- |
| **Nitrogen (N)** | Nitrogen content in the soil (mg/kg) | Integer | 0 - 300 |
| **Phosphorus (P)** | Phosphorus content in the soil (mg/kg) | Integer | 0 - 150 |
| **Potassium (K)** | Potassium content in the soil (mg/kg) | Integer | 0 - 200 |
| **pH** | Level of acidity or alkalinity of the soil | Float | 0.0 - 14.0 |
| **Moisture** | Water content in the soil (%) | Float | 0 - 100 |
| **Temperature** | Ambient temperature (°C) | Float | 10 - 50 |
| **Crop_Type** | The name of the crop being planted | Categorical | Wheat, Rice, Maize, Cotton, Sugarcane, Pulse |
| **Fertilizer** | The recommended fertilizer type (Target) | Categorical | Urea, DAP, NPK 15-15-15, NPK 10-26-26, MOP |
| **Total_Nutrients**| Derived feature: Sum of N, P, and K | Integer | Calculated |

## Notes:
- **Missing Values**: Handled using median imputation for numerical features.
- **Outliers**: Capped using the 1.5 * IQR method primarily for Nitrogen.
- **Scaling**: Robust scaling or Standard scaling is recommended before model training.
