from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime

app = FastAPI()

# Database connection
def get_db():
    conn = sqlite3.connect('tick_control.db')
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic models
class Operator(BaseModel):
    id: int
    name: str
    clock_in: Optional[str]
    clock_out: Optional[str]

class LoginRequest(BaseModel):
    username: str
    password: str

class Job(BaseModel):
    id: int
    customer_name: str
    address: str
    phone: Optional[str]
    notes: Optional[str]
    status: str
    date: str  # Add date field to Job model

class Truck(BaseModel):
    id: int
    name: str

class Calendar(BaseModel):
    month_year: str
    jobs_left: int

class JobListResponse(BaseModel):
    date: str
    jobs: List[Job]

# Database initialization
with get_db() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            clock_in TEXT,
            clock_out TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            notes TEXT,
            status TEXT NOT NULL,
            date TEXT NOT NULL  -- Add date column
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trucks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS truck_maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            truck_id INTEGER,
            maintenance_type TEXT NOT NULL,
            mileage TEXT,
            performer TEXT,
            FOREIGN KEY (truck_id) REFERENCES trucks(id)
        )
    ''')

    # Insert sample data with dates
    conn.execute("INSERT OR IGNORE INTO operators (id, name) VALUES (1, 'Jacob')")
    conn.execute("INSERT OR IGNORE INTO jobs (id, customer_name, address, phone, notes, status, date) VALUES (1, 'John Doe', '123 Main St', '555-1234', 'Spray backyard', 'PENDING', '2025-03-18')")
    conn.execute("INSERT OR IGNORE INTO jobs (id, customer_name, address, phone, notes, status, date) VALUES (2, 'Jane Smith', '456 Oak St', '555-5678', 'Check fence', 'PENDING', '2025-03-19')")
    conn.execute("INSERT OR IGNORE INTO trucks (id, name) VALUES (1, 'Tick 1')")
    conn.execute("INSERT OR IGNORE INTO trucks (id, name) VALUES (2, 'Tick 2')")
    conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('call_number', '555-123-4567')")

# Endpoints
@app.get("/operators/", response_model=List[Operator])
def list_operators():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, name, clock_in, clock_out FROM operators")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/login/")
def login(request: LoginRequest):
    if request.username == "Jacob" and request.password == "password123":
        with get_db() as conn:
            conn.execute("UPDATE operators SET clock_in = ? WHERE name = ?", (datetime.now().isoformat(), request.username))
            conn.commit()
        return {"message": "Login successful", "clock_in": datetime.now().isoformat()}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/jobs/", response_model=List[Job])
def list_jobs():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, customer_name, address, phone, notes, status, date FROM jobs")
        return [dict(row) for row in cursor.fetchall()]

@app.put("/jobs/{job_id}/status")
def update_job_status(job_id: int, status: str, photo_url: Optional[str] = None):
    with get_db() as conn:
        conn.execute("UPDATE jobs SET status = ?, photo_url = ? WHERE id = ?", (status, photo_url, job_id))
        conn.commit()
    return {"message": "Job status updated"}

@app.get("/trucks/", response_model=List[Truck])
def list_trucks():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, name FROM trucks")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/calendar/")
def get_calendar(month_year: str):
    # Placeholder logic for calendar
    return {"month_year": month_year, "jobs_left": 10}

@app.get("/jobs/date/{date}", response_model=JobListResponse)
def get_jobs_by_date(date: str):
    with get_db() as conn:
        cursor = conn.execute("SELECT id, customer_name, address, phone, notes, status, date FROM jobs WHERE date = ?", (date,))
        jobs = [dict(row) for row in cursor.fetchall()]
        return {"date": date, "jobs": jobs}

@app.get("/settings/call_number")
def get_call_number():
    with get_db() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = 'call_number'")
        row = cursor.fetchone()
        return {"call_number": row['value'] if row else "555-123-4567"}

@app.put("/operators/")
def update_operator(clock_out: str):
    with get_db() as conn:
        conn.execute("UPDATE operators SET clock_out = ? WHERE clock_out IS NULL", (clock_out,))
        conn.commit()
    return {"message": "Operator updated"}

@app.post("/end_of_day/")
def end_of_day(operator_id: int):
    # Placeholder logic for end of day
    return {"message": "End of day processed"}

@app.post("/truck_maintenance/")
def add_truck_maintenance(truck_id: int, maintenance_type: str, mileage: str, performer: str):
    with get_db() as conn:
        conn.execute("INSERT INTO truck_maintenance (truck_id, maintenance_type, mileage, performer) VALUES (?, ?, ?, ?)", 
                     (truck_id, maintenance_type, mileage, performer))
        conn.commit()
    return {"message": "Truck maintenance added"}
