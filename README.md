# Kisan Smart - AI-Based Fertilizer Recommendation System

Kisan Smart is a comprehensive agricultural decision-support system designed to provide personalized fertilizer recommendations based on soil parameters and crop requirements.

## Features
- **Accurate Recommendations**: Powered by Machine Learning.
- **MVC Architecture**: scalable and maintainable structure.
- **PostgreSQL Integration**: Robust data management.
- **User Management**: Secure authentication for Farmers and Admins.

## Tech Stack
- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **ML**: Scikit-learn, Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript

## Installation Guide

### 1. Prerequisites
- Python 3.8+
- PostgreSQL installed and running

### 2. Setup
```bash
# Clone the repository
git clone <repository-url>
cd kisan-smart

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your database credentials:
```bash
cp .env.example .env
```

### 4. Database Setup
Create a PostgreSQL database named `kisan_smart` and run the `schema.sql`:
```bash
psql -U postgres -d kisan_smart -f schema.sql
```

### 5. Run Application
```bash
python app.py
```

## Project Structure
Follows the Model-View-Controller (MVC) pattern. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.
