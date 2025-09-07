import os
import logging
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends, Query, Header, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, EmailStr, field_validator, model_validator, ConfigDict
from datetime import datetime
import database as dbmod
import queries

# Import API router
from api_clean import api_v1

# Import database initialization
from database import init_db, get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API router is imported from api_clean

@api_v1.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {
        "status": "ok",
        "message": "API is running",
        "timestamp": datetime.now().isoformat()
    }

@api_v1.post("/colleges/", status_code=201)
async def create_college(college: dict):
    return {"message": "College created successfully", "college": college}

@api_v1.get("/colleges/")
async def list_colleges():
    return {"colleges": []}

# Configure static files and templates
app = FastAPI(
    title='Campus Event Reporting API',
    version='1.0.0',
    description='A comprehensive API for managing campus events and student participation',
    docs_url='/api/v1/docs',
    openapi_url='/api/v1/openapi.json',
    redoc_url='/api/v1/redoc'
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_v1)

# Serve dashboard page
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Check if dashboard.html exists
    if not os.path.exists("templates/dashboard.html"):
        return JSONResponse(
            status_code=404,
            content={"error": "Dashboard template not found. Please ensure dashboard.html exists in the templates directory."}
        )
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize database on startup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    logger.info("Application startup: Database initialized")
    yield
    # Shutdown
    logger.info("Application shutdown")

# Create FastAPI app with lifespan
app = FastAPI(
    title='Campus Event Reporting API',
    version='1.0.0',
    description='A comprehensive API for managing campus events and student participation',
    docs_url='/api/v1/docs',
    openapi_url='/api/v1/openapi.json',
    redoc_url='/api/v1/redoc',
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_v1)

@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint that returns API information"""
    return {
        "message": "Welcome to Campus Event Reporting API",
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc",
        "openapi": "/api/v1/openapi.json"
    }

@app.get("/api/v1/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page with events and statistics"""
    try:
        # Get college ID from query params or use default
        college_id = request.query_params.get("college_id", "default_college")
        
        # Get events for the dashboard
        events = []
        try:
            with dbmod.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT event_id, title, description, start_time, end_time, venue, capacity, 
                           (SELECT COUNT(*) FROM registrations WHERE event_id = events.event_id) as registrations_count
                    FROM events 
                    WHERE college_id = ? 
                    ORDER BY start_time DESC
                    LIMIT 10
                """, (college_id,))
                events = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching events: {str(e)}")
            events = []
        
        # Get stats for the dashboard
        stats = {
            "total_events": 0,
            "total_students": 0,
            "upcoming_events": 0,
            "attendance_rate": 0
        }
        
        try:
            with dbmod.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Total events
                cursor.execute("SELECT COUNT(*) FROM events WHERE college_id = ?", (college_id,))
                stats["total_events"] = cursor.fetchone()[0] or 0
                
                # Total students
                cursor.execute("SELECT COUNT(*) FROM students WHERE college_id = ?", (college_id,))
                stats["total_students"] = cursor.fetchone()[0] or 0
                
                # Upcoming events (next 7 days)
                cursor.execute("""
                    SELECT COUNT(*) FROM events 
                    WHERE college_id = ? AND start_time BETWEEN datetime('now') AND datetime('now', '+7 days')
                """, (college_id,))
                stats["upcoming_events"] = cursor.fetchone()[0] or 0
                
                # Attendance rate (simplified)
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN present = 1 THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(*), 0), 0) as attendance_rate
                    FROM attendance a
                    JOIN events e ON a.event_id = e.event_id
                    WHERE e.college_id = ?
                """, (college_id,))
                stats["attendance_rate"] = round(cursor.fetchone()[0] or 0, 1)
                
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
        
        # Render the dashboard template with data
        return templates.TemplateResponse(
            "dashboard.html", 
            {
                "request": request,
                "events": events,
                "stats": stats,
                "college_id": college_id,
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        # Try to connect to the database
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        debug_info["database_tables"] = [table[0] for table in tables]
        conn.close()
        print(f"Database tables: {debug_info['database_tables']}")
    except Exception as e:
        debug_info["database_error"] = str(e)
        print(f"Database error: {e}")
    
    # Try to serve the template if it exists
    if os.path.exists("templates/index.html"):
        try:
            with open("templates/index.html", "r") as f:
                print("Successfully read index.html")
            return templates.TemplateResponse("index.html", {"request": request})
        except Exception as e:
            debug_info["template_error"] = str(e)
            print(f"Template error: {e}")
    
    # If template loading fails, return debug info as JSON
    return JSONResponse(content={"status": "API is running", "debug_info": debug_info})

# Remove duplicate health check endpoint

# CORS is already configured at the app level

# Custom exception handlers
@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )

@app.exception_handler(sqlite3.IntegrityError)
async def sqlite_integrity_error_handler(request: Request, exc: sqlite3.IntegrityError):
    error_msg = str(exc)
    if "UNIQUE" in error_msg:
        if "email" in error_msg:
            detail = "Email already exists"
        elif "username" in error_msg:
            detail = "Username already exists"
        else:
            detail = "Duplicate entry"
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": detail},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database integrity error"},
    )

# Request validation models
class CollegeBase(BaseModel):
    college_id: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    name: str = Field(..., min_length=3, max_length=100)
    domain: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    roll_no: Optional[str] = Field(None, min_length=2, max_length=50)

class EventBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, 
                      description="Title of the event")
    type: Optional[str] = Field("general", min_length=2, max_length=50,
                              description="Type/category of the event")
    description: Optional[str] = Field(None, max_length=2000,
                                     description="Detailed description of the event")
    start_time: datetime = Field(..., description="ISO 8601 format start time")
    end_time: datetime = Field(..., description="ISO 8601 format end time")
    venue: Optional[str] = Field(None, max_length=200,
                                description="Location where the event will take place")
    capacity: Optional[int] = Field(None, gt=0,
                                   description="Maximum number of attendees (0 for unlimited)")
    image_url: Optional[HttpUrl] = Field(None, description="URL to event banner/image")
    is_published: bool = Field(True, description="Whether the event is visible to students")
    registration_deadline: Optional[datetime] = Field(None, description="Last date to register")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Annual Tech Symposium",
                "type": "conference",
                "description": "Join us for a day of tech talks and workshops",
                "start_time": "2023-12-15T09:00:00Z",
                "end_time": "2023-12-15T17:00:00Z",
                "venue": "Main Auditorium",
                "capacity": 200,
                "is_published": True
            }
        }
    
    @field_validator('end_time')
    @classmethod
    def end_time_after_start_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @field_validator('registration_deadline')
    @classmethod
    def registration_before_start(cls, v, info):
        if v and 'start_time' in info.data and v > info.data['start_time']:
            raise ValueError('Registration deadline must be before event start time')
        return v

class RegistrationBase(BaseModel):
    event_id: str
    student_id: str

class AttendanceBase(BaseModel):
    event_id: str
    student_id: str
    present: bool
    method: Optional[str] = Field(None, max_length=50)

class FeedbackBase(BaseModel):
    event_id: str
    student_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

@api_v1.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "message": "Welcome to the Campus Event Reporting API",
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc",
        "openapi_schema": "/api/v1/openapi.json"
    }

class CreateCollege(BaseModel):
    college_id: str
    name: str
    domain: str | None = None

class CreateStudent(BaseModel):
    student_id: str | None = None
    name: str
    email: str
    roll_no: str | None = None

class CreateEvent(BaseModel):
    event_id: str | None = None
    title: str
    type: str | None = None
    start_time: str
    end_time: str
    venue: str | None = None
    capacity: int | None = None

class RegisterPayload(BaseModel):
    event_id: str
    student_id: str

class AttendancePayload(BaseModel):
    event_id: str
    student_id: str
    present: bool
    method: str | None = None

class FeedbackPayload(BaseModel):
    event_id: str
    student_id: str
    rating: int
    comment: str | None = None

@api_v1.get("/colleges", response_model=List[Dict[str, Any]])
async def list_colleges(
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    search: Optional[str] = Query(None, min_length=2, max_length=100, description="Search by name or domain")
):
    """
    List all colleges with optional search and pagination.
    
    - **limit**: Number of records per page (1-1000)
    - **offset**: Number of records to skip
    - **search**: Optional search term for name or domain
    """
    conn = dbmod.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = "SELECT college_id, name, domain FROM colleges WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE ? OR domain LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    try:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving colleges"
        )
    finally:
        conn.close()

@api_v1.post("/colleges", status_code=status.HTTP_201_CREATED)
async def create_college(payload: CollegeBase):
    """
    Create a new college.
    
    - **college_id**: Unique identifier for the college (alphanumeric, dashes, underscores only)
    - **name**: Full name of the college
    - **domain**: College email domain (optional)
    """
    conn = dbmod.get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO colleges(college_id, name, domain) VALUES (?, ?, ?)', 
                   (payload.college_id, payload.name, payload.domain))
        conn.commit()
        return {'college_id': payload.college_id}
    finally:
        conn.close()

@api_v1.get("/students", response_model=List[Dict[str, Any]])
async def list_students(
    x_college_id: str = Header(..., description="College ID for multi-tenancy"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    search: Optional[str] = Query(None, min_length=2, max_length=100, description="Search by name or email")
):
    """
    List all students for a college with optional search and pagination.
    
    - **x-college-id**: Required header for college context
    - **limit**: Number of records per page (1-1000)
    - **offset**: Number of records to skip
    - **search**: Optional search term for name or email
    """
    conn = dbmod.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
    SELECT student_id, name, email, roll_no, created_at
    FROM students 
    WHERE college_id = ?
    """
    params = [x_college_id]
    
    if search:
        query += " AND (name LIKE ? OR email LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    try:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving students"
        )
    finally:
        conn.close()

@api_v1.post("/students", status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentBase,
    x_college_id: str = Header(..., description="College ID for multi-tenancy")
):
    """
    Create a new student.
    
    - **name**: Full name of the student (2-100 characters)
    - **email**: Valid email address
    - **roll_no**: Optional roll number (2-50 characters)
    """
    student_id = str(uuid4())
    conn = dbmod.get_conn()
    cur = conn.cursor()
    
    try:
        # Check if college exists
        cur.execute('SELECT 1 FROM colleges WHERE college_id = ?', (x_college_id,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )
            
        cur.execute('''
            INSERT INTO students(student_id, college_id, name, email, roll_no) 
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, x_college_id, payload.name, payload.email, payload.roll_no))
        
        conn.commit()
        return {
            "student_id": student_id,
            "message": "Student created successfully"
        }
    finally:
        conn.close()

@api_v1.get("/events")
def list_events(
    x_college_id: str = Header(...),
    event_type: str | None = None,
    limit: int = 100,
    offset: int = 0
):
    """List all events, optionally filtered by type"""
    conn = dbmod.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
    SELECT event_id, title, type, start_time, end_time, venue, capacity, 
           (SELECT COUNT(*) FROM registrations WHERE event_id = events.event_id) as registrations_count
    FROM events 
    WHERE college_id = ?
    """
    params = [x_college_id]
    
    if event_type:
        query += " AND type = ?"
        params.append(event_type)
    
    query += " ORDER BY start_time LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    try:
        cur.execute(query, params)
        events = [dict(row) for row in cur.fetchall()]
        return JSONResponse(content=events)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@api_v1.post("/events")
def create_event(payload: CreateEvent, x_college_id: str | None = Header(None)):
    if x_college_id is None:
        raise HTTPException(status_code=400, detail='X-College-ID header required')
    event_id = payload.event_id or str(uuid4())
    conn = dbmod.get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO events(event_id, college_id, title, type, start_time, end_time, venue, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (event_id, x_college_id, payload.title, payload.type, payload.start_time, payload.end_time, payload.venue, payload.capacity))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {'event_id': event_id}

@api_v1.post("/registrations")
def register(payload: RegisterPayload, x_college_id: str | None = Header(None)):
    if x_college_id is None:
        raise HTTPException(status_code=400, detail='X-College-ID header required')
    reg_id = str(uuid4())
    conn = dbmod.get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO registrations(reg_id, college_id, event_id, student_id) VALUES (?, ?, ?, ?)',
                    (reg_id, x_college_id, payload.event_id, payload.student_id))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {'reg_id': reg_id}

@api_v1.post("/attendance")
def mark_attendance(payload: AttendancePayload, x_college_id: str | None = Header(None)):
    if x_college_id is None:
        raise HTTPException(status_code=400, detail='X-College-ID header required')
    att_id = str(uuid4())
    conn = dbmod.get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO attendance(att_id, college_id, event_id, student_id, present, method) VALUES (?, ?, ?, ?, ?, ?)',
                    (att_id, x_college_id, payload.event_id, payload.student_id, 1 if payload.present else 0, payload.method))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {'att_id': att_id}

@api_v1.post("/feedback")
def submit_feedback(payload: FeedbackPayload, x_college_id: str | None = Header(None)):
    conn = dbmod.get_conn()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO feedback(fb_id, college_id, event_id, student_id, rating, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid4()), x_college_id, payload.event_id, payload.student_id, 
              payload.rating, payload.comment))
        conn.commit()
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# Report Endpoints
@api_v1.get("/reports/events/popularity")
def get_event_popularity(
    x_college_id: str = Header(...),
    limit: int = Query(10, ge=1, le=100),
    event_type: Optional[str] = None
):
    """Get events sorted by popularity (number of registrations)"""
    try:
        results = queries.event_popularity(
            college_id=x_college_id,
            limit=limit,
            event_type=event_type
        )
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/reports/attendance/summary/{event_id}")
def get_attendance_summary(
    event_id: str,
    x_college_id: str = Header(...)
):
    """Get attendance summary for a specific event"""
    try:
        result = queries.attendance_summary(event_id, college_id=x_college_id)
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
        return JSONResponse(content=result[0] if result else {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/reports/students/participation")
def get_student_participation(
    x_college_id: str = Header(...),
    min_events: int = Query(1, ge=1),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get list of students with their event participation count"""
    try:
        results = queries.top_active_students(
            college_id=x_college_id,
            limit=100,  # Use a high limit since we're filtering by min_events
            start_date=start_date,
            end_date=end_date
        )
        # Filter by min_events
        results = [r for r in results if r.get('events_attended', 0) >= min_events]
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/reports/events/feedback/{event_id}")
def get_event_feedback(
    event_id: str,
    x_college_id: str = Header(...)
):
    """Get feedback summary for a specific event"""
    try:
        result = queries.average_feedback(event_id, college_id=x_college_id)
        if not result:
            raise HTTPException(status_code=404, detail="Event not found or no feedback available")
        return JSONResponse(content=result[0] if result else {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/v1/reports/top-active-students')
def get_top_active_students(
    x_college_id: str = Header(...),
    limit: int = Query(3, ge=1, le=20)
):
    """Get top active students by number of events attended"""
    try:
        results = queries.top_active_students(
            college_id=x_college_id,
            limit=limit
        )
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
