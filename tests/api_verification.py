import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api/v1"

def test_api():
    print("--- Kisan Smart API Verification ---")
    
    # 1. Health Check
    try:
        res = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {res.status_code} - {res.json()['status']}")
    except:
        print("Server not running. Please start flask first.")
        return

    # 2. Registration
    user_data = {
        "full_name": "API Tester",
        "email": f"tester_{int(time.time())}@example.com",
        "password": "SecurePassword123!"
    }
    res = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Registration: {res.status_code}")
    
    # 3. Login
    login_data = {"email": user_data['email'], "password": user_data['password']}
    res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login: {res.status_code}")
    token = res.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Profile
    res = requests.get(f"{BASE_URL}/profile/", headers=headers)
    print(f"Get Profile: {res.status_code} - {res.json()['data']['full_name']}")

    # 5. Prediction (Logged in)
    predict_data = {
        "nitrogen": 45, "phosphorus": 30, "potassium": 25,
        "ph": 6.5, "moisture": 40, "temperature": 25,
        "crop_type": "Wheat", "growth_stage": "Vegetative", "farm_area": 2.5
    }
    res = requests.post(f"{BASE_URL}/predict/", json=predict_data, headers=headers)
    print(f"Prediction: {res.status_code} - Rec: {res.json()['data']['fertilizer_type']}")

    # 6. History
    res = requests.get(f"{BASE_URL}/history/", headers=headers)
    print(f"History: {res.status_code} - Count: {res.json()['data']['pagination']['total']}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_api()
