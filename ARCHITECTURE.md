# Kisan Smart - System Architecture

## Overview
Kisan Smart follows the **Model-View-Controller (MVC)** architectural pattern to ensure separation of concerns, scalability, and ease of maintenance.

## MVC Decomposition

### 1. Models (`/website/models.py` and `/models/`)
- Represent the data structures and business logic.
- Managed by SQLAlchemy ORM.
- PostgreSQL tables are mapped to Python classes.

### 2. Views (`/website/templates/`)
- The user interface components.
- Implementation: Jinja2 templates (HTML/CSS/JS).
- Responsible for presentation logic only.

### 3. Controllers (`/website/views.py`, `/website/auth.py`)
- Act as intermediaries between Models and Views.
- Implementation: Flask Blueprints.
- Handle incoming HTTP requests, process input, and return responses.

## Folder Structure
```text
kisan-smart/
├── website/             # Main application package
│   ├── auth.py          # Authentication controller
│   ├── decorators.py    # Custom view decorators
│   ├── models.py        # Database models
│   ├── templates/       # HTML view templates
│   ├── views.py         # Main application controller
│   └── __init__.py      # App factory and blueprint registration
├── config/              # Environment configurations
├── controllers/         # Future scaled controllers
├── data/                # Datasets (raw/processed)
├── logs/                # Application runtime logs
├── models/              # Future scaled models
├── static/              # CSS, JS, and Image assets
├── tests/               # Automated tests
├── scripts/             # Data pipelines and ML scripts
├── app.py               # Entry point
├── config.py            # Configuration loader
├── schema.sql           # Database schema
└── requirements.txt     # Python dependencies
```

## Data Flow
1. User interacts with the UI (View).
2. Request is routed to a Flask Blueprint (Controller).
3. Controller interacts with SQLAlchemy classes (Model).
4. Model fetches/updates data in PostgreSQL.
5. Controller passes data back to the Jinja2 template (View) to be rendered.
