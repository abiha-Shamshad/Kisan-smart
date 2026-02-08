# Kisan Smart - Exploratory Data Analysis (EDA) Report

## 1. Feature Distributions
![Feature Distributions](file:///c:/Users/Each%20One%20Teach%20One/Desktop/Kisan%20smart/static/plots/feature_distributions.png)

- **Soil Nutrients (N, P, K)**: Display a wide range of values, indicating diverse soil conditions.
- **pH Level**: Most samples fall within the 5.5 to 8.5 range, consistent with typical agricultural soil.
- **Moisture**: Uniform distribution across the test set, allowing for robust model training across different climatic conditions.

## 2. Correlation Analysis
![Correlation Heatmap](file:///c:/Users/Each%20One%20Teach%20One/Desktop/Kisan%20smart/static/plots/correlation_heatmap.png)

- Low linear correlation between individual nutrients (N, P, K), suggesting they act as independent features.
- Soil moisture and temperature show negligible correlation in this synthetic set, but should be monitored in real-world data.

## 3. Crop Class Balances
![Crop Distribution](file:///c:/Users/Each%20One%20Teach%20One/Desktop/Kisan%20smart/static/plots/crop_distribution.png)

- The dataset is well-balanced across the six major crop types (Wheat, Rice, Maize, Cotton, Sugarcane, Pulse), preventing model bias.

## 4. Key Data Cleaning Insights
- **Missing Values**: 5% of N, pH, and Moisture data was missing (simulated) and successfully imputed using median values.
- **Outliers**: Extreme values in Nitrogen (e.g., 999) were successfully capped using the Interquartile Range (IQR) method.
- **New Feature**: `Total_Nutrients` was engineered to provide a composite view of soil health.
