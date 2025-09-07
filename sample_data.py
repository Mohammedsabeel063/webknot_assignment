import random
from datetime import datetime, timedelta
import sqlite3

# Sample data
COLLEGES = [
    {"college_id": "college_001", "name": "Tech University", "domain": "tech.edu"},
    {"college_id": "college_002", "name": "Science Institute", "domain": "sci.edu"}
]

EVENT_TYPES = ["Workshop", "Hackathon", "Seminar", "Conference", "Webinar"]
VENUES = ["Main Hall", "Auditorium", "Room 101", "Lab 1", "Conference Center"]

FIRST_NAMES = ["Alex", "Taylor", "Jordan", "Casey", "Riley", "Jamie", "Morgan", "Quinn"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

# Connect to database
def get_db():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with sample data"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.executescript("""
    DELETE FROM feedback;
    DELETE FROM attendance;
    DELETE FROM registrations;
    DELETE FROM events;
    DELETE FROM students;
    DELETE FROM colleges;
    """)
    
    # Insert colleges
    for college in COLLEGES:
        cursor.execute("""
        INSERT INTO colleges (college_id, name, domain)
        VALUES (?, ?, ?)
        """, (college["college_id"], college["name"], college["domain"]))
    
    # Insert sample students (10 per college)
    for college in COLLEGES:
        for i in range(1, 11):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            email = f"{first.lower()}.{last.lower()}{i}@{college['domain']}"
            cursor.execute("""
            INSERT INTO students (student_id, college_id, name, email, roll_no)
            VALUES (?, ?, ?, ?, ?)
            """, (
                f"stu_{college['college_id']}_{i:03d}",
                college["college_id"],
                f"{first} {last}",
                email,
                f"{college['college_id']}_{i:04d}"
            ))
    
    # Insert sample events (5 per college)
    for college in COLLEGES:
        for i in range(1, 6):
            event_start = datetime.now() + timedelta(days=random.randint(1, 30))
            event_end = event_start + timedelta(hours=random.randint(1, 8))
            
            cursor.execute("""
            INSERT INTO events (
                event_id, college_id, title, type, 
                start_time, end_time, venue, capacity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"ev_{college['college_id']}_{i:03d}",
                college["college_id"],
                f"{random.choice(EVENT_TYPES)} {i}",
                random.choice(EVENT_TYPES),
                event_start.isoformat(),
                event_end.isoformat(),
                random.choice(VENUES),
                random.randint(20, 200)
            ))
    
    # Create registrations (2-5 per student)
    cursor.execute("SELECT student_id, college_id FROM students")
    students = cursor.fetchall()
    
    for student in students:
        # Get events from the same college
        cursor.execute("""
        SELECT event_id, capacity FROM events 
        WHERE college_id = ?
        ORDER BY start_time
        """, (student['college_id'],))
        
        college_events = cursor.fetchall()
        num_events = min(random.randint(2, 5), len(college_events))
        
        for event in random.sample(college_events, num_events):
            # Register student for event
            cursor.execute("""
            INSERT INTO registrations (reg_id, college_id, event_id, student_id, registered_at)
            VALUES (?, ?, ?, ?, ?)
            """, (
                f"reg_{student['student_id']}_{event['event_id']}",
                student['college_id'],
                event['event_id'],
                student['student_id'],
                datetime.now().isoformat()
            ))
            
            # Randomly mark attendance (70% chance)
            if random.random() < 0.7:
                cursor.execute("""
                INSERT INTO attendance (
                    att_id, college_id, event_id, student_id,
                    present, method, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"att_{student['student_id']}_{event['event_id']}",
                    student['college_id'],
                    event['event_id'],
                    student['student_id'],
                    1,  # present
                    random.choice(['qr', 'manual', 'nfc']),
                    datetime.now().isoformat()
                ))
            
            # Randomly add feedback (50% chance if attended)
            if random.random() < 0.5:
                cursor.execute("""
                INSERT INTO feedback (
                    fb_id, college_id, event_id, student_id,
                    rating, comment, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"fb_{student['student_id']}_{event['event_id']}",
                    student['college_id'],
                    event['event_id'],
                    student['student_id'],
                    random.randint(3, 5),  # rating 3-5
                    "Great event!" if random.random() > 0.5 else "Could be improved.",
                    datetime.now().isoformat()
                ))
    
    conn.commit()
    conn.close()
    print("✅ Sample data generated successfully!")

if __name__ == "__main__":
    init_db()
