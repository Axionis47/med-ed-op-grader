"""
Integration tests for complete grading workflow.

Tests the entire system end-to-end using the Grading Orchestrator.
"""

import pytest
import httpx
import json
from pathlib import Path


# Base URLs
ORCHESTRATOR_URL = "http://localhost:8000"
RUBRIC_URL = "http://localhost:8001"

# Test data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RUBRICS_DIR = DATA_DIR / "rubrics" / "examples"
EXAMPLES_DIR = DATA_DIR / "examples"


@pytest.fixture(scope="module")
def http_client():
    """Create HTTP client for tests."""
    with httpx.Client(timeout=60.0) as client:
        yield client


@pytest.fixture(scope="module")
def ensure_services_healthy(http_client):
    """Ensure all services are healthy before running tests."""
    response = http_client.get(f"{ORCHESTRATOR_URL}/services/status")
    assert response.status_code == 200
    
    status = response.json()
    assert status["all_healthy"], f"Not all services are healthy: {status['services']}"
    
    return status


@pytest.fixture(scope="module")
def stroke_rubric(http_client):
    """Load and create stroke rubric."""
    rubric_path = RUBRICS_DIR / "stroke_v1.json"
    with open(rubric_path) as f:
        rubric_data = json.load(f)
    
    # Create rubric
    response = http_client.post(
        f"{RUBRIC_URL}/rubrics",
        json=rubric_data
    )
    assert response.status_code == 200
    
    return rubric_data


@pytest.fixture(scope="module")
def chest_pain_rubric(http_client):
    """Load and create chest pain rubric."""
    rubric_path = RUBRICS_DIR / "chest_pain_v1.json"
    with open(rubric_path) as f:
        rubric_data = json.load(f)
    
    # Create rubric
    response = http_client.post(
        f"{RUBRIC_URL}/rubrics",
        json=rubric_data
    )
    assert response.status_code == 200
    
    return rubric_data


@pytest.fixture
def stroke_transcript():
    """Load stroke example transcript."""
    transcript_path = EXAMPLES_DIR / "stroke_transcript_001.txt"
    with open(transcript_path) as f:
        return f.read()


@pytest.fixture
def chest_pain_transcript():
    """Load chest pain example transcript."""
    transcript_path = EXAMPLES_DIR / "chest_pain_transcript_001.txt"
    with open(transcript_path) as f:
        return f.read()


class TestServiceHealth:
    """Test service health and availability."""
    
    def test_orchestrator_health(self, http_client):
        """Test orchestrator health endpoint."""
        response = http_client.get(f"{ORCHESTRATOR_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_all_services_status(self, http_client, ensure_services_healthy):
        """Test all services are healthy."""
        status = ensure_services_healthy
        
        expected_services = [
            "rubric_management",
            "transcript_processing",
            "question_matching",
            "structure_evaluator",
            "reasoning_evaluator",
            "summary_evaluator",
            "scoring",
            "feedback_composer"
        ]
        
        for service in expected_services:
            assert service in status["services"]
            assert status["services"][service]["status"] == "healthy", \
                f"Service {service} is not healthy"


class TestStrokeGrading:
    """Test complete grading workflow for stroke presentations."""
    
    def test_grade_stroke_presentation(
        self,
        http_client,
        ensure_services_healthy,
        stroke_rubric,
        stroke_transcript
    ):
        """Test grading a complete stroke presentation."""
        # Grade the presentation
        response = http_client.post(
            f"{ORCHESTRATOR_URL}/grade",
            json={
                "rubric_id": "stroke_v1",
                "transcript_id": "stroke_test_001",
                "raw_text": stroke_transcript
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate response structure
        assert "transcript_id" in result
        assert result["transcript_id"] == "stroke_test_001"
        assert "rubric_id" in result
        assert result["rubric_id"] == "stroke_v1"
        assert "overall_score" in result
        assert "component_scores" in result
        assert "feedback" in result
        
        # Validate score range
        assert 0 <= result["overall_score"] <= 1
        
        # Validate component scores
        components = result["component_scores"]
        assert "structure" in components
        assert "key_questions" in components
        assert "reasoning" in components
        assert "summary" in components
        
        for component, score in components.items():
            assert 0 <= score <= 1, f"Component {component} score out of range: {score}"
        
        return result
    
    def test_stroke_feedback_has_citations(
        self,
        http_client,
        ensure_services_healthy,
        stroke_rubric,
        stroke_transcript
    ):
        """Test that all feedback items have proper citations."""
        response = http_client.post(
            f"{ORCHESTRATOR_URL}/grade",
            json={
                "rubric_id": "stroke_v1",
                "transcript_id": "stroke_test_002",
                "raw_text": stroke_transcript
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        feedback = result["feedback"]
        assert "sections" in feedback
        
        # Check all feedback items have rubric citations
        for section in feedback["sections"]:
            assert "items" in section
            for item in section["items"]:
                assert "citations" in item
                assert "rubric" in item["citations"]
                assert len(item["citations"]["rubric"]) > 0, \
                    f"Feedback item missing rubric citation: {item['text']}"
    
    def test_stroke_deterministic_scoring(
        self,
        http_client,
        ensure_services_healthy,
        stroke_rubric,
        stroke_transcript
    ):
        """Test that scoring is deterministic (same input -> same output)."""
        # Grade the same presentation twice
        request_data = {
            "rubric_id": "stroke_v1",
            "transcript_id": "stroke_test_003",
            "raw_text": stroke_transcript
        }
        
        response1 = http_client.post(f"{ORCHESTRATOR_URL}/grade", json=request_data)
        response2 = http_client.post(f"{ORCHESTRATOR_URL}/grade", json=request_data)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        result1 = response1.json()
        result2 = response2.json()
        
        # Scores should be identical
        assert result1["overall_score"] == result2["overall_score"]
        assert result1["component_scores"] == result2["component_scores"]


class TestChestPainGrading:
    """Test complete grading workflow for chest pain presentations."""
    
    def test_grade_chest_pain_presentation(
        self,
        http_client,
        ensure_services_healthy,
        chest_pain_rubric,
        chest_pain_transcript
    ):
        """Test grading a complete chest pain presentation."""
        response = http_client.post(
            f"{ORCHESTRATOR_URL}/grade",
            json={
                "rubric_id": "chest_pain_v1",
                "transcript_id": "chest_pain_test_001",
                "raw_text": chest_pain_transcript
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate response structure
        assert result["rubric_id"] == "chest_pain_v1"
        assert 0 <= result["overall_score"] <= 1
        
        # Validate component scores
        components = result["component_scores"]
        for component, score in components.items():
            assert 0 <= score <= 1
        
        return result
    
    def test_chest_pain_feedback_citations(
        self,
        http_client,
        ensure_services_healthy,
        chest_pain_rubric,
        chest_pain_transcript
    ):
        """Test chest pain feedback has proper citations."""
        response = http_client.post(
            f"{ORCHESTRATOR_URL}/grade",
            json={
                "rubric_id": "chest_pain_v1",
                "transcript_id": "chest_pain_test_002",
                "raw_text": chest_pain_transcript
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check all feedback items have citations
        for section in result["feedback"]["sections"]:
            for item in section["items"]:
                assert len(item["citations"]["rubric"]) > 0


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_rubric_id(self, http_client, ensure_services_healthy):
        """Test grading with invalid rubric ID."""
        response = http_client.post(
            f"{ORCHESTRATOR_URL}/grade",
            json={
                "rubric_id": "nonexistent_rubric",
                "transcript_id": "test_001",
                "raw_text": "[00:05] Student: Hello"
            }
        )
        
        # Should return error
        assert response.status_code in [404, 500]
    
    def test_empty_transcript(
        self,
        http_client,
        ensure_services_healthy,
        stroke_rubric
    ):
        """Test grading with empty transcript."""
        response = http_client.post(
            f"{ORCHESTRATOR_URL}/grade",
            json={
                "rubric_id": "stroke_v1",
                "transcript_id": "empty_test",
                "raw_text": ""
            }
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

