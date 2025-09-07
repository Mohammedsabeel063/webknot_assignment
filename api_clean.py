from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body, Header
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import crud, models, schemas
from database import get_db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create API router with version prefix
api_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

# Dependency to get current user from token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = crud.user.get_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# Auth endpoints
@api_v1.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.user.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Events endpoint
@api_v1.get("/events")
async def list_events(
    x_college_id: str = Header(..., description="College ID for multi-tenancy"),
    event_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """
    List all events, optionally filtered by type.
    
    - **x-college-id**: Required header for college context
    - **event_type**: Optional filter by event type
    - **limit**: Number of records per page (1-1000)
    - **offset**: Number of records to skip
    """
    # In a real implementation, you would query the database here
    # For now, return an empty list
    return {
        "events": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }

# College endpoints
@api_v1.post("/colleges/", response_model=schemas.CollegeResponse, status_code=201)
def create_college(
    college: schemas.CollegeCreate,
    db: Session = Depends(get_db)
):
    try:
        print(f"\n=== Creating College ===")
        print(f"Request data: {college.dict()}")
        
        # Validate required fields
        validation_errors = []
        if not college.college_id:
            validation_errors.append("college_id is required")
        if not college.name:
            validation_errors.append("name is required")
        if not college.domain:
            validation_errors.append("domain is required")
            
        if validation_errors:
            raise HTTPException(
                status_code=422,
                detail={"validation_errors": validation_errors}
            )
        
        # Check for existing college with same domain or ID
        existing_domain = crud.college.get_by_domain(db, domain=college.domain)
        if existing_domain:
            raise HTTPException(
                status_code=400,
                detail={"error": "A college with this domain already exists"}
            )
            
        existing_id = crud.college.get(db, id=college.college_id)
        if existing_id:
            raise HTTPException(
                status_code=400,
                detail={"error": "A college with this ID already exists"}
            )
        
        # Create the college
        db_college = crud.college.create(db, obj_in=college)
        print(f"Successfully created college: {db_college}")
        return db_college
        
    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )

@api_v1.get("/colleges/", response_model=List[schemas.CollegeResponse])
def read_colleges(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    colleges = crud.college.get_multi(db, skip=skip, limit=limit)
    return colleges

@api_v1.get("/colleges/{college_id}", response_model=schemas.CollegeResponse)
def read_college(
    college_id: str,
    db: Session = Depends(get_db)
):
    db_college = crud.college.get(db, id=college_id)
    if db_college is None:
        raise HTTPException(status_code=404, detail="College not found")
    return db_college

# Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
