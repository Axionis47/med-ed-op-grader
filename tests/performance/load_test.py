"""
Load testing script for the grading system.

Uses locust to simulate concurrent users grading presentations.
"""

from locust import HttpUser, task, between
import json
from pathlib import Path


# Load test data
DATA_DIR = Path(__file__).parent.parent.parent / "data"
EXAMPLES_DIR = DATA_DIR / "examples"


class GradingUser(HttpUser):
    """Simulates a user grading presentations."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Load test data when user starts."""
        # Load stroke transcript
        stroke_path = EXAMPLES_DIR / "stroke_transcript_001.txt"
        with open(stroke_path) as f:
            self.stroke_transcript = f.read()
        
        # Load chest pain transcript
        chest_pain_path = EXAMPLES_DIR / "chest_pain_transcript_001.txt"
        with open(chest_pain_path) as f:
            self.chest_pain_transcript = f.read()
    
    @task(3)
    def grade_stroke_presentation(self):
        """Grade a stroke presentation (most common)."""
        self.client.post(
            "/grade",
            json={
                "rubric_id": "stroke_v1",
                "transcript_id": f"load_test_stroke_{self.environment.runner.user_count}",
                "raw_text": self.stroke_transcript
            },
            name="/grade [stroke]"
        )
    
    @task(2)
    def grade_chest_pain_presentation(self):
        """Grade a chest pain presentation."""
        self.client.post(
            "/grade",
            json={
                "rubric_id": "chest_pain_v1",
                "transcript_id": f"load_test_chest_pain_{self.environment.runner.user_count}",
                "raw_text": self.chest_pain_transcript
            },
            name="/grade [chest_pain]"
        )
    
    @task(1)
    def check_service_status(self):
        """Check service status."""
        self.client.get("/services/status", name="/services/status")
    
    @task(1)
    def health_check(self):
        """Health check."""
        self.client.get("/health", name="/health")


if __name__ == "__main__":
    import os
    os.system("locust -f tests/performance/load_test.py --host=http://localhost:8000")

