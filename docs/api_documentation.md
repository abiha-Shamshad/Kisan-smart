# Kisan Smart - API Documentation
**Version**: 1.0.0
**Base URL**: `https://kisansmart.com/api/v1`

## Authentication
All protected endpoints require a JWT token in the header:
`Authorization: Bearer <your_token>`

---

## Endpoints

### 1. Authentication

#### POST /auth/register
Register a new user.
- **Body**:
  ```json
  {
    "username": "farmer_joe",
    "email": "joe@farm.com",
    "password": "SecurePassword123"
  }
  ```
- **Response (201)**: `{"message": "User registered successfully"}`

#### POST /auth/login
Login to receive a token.
- **Body**:
  ```json
  {"email": "joe@farm.com", "password": "SecurePassword123"}
  ```
- **Response (200)**:
  ```json
  {
    "token": "eyJhGciOiJIUzI1...",
    "user": {"id": 1, "username": "farmer_joe"}
  }
  ```

---

### 2. Predictions

#### POST /predict (Protected)
Generate a fertilizer recommendation.
- **Body**:
  ```json
  {
    "crop_type": "Wheat",
    "nitrogen": 50,
    "phosphorus": 40,
    "potassium": 20,
    "ph": 6.5,
    "moisture": 30,
    "temperature": 25,
    "humidity": 60
  }
  ```
- **Response (200)**:
  ```json
  {
    "recommendation": "Urea",
    "quantity": "50 kg/acre",
    "confidence": 98.5,
    "viz_data": {...}
  }
  ```

---

### 3. History

#### GET /history (Protected)
Retrieve past predictions.
- **Params**: `page` (int), `limit` (int)
- **Response (200)**:
  ```json
  {
    "data": [
      {
        "id": 101,
        "crop": "Wheat",
        "date": "2023-10-25T14:30:00Z",
        "result": "Urea"
      }
    ],
    "total": 50
  }
  ```

---

## Error Codes
- **400**: Bad Request (Invalid input).
- **401**: Unauthorized (Missing or invalid token).
- **403**: Forbidden (Insufficient permissions).
- **429**: Too Many Requests (Rate limit exceeded).
- **500**: Server Error.
