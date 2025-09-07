import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import Generator

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, api_v1
from database import Base, get_db, engine, SessionLocal
from models import College, Student, Event, Attendance, registrations

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Override the get_db dependency for testing
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine"""
    return engine

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a new database session with a rollback at the end of the test"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Rollback the transaction and close the session
    session.close()
    transaction.rollback()
    connection.close()
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client that uses the override_get_db fixture"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

# Test data fixtures
@pytest.fixture
def test_college():
    return {
        "college_id": "test_college_123",
        "name": "Test University",
        "domain": "testuniv.edu"
    }

@pytest.fixture
def test_student():
    return {
        "name": "John Doe",
        "email": "john.doe@testuniv.edu",
        "roll_no": "STU123"
    }

@pytest.fixture
def test_event():
    now = datetime.utcnow()
    return {
        "title": "Test Event",
        "type": "workshop",
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=2)).isoformat(),
        "venue": "Test Venue",
        "capacity": 100
    }

@pytest.fixture
def sample_college(db: Session, test_college):
    college = College(**test_college)
    db.add(college)
    db.commit()
    db.refresh(college)
    return college

@pytest.fixture
def sample_student(db: Session, sample_college, test_student):
    student = Student(college_id=sample_college.college_id, **test_student)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

@pytest.fixture
def sample_event(db: Session, sample_college, test_event):
    event = Event(college_id=sample_college.college_id, **test_event)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
