import pytest
from fastapi import status

# Test data
TEST_COLLEGE_ID = "test_college_123"

class TestCollegeAPI:
    def test_create_college(self, client, test_college):
        response = client.post(
            "/api/v1/colleges/",
            json=test_college,
            headers={"X-College-ID": test_college["college_id"]}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["college_id"] == test_college["college_id"]
        assert data["name"] == test_college["name"]

class TestStudentAPI:
    def test_create_student(self, client, test_college, test_student):
        # First create a college
        client.post("/api/v1/colleges/", json=test_college)
        
        # Then create a student
        response = client.post(
            "/api/v1/students/",
            json=test_student,
            headers={"X-College-ID": test_college["college_id"]}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == test_student["name"]
        assert data["email"] == test_student["email"]
        assert "student_id" in data

class TestEventAPI:
    def test_create_event(self, client, test_college, test_event):
        # First create a college
        client.post("/api/v1/colleges/", json=test_college)
        
        # Then create an event
        response = client.post(
            "/api/v1/events/",
            json=test_event,
            headers={"X-College-ID": test_college["college_id"]}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == test_event["title"]
        assert data["type"] == test_event["type"]
        assert "event_id" in data

class TestRegistrationAPI:
    def test_register_student_for_event(self, client, test_college, test_student, test_event):
        # Setup: Create college, student, and event
        client.post("/api/v1/colleges/", json=test_college)
        
        student_resp = client.post(
            "/api/v1/students/",
            json=test_student,
            headers={"X-College-ID": test_college["college_id"]}
        )
        student_id = student_resp.json()["student_id"]
        
        event_resp = client.post(
            "/api/v1/events/",
            json=test_event,
            headers={"X-College-ID": test_college["college_id"]}
        )
        event_id = event_resp.json()["event_id"]
        
        # Test registration
        response = client.post(
            "/api/v1/registrations/",
            json={"event_id": event_id, "student_id": student_id},
            headers={"X-College-ID": test_college["college_id"]}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["event_id"] == event_id
        assert data["student_id"] == student_id

class TestAttendanceAPI:
    def test_mark_attendance(self, client, test_college, test_student, test_event):
        # Setup
        client.post("/api/v1/colleges/", json=test_college)
        
        student_resp = client.post(
            "/api/v1/students/",
            json=test_student,
            headers={"X-College-ID": test_college["college_id"]}
        )
        student_id = student_resp.json()["student_id"]
        
        event_resp = client.post(
            "/api/v1/events/",
            json=test_event,
            headers={"X-College-ID": test_college["college_id"]}
        )
        event_id = event_resp.json()["event_id"]
        
        # Test attendance
        response = client.post(
            "/api/v1/attendance/",
            json={
                "event_id": event_id,
                "student_id": student_id,
                "present": True,
                "method": "manual"
            },
            headers={"X-College-ID": test_college["college_id"]}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["event_id"] == event_id
        assert data["student_id"] == student_id
        assert data["present"] is True

class TestReportsAPI:
    def test_event_popularity(self, client, test_college, test_event):
        # Setup
        client.post("/api/v1/colleges/", json=test_college)
        
        # Create an event
        event_resp = client.post(
            "/api/v1/events/",
            json=test_event,
            headers={"X-College-ID": test_college["college_id"]}
        )
        
        # Test report
        response = client.get(
            "/api/v1/reports/event-popularity",
            headers={"X-College-ID": test_college["college_id"]}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
    def test_top_active_students(self, client, test_college):
        response = client.get(
            "/api/v1/reports/top-active-students",
            headers={"X-College-ID": test_college["college_id"]}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
