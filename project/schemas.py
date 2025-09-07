from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from enum import Enum

# Enums for type safety
class EventType(str, Enum):
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    CONFERENCE = "conference"
    HACKATHON = "hackathon"
    WEBINAR = "webinar"
    MEETUP = "meetup"
    OTHER = "other"

class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class CheckInMethod(str, Enum):
    QR_CODE = "qr_code"
    MANUAL = "manual"
    NFC = "nfc"
    FACE_RECOGNITION = "face_recognition"
    EMAIL = "email"
    OTHER = "other"

# Base schemas
class CollegeBase(BaseModel):
    college_id: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    name: str = Field(..., min_length=3, max_length=100)
    domain: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[HttpUrl] = None

class CollegeCreate(CollegeBase):
    pass

class CollegeUpdate(CollegeBase):
    name: Optional[str] = Field(None, min_length=3, max_length=100)

class CollegeResponse(CollegeBase):
    college_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Student schemas
class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    roll_no: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    department: Optional[str] = None
    batch_year: Optional[int] = Field(None, ge=2000, le=2100)

class StudentCreate(StudentBase):
    college_id: str

class StudentUpdate(StudentBase):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class StudentResponse(StudentBase):
    student_id: str
    college_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Event schemas
class EventBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    type: EventType = EventType.OTHER
    start_time: datetime
    end_time: datetime
    venue: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0)
    image_url: Optional[HttpUrl] = None
    registration_deadline: Optional[datetime] = None
    is_published: bool = False

    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('registration_deadline')
    def registration_before_start(cls, v, values):
        if v and 'start_time' in values and v > values['start_time']:
            raise ValueError('Registration deadline must be before event start time')
        return v

class EventCreate(EventBase):
    college_id: str

class EventUpdate(EventBase):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    type: Optional[EventType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[EventStatus] = None

class EventResponse(EventBase):
    event_id: str
    college_id: str
    status: EventStatus
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    registration_count: int = 0
    attendance_count: int = 0

    class Config:
        orm_mode = True

# Registration schemas
class RegistrationBase(BaseModel):
    event_id: str
    student_id: str

class RegistrationCreate(RegistrationBase):
    pass

class RegistrationResponse(RegistrationBase):
    registration_id: str
    registered_at: datetime
    attended: Optional[bool] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None

    class Config:
        orm_mode = True

# Attendance schemas
class AttendanceBase(BaseModel):
    event_id: str
    student_id: str
    present: bool = True
    method: Optional[CheckInMethod] = None
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    attendance_id: str
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    verified_by: Optional[str] = None

    class Config:
        orm_mode = True

# Feedback schemas
class FeedbackBase(BaseModel):
    event_id: str
    student_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    anonymous: bool = False
    would_recommend: Optional[bool] = None
    topics_covered_rating: Optional[int] = Field(None, ge=1, le=5)
    presenter_rating: Optional[int] = Field(None, ge=1, le=5)
    venue_rating: Optional[int] = Field(None, ge=1, le=5)

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackResponse(FeedbackBase):
    feedback_id: str
    submitted_at: datetime

    class Config:
        orm_mode = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    scopes: List[str] = []

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserInDB(UserBase):
    hashed_password: str

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

# Generic response models
class Message(BaseModel):
    detail: str

class HTTPError(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Error message"}
        }

# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
