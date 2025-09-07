Campus Event Management System

This is a comprehensive platform designed to help educational institutions manage campus events, student registrations, attendance tracking, and feedback collection. It solves the common challenges faced by event organizers in academic settings.

main things what i added:

1.Event Management
Create, update, and track events
Categorize events by type like workshop, seminar, sports, etc.
Set event capacity and track registrations

2.Student Portal
Easy event registration
Personal event calendar
Attendance tracking

3.Administration
Real-time event analytics
Attendance reports
Feedback analysis
Student participation metrics

4.Technical Stack
Backend: FastAPI (Python)
Database: SQLite (with SQLAlchemy ORM)
Frontend: HTML/CSS/JavaScript (for admin dashboard)
Authentication: API key-based


set up to do :
rerequisites
Python 3.8 or higher
pip (Python package manager)


1. Clone the repository
git clone git remote add origin https://github.com/Mohammedsabeel063/webknot_assignment.git
cd campus-event-platform

2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate


3. Install dependencies
pip install -r requirements.txt

4. Set up environment variables
cp .env.example .env
Edit .env with your configuration

5. Initialize the database
python init_db.py

6. Run the application
uvicorn main:app --reload


Access the Application:
1.API Documentation: http://localhost:8000/docs
2.Admin Dashboard: http://localhost:8000/dashboard



This version:
1. Uses simpler language
2. Has a cleaner structure
3. Leaves space for your personal experience
4. Focuses on the practical aspects

My Experience

1. Technical Growth
    Gained hands-on experience with FastAPI and SQLAlchemy
    Learned how to design RESTful APIs with proper error handling
    Understood the importance of database relationships and data modeling

2. Challenges Faced
    Initially struggled with database schema design
    Had to learn about authentication and API security
    Debugging complex queries was tough but educational

3. Key Takeaways
    The importance of writing clean, maintainable code
    How to structure a medium-sized Python project
    The value of good documentation and testing

4. What I'm Proud Of
    Creating a fully functional event management system
    Implementing real-time features
    Building something that could actually be useful in a real educational setting

This project has significantly improved my backend development skills and given me confidence in building web applications.

Screenshots:

Database Working
![Database Working](./screenshots/database%20working.png)

 API
![API](./screenshots/api.png)
