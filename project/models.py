from datetime import datetime
from typing import Optional, List
from passlib.context import CryptContext
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    ForeignKey, Float, Text, Table, Enum, JSON
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from enum import Enum as PyEnum
from datetime import datetime

from database import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """
    Represents a system user who can log in and perform administrative actions.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True,
               comment="Unique identifier for the user")
    username = Column(String(50), unique=True, index=True, nullable=False,
                    comment="Unique username for login")
    email = Column(String(100), unique=True, index=True, nullable=False,
                 comment="User's email address")
    hashed_password = Column(String(100), nullable=False,
                          comment="Hashed password")
    full_name = Column(String(100), nullable=True,
                     comment="User's full name")
    is_active = Column(Boolean(), default=True,
                     comment="Whether the user account is active")
    is_superuser = Column(Boolean(), default=False,
                        comment="Whether the user has superuser privileges")
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                      comment="When the user account was created")
    last_login = Column(DateTime(timezone=True), nullable=True,
                      comment="When the user last logged in")
    
    # Relationships
    created_events = relationship("Event", back_populates="creator")
    
    def set_password(self, password: str):
        """Hash and set the user's password."""
        self.hashed_password = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return pwd_context.verify(password, self.hashed_password)
    
    def __repr__(self):
        return f"<User {self.username} ({self.email})>"




class Registration(Base):
    """
    Represents a student's registration for an event.
    This is a junction table between Student and Event with additional attributes.
    """
    __tablename__ = 'registrations'
    
    reg_id = Column(String(50), primary_key=True, index=True,
                   comment="Unique identifier for the registration")
    event_id = Column(String(50), ForeignKey('events.event_id'), 
                     nullable=False, index=True,
                     comment="Reference to the event")
    student_id = Column(String(50), ForeignKey('students.student_id'), 
                       nullable=False, index=True,
                       comment="Reference to the student")
    registration_time = Column(DateTime(timezone=True), server_default=func.now(),
                             comment="When the student registered for the event")
    attended = Column(Boolean, default=False,
                     comment="Whether the student attended the event")
    check_in_time = Column(DateTime(timezone=True), nullable=True,
                          comment="When the student checked in")
    check_out_time = Column(DateTime(timezone=True), nullable=True,
                           comment="When the student checked out")
    
    # Relationships
    event = relationship("Event", back_populates="registrations")
    student = relationship("Student", back_populates="registrations")
    
    def __repr__(self):
        return f"<Registration(reg_id='{self.reg_id}', event_id='{self.event_id}', student_id='{self.student_id}')>"


class College(Base):
    """
    Represents an educational institution that uses the platform.
    Each college has its own isolated data including students, events, etc.
    """
    __tablename__ = 'colleges'
    
    college_id = Column(String(50), primary_key=True, index=True, 
                      comment="Unique identifier for the college")
    name = Column(String(100), nullable=False, 
                comment="Full name of the college")
    domain = Column(String(100), unique=True, nullable=True,
                  comment="Email domain used for student verification")
    address = Column(Text, nullable=True, 
                   comment="Physical address of the college")
    contact_email = Column(String(100), nullable=True,
                        comment="Primary contact email")
    contact_phone = Column(String(20), nullable=True,
                        comment="Primary contact phone number")
    logo_url = Column(String(255), nullable=True,
                    comment="URL to the college's logo")
    is_active = Column(Boolean, default=True,
                     comment="Whether the college account is active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                      comment="When the college was registered in the system")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(),
                      comment="When the college record was last updated")
    
    # Relationships
    students = relationship("Student", back_populates="college", 
                          cascade="all, delete-orphan")
    events = relationship("Event", back_populates="college",
                        cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<College {self.name} ({self.college_id})>"

class Student(Base):
    """
    Represents a student who can register for and attend events.
    Each student belongs to a specific college.
    """
    __tablename__ = 'students'
    
    student_id = Column(String(50), primary_key=True, index=True,
                      comment="Unique identifier for the student")
    college_id = Column(String(50), ForeignKey('colleges.college_id'), 
                      nullable=False, index=True,
                      comment="Reference to the student's college")
    name = Column(String(100), nullable=False,
                comment="Full name of the student")
    email = Column(String(100), nullable=False, unique=True,
                 comment="Student's email address (must be unique)")
    roll_no = Column(String(50), unique=True, nullable=True,
                   comment="Student's roll number (unique within college)")
    phone = Column(String(20), nullable=True,
                 comment="Student's contact number")
    department = Column(String(50), nullable=True,
                      comment="Student's department or major")
    batch_year = Column(Integer, nullable=True,
                      comment="Student's admission/graduation year")
    is_active = Column(Boolean, default=True,
                     comment="Whether the student account is active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                      comment="When the student was registered")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(),
                      comment="When the student record was last updated")
    
    # Relationships
    college = relationship("College", back_populates="students")
    registrations = relationship("Registration", back_populates="student",
                                  cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student",
                            cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="student",
                           cascade="all, delete-orphan")
    
    # Validation
    @validates('email')
    def validate_email(self, key, email):
        if not email or '@' not in email:
            raise ValueError("Invalid email address")
        return email.lower()
    
    def __repr__(self):
        return f"<Student {self.name} ({self.student_id})>"

class EventType(str, PyEnum):
    """Enumeration of possible event types"""
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    CONFERENCE = "conference"
    HACKATHON = "hackathon"
    WEBINAR = "webinar"
    MEETUP = "meetup"
    OTHER = "other"

class EventStatus(str, PyEnum):
    """Enumeration of possible event statuses"""
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Event(Base):
    """
    Represents an event that students can register for and attend.
    Each event belongs to a specific college.
    """
    __tablename__ = 'events'
    
    event_id = Column(String(50), primary_key=True, index=True,
                    comment="Unique identifier for the event")
    college_id = Column(String(50), ForeignKey('colleges.college_id'), 
                      nullable=False, index=True,
                      comment="Reference to the organizing college")
    title = Column(String(200), nullable=False,
                 comment="Title of the event")
    slug = Column(String(220), unique=True, nullable=True,
                comment="URL-friendly version of the title")
    description = Column(Text, nullable=True,
                      comment="Detailed description of the event")
    type = Column(String(50), nullable=False, default=EventType.OTHER.value,
                comment="Type/category of the event")
    start_time = Column(DateTime(timezone=True), nullable=False,
                      comment="Scheduled start time of the event")
    end_time = Column(DateTime(timezone=True), nullable=False,
                    comment="Scheduled end time of the event")
    venue = Column(String(200), nullable=True,
                 comment="Physical location of the event")
    capacity = Column(Integer, nullable=True,
                    comment="Maximum number of attendees (NULL for unlimited)")
    image_url = Column(String(255), nullable=True,
                     comment="URL to event banner/image")
    registration_deadline = Column(DateTime(timezone=True), nullable=True,
                                 comment="Last date to register for the event")
    is_published = Column(Boolean, default=False,
                        comment="Whether the event is visible to students")
    status = Column(String(20), default=EventStatus.DRAFT.value,
                  comment="Current status of the event")
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True,
                     comment="Reference to the user who created the event")
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                      comment="When the event was created")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(),
                      comment="When the event was last updated")
    
    # Relationships
    college = relationship("College", back_populates="events")
    creator = relationship("User", back_populates="created_events")
    registrations = relationship("Registration", back_populates="event",
                                  cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="event",
                            cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="event",
                           cascade="all, delete-orphan")
    
    # Validation
    @validates('end_time')
    def validate_end_time(self, key, end_time):
        if hasattr(self, 'start_time') and end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return end_time
    
    @validates('registration_deadline')
    def validate_registration_deadline(self, key, deadline):
        if deadline and hasattr(self, 'start_time') and deadline > self.start_time:
            raise ValueError("Registration deadline must be before event start time")
        return deadline
    
    @property
    def is_upcoming(self) -> bool:
        """Check if the event is upcoming"""
        now = datetime.now(self.start_time.tzinfo)
        return self.start_time > now
    
    @property
    def is_ongoing(self) -> bool:
        """Check if the event is currently ongoing"""
        now = datetime.now(self.start_time.tzinfo)
        return self.start_time <= now <= self.end_time
    
    @property
    def is_past(self) -> bool:
        """Check if the event has already ended"""
        now = datetime.now(self.end_time.tzinfo)
        return self.end_time < now
    
    @property
    def registration_count(self) -> int:
        """Get the number of registrations for this event"""
        return len(self.registrations)
    
    @property
    def attendance_count(self) -> int:
        """Get the number of attendees for this event"""
        return len([a for a in self.attendances if a.present])
    
    @property
    def is_full(self) -> bool:
        """Check if the event has reached its capacity"""
        if self.capacity is None:
            return False
        return self.registration_count >= self.capacity
    
    def __repr__(self):
        return f"<Event {self.title} ({self.event_id})>"

class Feedback(Base):
    """
    Represents feedback provided by a student for an event.
    """
    __tablename__ = 'feedbacks'
    
    feedback_id = Column(String(50), primary_key=True, index=True,
                      comment="Unique identifier for the feedback")
    event_id = Column(String(50), ForeignKey('events.event_id'), 
                    nullable=False, index=True,
                    comment="Reference to the event")
    student_id = Column(String(50), ForeignKey('students.student_id'), 
                      nullable=False, index=True,
                      comment="Reference to the student")
    rating = Column(Integer, nullable=False,
                  comment="Rating given by the student (e.g., 1-5 stars)")
    comment = Column(Text, nullable=True,
                   comment="Detailed feedback comment")
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(),
                        comment="When the feedback was submitted")
    is_anonymous = Column(Boolean, default=False,
                        comment="Whether the feedback is anonymous")
    
    # Relationships
    event = relationship("Event", back_populates="feedbacks")
    student = relationship("Student", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<Feedback {self.feedback_id} for Event {self.event_id}>"


class CheckInMethod(str, PyEnum):
    """Enumeration of possible check-in methods"""
    QR_CODE = "qr_code"
    MANUAL = "manual"
    NFC = "nfc"
    FACE_RECOGNITION = "face_recognition"
    EMAIL = "email"
    OTHER = "other"

class Attendance(Base):
    """
    Tracks student attendance at events.
    Separate from registration to handle cases where attendance is taken
    without prior registration.
    """
    __tablename__ = 'attendance'
    
    attendance_id = Column(String(50), primary_key=True, index=True,
                        comment="Unique identifier for the attendance record")
    event_id = Column(String(50), ForeignKey('events.event_id'), 
                    nullable=False, index=True,
                    comment="Reference to the event")
    student_id = Column(String(50), ForeignKey('students.student_id'), 
                      nullable=False, index=True,
                      comment="Reference to the student")
    present = Column(Boolean, default=False, nullable=False,
                   comment="Whether the student was present")
    check_in_time = Column(DateTime(timezone=True), server_default=func.now(),
                         comment="When the student checked in")
    check_out_time = Column(DateTime(timezone=True), nullable=True,
                          comment="When the student checked out")
    method = Column(String(50), nullable=True,
                  comment=f"Method used for check-in ({', '.join([m.value for m in CheckInMethod])})")
    verified_by = Column(String(100), nullable=True,
                      comment="User who verified the attendance")
    notes = Column(Text, nullable=True,
                 comment="Any additional notes about the attendance")
    
    # Relationships
    event = relationship("Event", back_populates="attendances")
    student = relationship("Student", back_populates="attendances")
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate the duration the student spent at the event in minutes"""
        if self.check_in_time and self.check_out_time:
            return (self.check_out_time - self.check_in_time).total_seconds() / 60
        return None
    
    def __repr__(self):
        status = "present" if self.present else "absent"
        return f"<Attendance {self.student_id} @ {self.event_id}: {status}>"
