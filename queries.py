import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

DB = Path(__file__).parent / 'data.db'

def run_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results as a list of dictionaries.
    
    Args:
        sql: SQL query string
        params: Parameters for the SQL query
        
    Returns:
        List of dictionaries representing the query results
    """
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def execute_update(sql: str, params: tuple = ()) -> int:
    """Execute an update/insert/delete query and return the number of affected rows.
    
    Args:
        sql: SQL query string
        params: Parameters for the SQL query
        
    Returns:
        Number of rows affected
    """
    conn = sqlite3.connect(DB)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def event_popularity(college_id: str = None, limit: int = 10, event_type: str = None) -> List[Dict[str, Any]]:
    """Get events sorted by popularity (number of registrations).
    
    Args:
        college_id: Optional filter for a specific college
        limit: Maximum number of results to return
        event_type: Optional filter for specific event type
        
    Returns:
        List of events with registration counts
    """
    sql = """
    SELECT e.event_id, e.title, e.type, 
           COUNT(r.reg_id) AS registrations,
           e.start_time, e.end_time, e.venue,
           (SELECT COUNT(*) FROM attendance a 
            WHERE a.event_id = e.event_id AND a.present = 1) AS attendance_count
    FROM events e
    LEFT JOIN registrations r ON r.event_id = e.event_id
    WHERE 1=1
    """
    
    params = []
    if college_id:
        sql += " AND e.college_id = ?"
        params.append(college_id)
    
    if event_type:
        sql += " AND e.type = ?"
        params.append(event_type)
    
    sql += """
    GROUP BY e.event_id, e.title, e.type
    ORDER BY registrations DESC
    LIMIT ?
    """
    params.append(limit)
    
    return run_query(sql, tuple(params))

def attendance_summary(event_id: str, college_id: str = None) -> List[Dict[str, Any]]:
    """Get attendance summary for a specific event.
    
    Args:
        event_id: ID of the event
        college_id: Optional college ID for additional filtering
        
    Returns:
        List containing attendance summary for the event
    """
    sql = """
    SELECT 
        e.event_id, 
        e.title AS event_title,
        e.start_time,
        e.end_time,
        e.venue,
        COUNT(DISTINCT r.student_id) AS registered,
        COUNT(DISTINCT CASE WHEN a.present = 1 THEN a.student_id END) AS present,
        COUNT(DISTINCT CASE WHEN a.present = 0 THEN a.student_id END) AS absent,
        ROUND((COUNT(DISTINCT CASE WHEN a.present = 1 THEN a.student_id END) * 100.0) / 
              NULLIF(COUNT(DISTINCT r.student_id), 0), 2) AS attendance_pct,
        e.capacity,
        COUNT(DISTINCT r.student_id) AS current_registrations,
        e.capacity - COUNT(DISTINCT r.student_id) AS remaining_capacity
    FROM events e
    LEFT JOIN registrations r ON r.event_id = e.event_id
    LEFT JOIN attendance a ON a.event_id = e.event_id AND a.student_id = r.student_id
    WHERE e.event_id = ?
    """
    
    params = [event_id]
    
    if college_id:
        sql += " AND e.college_id = ?"
        params.append(college_id)
    
    sql += " GROUP BY e.event_id"
    
    return run_query(sql, tuple(params))

def average_feedback(event_id: str, college_id: str = None) -> List[Dict[str, Any]]:
    """Get average feedback for a specific event.
    
    Args:
        event_id: ID of the event
        college_id: Optional college ID for additional filtering
        
    Returns:
        List containing feedback statistics for the event
    """
    sql = """
    SELECT 
        e.event_id, 
        e.title AS event_title,
        ROUND(AVG(f.rating), 2) AS avg_rating,
        COUNT(f.fb_id) AS response_count,
        MIN(f.rating) AS min_rating,
        MAX(f.rating) AS max_rating,
        COUNT(CASE WHEN f.rating = 5 THEN 1 END) AS five_stars,
        COUNT(CASE WHEN f.rating = 4 THEN 1 END) AS four_stars,
        COUNT(CASE WHEN f.rating = 3 THEN 1 END) AS three_stars,
        COUNT(CASE WHEN f.rating = 2 THEN 1 END) AS two_stars,
        COUNT(CASE WHEN f.rating = 1 THEN 1 END) AS one_star
    FROM events e
    LEFT JOIN feedback f ON f.event_id = e.event_id
    WHERE e.event_id = ?
    """
    
    params = [event_id]
    
    if college_id:
        sql += " AND e.college_id = ?"
        params.append(college_id)
    
    sql += " GROUP BY e.event_id, e.title"
    
    return run_query(sql, tuple(params))

def top_active_students(college_id: str = None, limit: int = 10, 
                       start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """Get the most active students based on event attendance.
    
    Args:
        college_id: Optional filter for a specific college
        limit: Maximum number of results to return
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        
    Returns:
        List of students with their attendance counts
    """
    sql = """
    SELECT 
        s.student_id, 
        s.name,
        s.email,
        s.roll_no,
        COUNT(DISTINCT a.event_id) AS events_attended,
        COUNT(DISTINCT r.event_id) AS events_registered,
        ROUND((COUNT(DISTINCT a.event_id) * 100.0) / 
              NULLIF(COUNT(DISTINCT r.event_id), 0), 2) AS attendance_rate,
        GROUP_CONCAT(DISTINCT e.title, '|') AS attended_events
    FROM students s
    LEFT JOIN attendance a ON a.student_id = s.student_id AND a.present = 1
    LEFT JOIN registrations r ON r.student_id = s.student_id
    LEFT JOIN events e ON e.event_id = a.event_id
    WHERE 1=1
    """
    
    params = []
    
    if college_id:
        sql += " AND s.college_id = ?"
        params.append(college_id)
    
    if start_date:
        sql += " AND e.start_time >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND e.end_time <= ?"
        params.append(end_date)
    
    sql += """
    GROUP BY s.student_id, s.name, s.email, s.roll_no
    HAVING events_attended > 0
    ORDER BY events_attended DESC, attendance_rate DESC
    LIMIT ?
    """
    params.append(limit)
    
    results = run_query(sql, tuple(params))
    
    # Process the GROUP_CONCAT results into lists
    for row in results:
        if row.get('attended_events'):
            row['attended_events'] = row['attended_events'].split('|')
        else:
            row['attended_events'] = []
    
    return results

def event_registration_trends(college_id: str = None, days: int = 30) -> List[Dict[str, Any]]:
    """Get event registration trends over time.
    
    Args:
        college_id: Optional filter for a specific college
        days: Number of days to look back
        
    Returns:
        List of daily registration counts
    """
    sql = """
    SELECT 
        DATE(e.start_time) AS date,
        COUNT(DISTINCT e.event_id) AS events_created,
        COUNT(DISTINCT r.reg_id) AS registrations,
        COUNT(DISTINCT s.student_id) AS unique_students
    FROM events e
    LEFT JOIN registrations r ON r.event_id = e.event_id
    LEFT JOIN students s ON s.student_id = r.student_id
    WHERE e.start_time >= date('now', ?)
    """
    
    params = [f'-{days} days']
    
    if college_id:
        sql += " AND e.college_id = ?"
        params.append(college_id)
    
    sql += """
    GROUP BY DATE(e.start_time)
    ORDER BY date ASC
    """
    
    return run_query(sql, tuple(params))

if __name__ == "__main__":
    # Example usage
    college_id = "college_001"  # From your seed data
    
    results = {
        "event_popularity": event_popularity(college_id=college_id, limit=5),
        "attendance_ev_001": attendance_summary("ev_001", college_id=college_id),
        "average_feedback_ev_001": average_feedback("ev_001", college_id=college_id),
        "top_active_students": top_active_students(college_id=college_id, limit=5),
        "registration_trends": event_registration_trends(college_id=college_id, days=90)
    }
    
    with open('report_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("Sample reports generated in report_results.json")
