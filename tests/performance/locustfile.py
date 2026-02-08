"""
Load testing with Locust
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:5000
"""

from locust import HttpUser, task, between
import random


class KisanSmartUser(HttpUser):
    """
    Simulates a typical Kisan Smart user
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """
        Login before starting tasks
        """
        # Register a unique user
        self.username = f"loadtest_user_{random.randint(1000, 9999)}"
        self.password = "LoadTest123!"

        # Register
        self.client.post(
            "/api/v1/auth/register",
            json={
                "username": self.username,
                "email": f"{self.username}@loadtest.com",
                "password": self.password,
            },
        )

        # Login and get token
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
        )

        if response.status_code == 200:
            self.token = response.json()["data"]["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def get_dashboard_stats(self):
        """
        Get dashboard statistics (most common action)
        """
        if self.token:
            with self.client.get(
                "/api/v1/history/stats", headers=self.headers, catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

    @task(2)
    def get_history(self):
        """
        Browse prediction history (common action)
        """
        if self.token:
            page = random.randint(1, 3)
            with self.client.get(
                f"/api/v1/history?page={page}&per_page=20",
                headers=self.headers,
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

    @task(1)
    def make_prediction(self):
        """
        Make a fertilizer prediction (less common but critical)
        """
        if self.token:
            crops = ["wheat", "rice", "maize", "cotton", "sugarcane"]

            prediction_data = {
                "crop_type": random.choice(crops),
                "nitrogen": random.uniform(30, 60),
                "phosphorus": random.uniform(20, 50),
                "potassium": random.uniform(15, 40),
                "ph": random.uniform(5.5, 7.5),
                "moisture": random.uniform(50, 80),
                "temperature": random.uniform(15, 30),
                "farm_area": random.uniform(1, 10),
            }

            with self.client.post(
                "/api/v1/predict",
                json=prediction_data,
                headers=self.headers,
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    # Check response time (should be <3s)
                    if response.elapsed.total_seconds() < 3.0:
                        response.success()
                    else:
                        response.failure(
                            f"Prediction too slow: {response.elapsed.total_seconds()}s"
                        )
                else:
                    response.failure(f"Got status code {response.status_code}")

    @task(1)
    def view_profile(self):
        """
        View user profile
        """
        if self.token:
            with self.client.get(
                "/api/v1/profile", headers=self.headers, catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")


class AdminUser(HttpUser):
    """
    Simulates an admin user with different behavior
    """

    wait_time = between(2, 5)

    def on_start(self):
        """Login as admin"""
        # Admin login
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "AdminPassword123!"},
        )

        if response.status_code == 200:
            self.token = response.json()["data"]["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task
    def view_all_users(self):
        """View all users (admin only)"""
        if self.token:
            self.client.get("/api/v1/admin/users", headers=self.headers)
