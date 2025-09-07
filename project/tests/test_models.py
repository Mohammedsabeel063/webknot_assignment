import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from database import Base, get_db
from main import app

class TestModels:
    def test_college_model(self, dbsession):
        from models import College
        
        # Test creating a college
        college = College(
            college_id="test_college_123",
            name="Test University",
            domain="test.edu"
        )
        dbsession.add(college)
        dbsession.commit()
        
        # Test retrieving the college
        retrieved = dbsession.query(College).filter_by(college_id="test_college_123").first()
        assert retrieved is not None
        assert retrieved.name == "Test University"
        assert retrieved.domain == "test.edu"
    
    def test_student_model(self, dbsession):
        from models import College, Student
        
        # Create a college first
        college = College(college_id="test_college_123", name="Test University")
        dbsession.add(college)
        dbsession.commit()
        
        # Test creating a student
        student = Student(
            student_id="test_student_1",
            college_id=college.college_id,
            name="Test Student",
            email="test@test.edu"
        )
        dbsession.add(student)
        dbsession.commit()
        
        # Test retrieving the student
        retrieved = dbsession.query(Student).filter_by(student_id="test_student_1").first()
        assert retrieved is not None
        assert retrieved.name == "Test Student"
        assert retrieved.college_id == college.college_id
    
    def test_event_model(self, dbsession):
        from models import College, Event
        
        # Create a college
        college = College(college_id="test_college_123", name="Test University")
        dbsession.add(college)
        dbsession.commit()
        
        # Test creating an event
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        event = Event(
            event_id="test_event_1",
            college_id=college.college_id,
            title="Test Event",
            type="workshop",
            start_time=start_time,
            end_time=end_time,
            venue="Test Hall"
        )
        dbsession.add(event)
        dbsession.commit()
        
        # Test retrieving the event
        retrieved = dbsession.query(Event).filter_by(event_id="test_event_1").first()
        assert retrieved is not None
        assert retrieved.title == "Test Event"
        assert retrieved.college_id == college.college_id
        assert retrieved.start_time == start_time
        assert retrieved.end_time == end_time
    
    def test_registration_model(self, dbsession):
        from models import College, Student, Event, Registration
        
        # Setup test data
        college = College(college_id="test_college_123", name="Test University")
        student = Student(
            student_id="test_student_1",
            college_id=college.college_id,
            name="Test Student",
            email="test@test.edu"
        )
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        event = Event(
            event_id="test_event_1",
            college_id=college.college_id,
            title="Test Event",
            start_time=start_time,
            end_time=end_time
        )
        
        dbsession.add_all([college, student, event])
        dbsession.commit()
        
        # Test creating a registration
        registration = Registration(
            reg_id="test_reg_1",
            college_id=college.college_id,
            event_id=event.event_id,
            student_id=student.student_id
        )
        dbsession.add(registration)
        dbsession.commit()
        
        # Test retrieving the registration
        retrieved = dbsession.query(Registration).filter_by(reg_id="test_reg_1").first()
        assert retrieved is not None
        assert retrieved.event_id == event.event_id
        assert retrieved.student_id == student.student_id
        assert retrieved.college_id == college.college_id
    
    def test_attendance_model(self, dbsession):
        from models import College, Student, Event, Attendance
        
        # Setup test data
        college = College(college_id="test_college_123", name="Test University")
        student = Student(
            student_id="test_student_1",
            college_id=college.college_id,
            name="Test Student",
            email="test@test.edu"
        )
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        event = Event(
            event_id="test_event_1",
            college_id=college.college_id,
            title="Test Event",
            start_time=start_time,
            end_time=end_time
        )
        
        dbsession.add_all([college, student, event])
        dbsession.commit()
        
        # Test creating an attendance record
        attendance = Attendance(
            att_id="test_att_1",
            college_id=college.college_id,
            event_id=event.event_id,
            student_id=student.student_id,
            present=True,
            method="manual"
        )
        dbsession.add(attendance)
        dbsession.commit()
        
        # Test retrieving the attendance record
        retrieved = dbsession.query(Attendance).filter_by(att_id="test_att_1").first()
        assert retrieved is not None
        assert retrieved.event_id == event.event_id
        assert retrieved.student_id == student.student_id
        assert retrieved.present is True
        assert retrieved.method == "manual"
