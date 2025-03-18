from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from typing import List

app = FastAPI()

# SQLite database setup
DATABASE = "app.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create tables for main software and apps
@app.on_event("startup")
def startup():
    with get_db() as conn:
        # Operators (for Operator App and main software)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                clock_in TEXT,
                clock_out TEXT
            )
        """)
        # Customers (for main software and Salesman App)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT
            )
        """)
        # Jobs (for Operator App and Schedule)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER,
                customer_id INTEGER,
                address TEXT,
                status TEXT,
                start_time TEXT,
                stop_time TEXT,
                photo_url TEXT,
                FOREIGN KEY (operator_id) REFERENCES operators (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        # Sales (for main software and Salesman App)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                amount REAL,
                date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        conn.commit()

# Models
class Operator(BaseModel):
    name: str
    clock_in: str = None
    clock_out: str = None

class Customer(BaseModel):
    name: str
    email: str = None
    phone: str = None
    address: str = None

class Job(BaseModel):
    operator_id: int
    customer_id: int
    address: str
    status: str = "GO"
    start_time: str = None
    stop_time: str = None
    photo_url: str = None

class Sale(BaseModel):
    customer_id: int
    amount: float
    date: str

# Endpoints
@app.get("/")
def home():
    return {"message": "Main Software Backend - Serving Operator and Salesman Apps"}

# Operators
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

# Customers
@app.post("/customers/", response_model=Customer)
def add_customer(customer: Customer):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)",
            (customer.name, customer.email, customer.phone, customer.address)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **customer.dict()}

@app.get("/customers/", response_model=List[Customer])
def list_customers():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM customers")
        return [dict(row) for row in cursor.fetchall()]

# Jobs
@app.post("/jobs/", response_model=Job)
def add_job(job: Job):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO jobs (operator_id, customer_id, address, status) VALUES (?, ?, ?, ?)",
            (job.operator_id, job.customer_id, job.address, job.status)
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
        conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        if status == "START":
            conn.execute("UPDATE jobs SET start_time = datetime('now') WHERE id = ?", (job_id,))
        elif status == "STOP":
            conn.execute("UPDATE jobs SET stop_time = datetime('now') WHERE id = ?", (job_id,))
        conn.commit()
        cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return dict(cursor.fetchone())

# Sales
@app.post("/sales/", response_model=Sale)
def add_sale(sale: Sale):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO sales (customer_id, amount, date) VALUES (?, ?, ?)",
            (sale.customer_id, sale.amount, sale.date)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **sale.dict()}

@app.get("/sales/", response_model=List[Sale])
def list_sales():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM sales")
        return [dict(row) for row in cursor.fetchall()]
