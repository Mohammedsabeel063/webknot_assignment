import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create engine
engine = create_engine(os.getenv('DATABASE_URL'))

# Get table names
inspector = inspect(engine)
tables = inspector.get_table_names()
print("\nTables in database:")
for table in tables:
    print(f"- {table}")

# Show row counts for each table
with engine.connect() as conn:
    for table in tables:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        print(f"\nTable: {table} - Rows: {count}")
        
        # Show column names and first few rows if table is not empty
        if count > 0:
            # Get column names
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            columns = [row[1] for row in result]
            print(f"Columns: {', '.join(columns)}")
            
            # Show first 3 rows
            result = conn.execute(text(f"SELECT * FROM {table} LIMIT 3"))
            print("Sample data:")
            for row in result:
                print(dict(row))
