import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

class TestQueries:
    def test_get_events_by_college(self, dbsession):
        from models import College, Event
        from queries import get_events_by_college
        
        # Setup test data
        college1 = College(college_id="college_1", name="College 1")
        college2 = College(college_id="college_2", name="College 2")
        
        now = datetime.utcnow()
        
        # Add events for college 1
        event1 = Event(
            event_id="event_1",
            college_id=college1.college_id,
            title="Event 1",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2)
        )
        
        event2 = Event(
            event_id="event_2",
            college_id=college1.college_id,
            title="Event 2",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=2)
        )
        
        # Add event for college 2
        event3 = Event(
            event_id="event_3",
            college_id=college2.college_id,
            title="Event 3",
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=3, hours=2)
        )
        
        dbsession.add_all([college1, college2, event1, event2, event3])
        dbsession.commit()
        
        # Test getting events for college 1
        events = get_events_by_college(dbsession, college1.college_id)
        assert len(events) == 2
        assert {e.event_id for e in events} == {"event_1", "event_2"}
        
        # Test getting events for college 2
        events = get_events_by_college(dbsession, college2.college_id)
        assert len(events) == 1
        assert events[0].event_id == "event_3"
    
    def test_get_student_registrations(self, dbsession):
        from models import College, Student, Event, Registration
        from queries import get_student_registrations
        
        # Setup test data
        college = College(college_id="test_college", name="Test University")
        
        student1 = Student(
            student_id="student_1",
            college_id=college.college_id,
            name="Student 1",
            email="student1@test.edu"
        )
        
        student2 = Student(
            student_id="student_2",
            college_id=college.college_id,
            name="Student 2",
            email="student2@test.edu"
        )
        
        now = datetime.utcnow()
        
        event1 = Event(
            event_id="event_1",
            college_id=college.college_id,
            title="Event 1",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2)
        )
        
        event2 = Event(
            event_id="event_2",
            college_id=college.college_id,
            title="Event 2",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=2)
        )
        
        # Student 1 registers for both events
        reg1 = Registration(
            reg_id="reg_1",
            college_id=college.college_id,
            event_id=event1.event_id,
            student_id=student1.student_id
        )
        
        reg2 = Registration(
            reg_id="reg_2",
            college_id=college.college_id,
            event_id=event2.event_id,
            student_id=student1.student_id
        )
        
        # Student 2 registers for one event
        reg3 = Registration(
            reg_id="reg_3",
            college_id=college.college_id,
            event_id=event1.event_id,
            student_id=student2.student_id
        )
        
        dbsession.add_all([
            college, student1, student2, event1, event2, reg1, reg2, reg3
        ])
        dbsession.commit()
        
        # Test getting registrations for student 1
        registrations = get_student_registrations(dbsession, student1.student_id)
        assert len(registrations) == 2
        assert {r.event_id for r in registrations} == {"event_1", "event_2"}
        
        # Test getting registrations for student 2
        registrations = get_student_registrations(dbsession, student2.student_id)
        assert len(registrations) == 1
        assert registrations[0].event_id == "event_1"
    
    def test_get_event_attendance(self, dbsession):
        from models import College, Student, Event, Attendance
        from queries import get_event_attendance
        
        # Setup test data
        college = College(college_id="test_college", name="Test University")
        
        student1 = Student(
            student_id="student_1",
            college_id=college.college_id,
            name="Student 1",
            email="student1@test.edu"
        )
        
        student2 = Student(
            student_id="student_2",
            college_id=college.college_id,
            name="Student 2",
            email="student2@test.edu"
        )
        
        now = datetime.utcnow()
        
        event1 = Event(
            event_id="event_1",
            college_id=college.college_id,
            title="Event 1",
            start_time=now - timedelta(days=1),  # Past event
            end_time=now - timedelta(days=1) + timedelta(hours=2)
        )
        
        event2 = Event(
            event_id="event_2",
            college_id=college.college_id,
            title="Event 2",
            start_time=now + timedelta(days=1),  # Future event
            end_time=now + timedelta(days=1, hours=2)
        )
        
        # Student 1 attended event 1
        att1 = Attendance(
            att_id="att_1",
            college_id=college.college_id,
            event_id=event1.event_id,
            student_id=student1.student_id,
            present=True,
            method="qr_code"
        )
        
        # Student 2 was absent from event 1
        att2 = Attendance(
            att_id="att_2",
            college_id=college.college_id,
            event_id=event1.event_id,
            student_id=student2.student_id,
            present=False,
            method="manual"
        )
        
        dbsession.add_all([
            college, student1, student2, event1, event2, att1, att2
        ])
        dbsession.commit()
        
        # Test getting attendance for event 1
        attendance = get_event_attendance(dbsession, event1.event_id)
        assert len(attendance) == 2
        
        # Check attendance records
        present = [a for a in attendance if a.present]
        absent = [a for a in attendance if not a.present]
        
        assert len(present) == 1
        assert present[0].student_id == student1.student_id
        
        assert len(absent) == 1
        assert absent[0].student_id == student2.student_id
        
        # Test getting attendance for event 2 (no attendance records)
        attendance = get_event_attendance(dbsession, event2.event_id)
        assert len(attendance) == 0
