import os
from dotenv import load_dotenv

print("Testing environment variables...")
load_dotenv()

print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")
print(f"ALGORITHM: {os.getenv('ALGORITHM')}")

# Test database connection
from sqlalchemy import create_engine

try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        print("✅ Successfully connected to the database")
except Exception as e:
    print(f"❌ Error connecting to the database: {e}")
