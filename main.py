from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from typing import List

app = FastAPI()

# SQLite database setup
DATABASE = "app.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries
    return conn

# Create tables (run once on startup)
@app.on_event("startup")
def startup():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                clock_in TEXT,
                clock_out TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER,
                customer_name TEXT,
                address TEXT,
                status TEXT,
                start_time TEXT,
                stop_time TEXT,
                photo_url TEXT,
                FOREIGN KEY (operator_id) REFERENCES operators (id)
            )
        """)
        conn.commit()

# Models
class Operator(BaseModel):
    name: str
    clock_in: str = None
    clock_out: str = None

class Job(BaseModel):
    operator_id: int
    customer_name: str
    address: str
    status: str = "GO"
    start_time: str = None
    stop_time: str = None
    photo_url: str = None

# Endpoints
@app.get("/")
def home():
    return {"message": "Hello Darren - Operator App Backend"}

@app.post("/operators/", response_model=Operator)
def add_operator(operator: Operator):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO operators (name, clock_in) VALUES (?, ?)",
            (operator.name, operator.clock_in)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **operator.dict()}

@app.get("/operators/", response_model=List[Operator])
def list_operators():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM operators")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/jobs/", response_model=Job)
def add_job(job: Job):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO jobs (operator_id, customer_name, address, status) VALUES (?, ?, ?, ?)",
            (job.operator_id, job.customer_name, job.address, job.status)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **job.dict()}

@app.get("/jobs/", response_model=List[Job])
def list_jobs():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM jobs")
        return [dict(row) for row in cursor.fetchall()]

@app.put("/jobs/{job_id}/status")
def update_job_status(job_id: int, status: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE jobs SET status = ? WHERE id = ?",
            (status, job_id)
        )
        if status == "START":
            conn.execute("UPDATE jobs SET start_time = datetime('now') WHERE id = ?", (job_id,))
        elif status == "STOP":
            conn.execute("UPDATE jobs SET stop_time = datetime('now') WHERE id = ?", (job_id,))
        conn.commit()
        cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return dict(cursor.fetchone())
