# System Architecture

## Overview
Kisan Smart is a web-based application built on the **Flask** microframework, following a **Model-View-Controller (MVC)** pattern. It integrates Machine Learning models for prediction logic.

## Components

### 1. Frontend
- **HTML5/CSS3/Bootstrap 5**: Responsive UI.
- **JavaScript**: Client-side validation, AJAX requests, Charts.js for visualization.
- **Jinja2**: Server-side templating.

### 2. Backend (Flask)
- **Blueprints**: Modular structure (`auth`, `main`, `admin`, `api`).
- **SQLAlchemy (ORM)**: Database abstraction.
- **Pandas/Scikit-Learn**: Data processing and inference.

### 3. Database (MySQL)
- **Users**: Authentication data.
- **Recommendations**: History of predictions.
- **Crops/Fertilizers**: Static reference data.

### 4. Machine Learning
- **Models**: Random Forest (Classifier), Regression models.
- **Pipeline**: Preprocessing (`StandardScaler`, `LabelEncoder`) -> Inference -> Post-processing.
- **Storage**: Serialized `.pkl` files.

## Data Flow
1. **User Input** -> **Frontend Validation** -> **API Request (POST)**.
2. **Backend**:
   - Authenticates User (JWT/Session).
   - Loads ML Model.
   - Preprocesses Data.
   - Generates Prediction.
   - Saves to Database.
3. **Response** -> **Frontend Visualization**.

## Infrastructure
- **Server**: Ubuntu LTS.
- **Web Server**: Nginx (Reverse Proxy) -> Gunicorn (WSGI).
- **Process Control**: Supervisor.
