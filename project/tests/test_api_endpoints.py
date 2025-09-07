import pytest
from fastapi.testclient import TestClient
from main_clean import app
from database import init_db, get_db
import sqlite3
import os

# Test client
client = TestClient(app)

# Test database setup
TEST_DB = "test_events.db"

def setup_module(module):
    """Setup test database"""
    # Initialize test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Override the database path for testing
    app.dependency_overrides[get_db] = lambda: sqlite3.connect(TEST_DB)
    init_db()

def teardown_module(module):
    """Cleanup test database"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# Test data
TEST_COLLEGE = {
    "college_id": "test_college_1",
    "name": "Test University",
    "domain": "test.edu"
}

TEST_STUDENT = {
    "name": "John Doe",
    "email": "john.doe@test.edu",
    "roll_no": "STU001"
}

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_college():
    """Test college creation"""
    response = client.post(
        "/api/v1/colleges",
        json=TEST_COLLEGE,
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 201
    assert response.json()["college_id"] == TEST_COLLEGE["college_id"]

def test_create_student():
    """Test student creation"""
    response = client.post(
        "/api/v1/students",
        json=TEST_STUDENT,
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 201
    assert "student_id" in response.json()
    return response.json()["student_id"]

def test_create_event():
    """Test event creation"""
    event_data = {
        "title": "Test Event",
        "type": "workshop",
        "start_time": "2025-10-01T10:00:00",
        "end_time": "2025-10-01T12:00:00",
        "venue": "Test Hall",
        "capacity": 100
    }
    response = client.post(
        "/api/v1/events",
        json=event_data,
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 200
    assert "event_id" in response.json()
    return response.json()["event_id"]

def test_event_registration(student_id, event_id):
    """Test event registration"""
    response = client.post(
        "/api/v1/registrations",
        json={"event_id": event_id, "student_id": student_id},
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 200
    assert "reg_id" in response.json()

def test_mark_attendance(student_id, event_id):
    """Test attendance marking"""
    response = client.post(
        "/api/v1/attendance",
        json={
            "event_id": event_id,
            "student_id": student_id,
            "present": True,
            "method": "qr_code"
        },
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 200
    assert "att_id" in response.json()

def test_submit_feedback(student_id, event_id):
    """Test feedback submission"""
    response = client.post(
        "/api/v1/feedback",
        json={
            "event_id": event_id,
            "student_id": student_id,
            "rating": 5,
            "comment": "Great event!"
        },
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 200
    assert "message" in response.json()

def test_get_reports(event_id):
    """Test report generation"""
    # Test event popularity report
    response = client.get(
        "/api/v1/reports/events/popularity",
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test attendance summary
    response = client.get(
        f"/api/v1/reports/attendance/summary/{event_id}",
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 200
    
    # Test student participation
    response = client.get(
        "/api/v1/reports/students/participation",
        headers={"x-college-id": TEST_COLLEGE["college_id"]}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Run tests with: pytest tests/test_api_endpoints.py -v
