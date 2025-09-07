import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from models import Base, College, Student, Event, Registration, Attendance, Feedback
from schemas import EventType, AttendanceMethod, FeedbackRating
import random

def create_test_data():
    """Create test data in the database"""
    db = SessionLocal()
    
    try:
        # Create colleges
        colleges = [
            College(
                college_id=f"college_{i}",
                name=f"Test University {i}",
                domain=f"test{i}.edu",
                address=f"{i} Test St, Test City"
            ) for i in range(1, 4)
        ]
        db.add_all(colleges)
        db.commit()
        
        # Create students (20 per college)
        students = []
        for college in colleges:
            for i in range(1, 21):
                students.append(Student(
                    student_id=f"{college.college_id}_stu_{i:03d}",
                    college_id=college.college_id,
                    name=f"Student {i} {college.name}",
                    email=f"student{i}@{college.domain}",
                    roll_no=f"STU{i:03d}",
                    department=f"Dept {i%5 + 1}",
                    year_of_study=(i % 4) + 1
                ))
        db.add_all(students)
        db.commit()
        
        # Create events (5 per college)
        event_types = list(EventType)
        events = []
        for college in colleges:
            for i in range(1, 6):
                start_time = datetime.utcnow() + timedelta(days=i*2)
                events.append(Event(
                    event_id=f"{college.college_id}_event_{i}",
                    college_id=college.college_id,
                    title=f"{event_types[i%len(event_types)].value} Event {i}",
                    description=f"Description for event {i}",
                    type=event_types[i%len(event_types)],
                    start_time=start_time,
                    end_time=start_time + timedelta(hours=2),
                    venue=f"Venue {i}",
                    capacity=random.randint(30, 100),
                    status="upcoming"
                ))
        db.add_all(events)
        db.commit()
        
        # Create registrations and attendance (random)
        registrations = []
        attendances = []
        feedbacks = []
        
        for event in events:
            college_students = [s for s in students if s.college_id == event.college_id]
            registered_students = random.sample(college_students, min(20, len(college_students)))
            
            for student in registered_students:
                # Register student for event
                reg = Registration(
                    registration_id=f"reg_{event.event_id}_{student.student_id}",
                    event_id=event.event_id,
                    student_id=student.student_id,
                    registration_time=datetime.utcnow() - timedelta(days=random.randint(1, 5))
                )
                registrations.append(reg)
                
                # Randomly mark attendance (70% chance)
                if random.random() < 0.7:
                    attendances.append(Attendance(
                        attendance_id=f"att_{event.event_id}_{student.student_id}",
                        event_id=event.event_id,
                        student_id=student.student_id,
                        present=True,
                        check_in_time=event.start_time + timedelta(minutes=random.randint(-15, 15)),
                        method=random.choice(list(AttendanceMethod)),
                        notes=""
                    ))
                    
                    # Randomly add feedback (50% of attended)
                    if random.random() < 0.5:
                        feedbacks.append(Feedback(
                            feedback_id=f"fb_{event.event_id}_{student.student_id}",
                            event_id=event.event_id,
                            student_id=student.student_id,
                            rating=random.choice(list(FeedbackRating)),
                            comment=f"Feedback from {student.name} for {event.title}",
                            submission_time=event.start_time + timedelta(hours=2)
                        ))
        
        db.add_all(registrations)
        db.add_all(attendances)
        db.add_all(feedbacks)
        db.commit()
        
        print(f"Created test data: {len(colleges)} colleges, {len(students)} students, "
              f"{len(events)} events, {len(registrations)} registrations, "
              f"{len(attendances)} attendance records, {len(feedbacks)} feedbacks")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating test data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Generate test data
    create_test_data()
