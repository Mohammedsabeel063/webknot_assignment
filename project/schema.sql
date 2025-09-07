PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS colleges (
  college_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT
);

CREATE TABLE IF NOT EXISTS students (
  student_id TEXT PRIMARY KEY,
  college_id TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  roll_no TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (college_id) REFERENCES colleges(college_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_students_college_email ON students(college_id, email);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  college_id TEXT NOT NULL,
  title TEXT NOT NULL,
  type TEXT,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  venue TEXT,
  capacity INTEGER,
  is_cancelled INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (college_id) REFERENCES colleges(college_id)
);

CREATE TABLE IF NOT EXISTS registrations (
  reg_id TEXT PRIMARY KEY,
  college_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (college_id) REFERENCES colleges(college_id),
  FOREIGN KEY (event_id) REFERENCES events(event_id),
  FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_reg_unique ON registrations(college_id, event_id, student_id);

CREATE TABLE IF NOT EXISTS attendance (
  att_id TEXT PRIMARY KEY,
  college_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  present INTEGER NOT NULL CHECK (present IN (0,1)),
  marked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  method TEXT,
  FOREIGN KEY (college_id) REFERENCES colleges(college_id),
  FOREIGN KEY (event_id) REFERENCES events(event_id),
  FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS feedback (
  fb_id TEXT PRIMARY KEY,
  college_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (college_id) REFERENCES colleges(college_id),
  FOREIGN KEY (event_id) REFERENCES events(event_id),
  FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_feedback_unique ON feedback(college_id, event_id, student_id);

-- Additional indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_events_college_date ON events(college_id, start_time);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_attendance_event ON attendance(event_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_feedback_event ON feedback(event_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_registrations_student ON registrations(student_id);
