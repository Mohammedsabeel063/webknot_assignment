from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

# For SQLite, we need to handle the connection differently
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Session:
    """
    Dependency function to get DB session.
    
    Yields:
        Session: A database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database by creating all tables"""
    import models
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def drop_db():
    """Drop all database tables (for testing/development)"""
    import models
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped")
