from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from contextlib import contextmanager

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database context manager
@contextmanager
def get_db():
    conn = sqlite3.connect('tickcontrol.db')
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models
class Operator(BaseModel):
    id: int
    name: str
    clock_in: str | None
    clock_out: str | None

class Login(BaseModel):
    username: str
    password: str

class Job(BaseModel):
    id: int
    customer_name: str
    phone: str | None
    address: str
    notes: str | None
    status: str

class Truck(BaseModel):
    id: int
    name: str

class Maintenance(BaseModel):
    truck_id: int
    maintenance_type: str
    mileage: str
    performer: str

# Endpoints
@app.get("/operators/", response_model=list[Operator])
def list_operators():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, name, clock_in, clock_out FROM operators")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/login/")
def login(login: Login):
    with get_db() as conn:
        cursor = conn.execute("SELECT id, name FROM operators WHERE name = ? AND password = ?", (login.username, login.password))
        operator = cursor.fetchone()
        if operator:
            conn.execute("UPDATE operators SET clock_in = ? WHERE id = ?", (datetime.now().isoformat(), operator[0]))
            conn.commit()
            return {"message": "Login successful", "clock_in": datetime.now().isoformat()}
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.put("/operators/")
def clock_out(operator_data: dict):
    with get_db() as conn:
        if "clock_out" in operator_data:
            conn.execute("UPDATE operators SET clock_out = ? WHERE name = (SELECT name FROM operators WHERE clock_in IS NOT NULL AND clock_out IS NULL LIMIT 1)", (operator_data["clock_out"],))
            conn.commit()
        return {"message": "Clock out updated"}

@app.post("/end_of_day/")
def end_of_day(operator_id: int):
    with get_db() as conn:
        conn.execute("UPDATE operators SET clock_out = ? WHERE id = ?", (datetime.now().isoformat(), operator_id))
        conn.commit()
        return {"message": "End of day processed"}

@app.get("/trucks/", response_model=list[Truck])
def list_trucks():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, name FROM trucks")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/jobs/", response_model=list[Job])
def list_jobs():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, customer_name, phone, address, notes, status FROM jobs")
        return [dict(row) for row in cursor.fetchall()]

@app.put("/jobs/{job_id}/status")
def update_job_status(job_id: int, status_data: dict):
    with get_db() as conn:
        if "status" in status_data:
            conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status_data["status"], job_id))
            conn.commit()
        return {"message": "Job status updated"}

@app.get("/calendar/")
def get_calendar(month_year: str):
    with get_db() as conn:
        # Simple example: Count jobs for the given month_year
        cursor = conn.execute("SELECT COUNT(*) as jobs_left FROM jobs WHERE status != 'COMPLETED'")
        jobs_left = cursor.fetchone()[0]
        return {"month_year": month_year, "jobs_left": jobs_left}

@app.post("/truck_maintenance/")
def add_maintenance(maintenance: Maintenance):
    with get_db() as conn:
        conn.execute("INSERT INTO truck_maintenance (truck_id, maintenance_type, mileage, performer) VALUES (?, ?, ?, ?)",
                     (maintenance.truck_id, maintenance.maintenance_type, maintenance.mileage, maintenance.performer))
        conn.commit()
        return {"message": "Maintenance record added"}

@app.get("/settings/call_number")
def get_call_number():
    with get_db() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = 'call_number'")
        result = cursor.fetchone()
        return {"call_number": result[0] if result else "555-123-4567"}

# Initialize database (run once or on startup if needed)
def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                clock_in TEXT,
                clock_out TEXT,
                password TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trucks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT,
                address TEXT NOT NULL,
                notes TEXT,
                status TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS truck_maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                truck_id INTEGER,
                maintenance_type TEXT NOT NULL,
                mileage TEXT NOT NULL,
                performer TEXT NOT NULL,
                FOREIGN KEY (truck_id) REFERENCES trucks(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Insert sample data if not exists
        conn.execute("INSERT OR IGNORE INTO operators (name, password) VALUES (?, ?)", ("Jacob", "password123"))
        conn.execute("INSERT OR IGNORE INTO trucks (name) VALUES (?)", ("Truck 1",))
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("call_number", "555-123-4567"))
        conn.commit()

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
