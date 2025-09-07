import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Import models to ensure they're registered with SQLAlchemy
from models import Base, College, Student, Event, Attendance, Registration
from database import engine, SessionLocal

def init_db():
    """Initialize the database with schema and sample data"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Add sample college
        college = College(
            college_id='test_college_123',
            name='Test University',
            domain='testuniv.edu'
        )
        db.add(college)
        
        # Add sample students
        students = [
            {
                'student_id': f'STU{str(i).zfill(3)}',
                'name': f'Student {i}',
                'email': f'student{i}@testuniv.edu',
                'roll_no': f'R{str(i).zfill(5)}',
                'college_id': 'test_college_123'
            } for i in range(1, 21)  # 20 sample students
        ]
        
        for student_data in students:
            db.add(Student(**student_data))
        
        # Add sample events
        event_types = ['workshop', 'seminar', 'conference', 'hackathon', 'webinar']
        venues = ['Main Hall', 'Auditorium', 'Room 101', 'Online', 'Lab 3']
        
        events = []
        for i in range(1, 11):  # 10 sample events
            start_time = datetime.utcnow() + timedelta(days=random.randint(1, 30))
            end_time = start_time + timedelta(hours=random.randint(1, 4))
            
            event = Event(
                event_id=f'EVT{str(i).zfill(3)}',
                college_id='test_college_123',
                title=f'Event {i}: {random.choice(event_types).title()}',
                type=random.choice(event_types),
                start_time=start_time,
                end_time=end_time,
                venue=random.choice(venues),
                capacity=random.choice([50, 100, 150, 200]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            events.append(event)
            db.add(event)
        
        # Commit to get the event IDs
        db.commit()
        
        # Add registrations and attendance
        all_students = db.query(Student).all()
        
        for event in events:
            # Register random students (50-100% of students)
            num_registrations = random.randint(len(all_students) // 2, len(all_students))
            registered_students = random.sample(all_students, num_registrations)
            
            for student in registered_students:
                # Create registration
                reg = Registration(
                    reg_id=f'REG{len(registered_students)}_{event.event_id[-3:]}_{student.student_id[-3:]}',
                    event_id=event.event_id,
                    student_id=student.student_id,
                    registration_time=datetime.utcnow() - timedelta(days=random.randint(1, 7))
                )
                db.add(reg)
                
                # Mark attendance (randomly 70-100% of registered students attend)
                if random.random() < 0.7:
                    attendance = Attendance(
                        att_id=f'ATT{event.event_id[-3:]}_{student.student_id[-3:]}',
                        college_id=college.college_id,
                        event_id=event.event_id,
                        student_id=student.student_id,
                        present=True,
                        check_in_time=event.start_time + timedelta(minutes=random.randint(-15, 30)),
                        method=random.choice(['qr_code', 'manual', 'nfc'])
                    )
                    db.add(attendance)
        
        db.commit()
        print("✅ Database initialized with sample data")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        db.close()

def reset_db():
    """Drop and recreate all tables"""
    Base.metadata.drop_all(bind=engine)
    print("✅ Dropped all tables")
    init_db()

if __name__ == "__main__":
    print("Initializing database...")
    reset_db()
    print("✅ Database initialization complete!")
