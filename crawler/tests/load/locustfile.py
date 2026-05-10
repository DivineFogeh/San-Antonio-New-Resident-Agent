# crawler/tests/load/locustfile.py
# Load test for SA New Resident Agent
# Usage: locust -f tests/load/locustfile.py --headless --users 20 --spawn-rate 5 --run-time 60s --host http://localhost:8001
# Or via root Makefile: make loadtest

from locust import HttpUser, task, between
import random
import uuid

QUESTIONS = [
    "What are the current CPS Energy residential rates?",
    "What documents do I need to sign up for SAWS?",
    "How do I register with the City of San Antonio as a new resident?",
    "What should I enter for the service address field on the CPS Energy form?",
    "How long does CPS Energy setup take?",
    "What is the average SAWS water bill?",
    "Is there a deposit required for CPS Energy?",
    "Tell me about the SAWS Cares program",
    "What trash pickup days are available?",
    "How do I set up AutoPay for SAWS?",
]

class AgentUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.session_id = str(uuid.uuid4())

    @task(5)
    def chat_question(self):
        """Primary endpoint — Q&A chat (weighted 5x)"""
        self.client.post(
            "/chat",
            json={
                "session_id": self.session_id,
                "message": random.choice(QUESTIONS)
            },
            name="/chat"
        )

    @task(2)
    def simulate_enrollment(self):
        """Guided enrollment simulation"""
        self.client.post(
            "/simulate",
            json={
                "session_id": self.session_id,
                "message": "I want to set up my CPS Energy service"
            },
            name="/simulate"
        )

    @task(2)
    def get_status(self):
        """Session status check"""
        self.client.get(
            f"/status/{self.session_id}",
            name="/status/{session_id}"
        )

    @task(1)
    def health_check(self):
        """Health probe"""
        self.client.get("/health", name="/health")


class BackendUser(HttpUser):
    """Load test against the backend API instead of the crawler directly."""
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self):
        self.session_id = str(uuid.uuid4())
        # Create user session
        resp = self.client.post(
            "/api/user/session",
            json={
                "name": "Load Test User",
                "email": f"loadtest-{self.session_id[:8]}@test.com",
                "address": "123 Main St, San Antonio, TX"
            },
            name="/api/user/session"
        )
        if resp.status_code == 200:
            self.user_id = resp.json().get("id")
        else:
            self.user_id = None

    @task(4)
    def agent_chat(self):
        """Agent chat via backend proxy"""
        self.client.post(
            "/api/services/agent/chat",
            json={
                "session_id": self.session_id,
                "message": random.choice(QUESTIONS)
            },
            name="/api/services/agent/chat"
        )

    @task(2)
    def get_checklist(self):
        """Get checklist progress"""
        if self.user_id:
            self.client.get(
                f"/api/checklist/{self.user_id}",
                name="/api/checklist/{user_id}"
            )

    @task(1)
    def health_check(self):
        self.client.get("/", name="/health")
