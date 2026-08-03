from locust import HttpUser, task, between

class AuthVaultLoadTest(HttpUser):
    """
    Simulates high-throughput traffic against the AuthVault API.
    To run this test locally:
    1. Ensure the FastAPI server is running: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
    2. Run Locust: `locust -f benchmarks/locustfile.py`
    """
    
    # Wait time between tasks for a single user (simulates think time)
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """
        Executed when a simulated user starts.
        We generate a token to use for protected endpoints.
        """
        # In a real benchmark, you would pre-seed the database with this user.
        # For pure throughput testing, we assume a test user exists, or we test the health endpoint.
        self.token = None
        
        # Uncomment to test authentication flow overhead (requires test user in DB)
        # response = self.client.post("/api/v1/auth/login", data={
        #     "username": "test@example.com",
        #     "password": "testpassword123"
        # })
        # if response.status_code == 200:
        #     self.token = response.json().get("access_token")

    @task(3)
    def test_health_endpoint(self):
        """
        Tests the maximum raw throughput of the async API layer.
        """
        self.client.get("/api/v1/health")

    @task(1)
    def test_protected_endpoint(self):
        """
        Tests throughput of endpoints requiring token validation and RBAC checks.
        """
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.get("/api/v1/users/me", headers=headers)
