from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
from typing import List, Dict
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta

app = FastAPI()

# SQLite database setup
DATABASE = "app.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
@app.on_event("startup")
def startup():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                clock_in TEXT,
                clock_out TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT
            )
        """)
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
                upload_time TEXT,
                notes TEXT,
                FOREIGN KEY (operator_id) REFERENCES operators (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trucks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT,
                oil_change_date TEXT,
                tire_status TEXT,
                def_level TEXT,
                emissions_date TEXT,
                insurance_date TEXT,
                gas_type TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS truck_insurance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                truck_id INTEGER,
                company TEXT,
                premium REAL,
                start_date TEXT,
                expiration_date TEXT,
                payment_due_date TEXT,
                payment_amount REAL,
                payment_method TEXT,
                pdf_url TEXT,
                FOREIGN KEY (truck_id) REFERENCES trucks (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS truck_maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                truck_id INTEGER,
                maintenance_type TEXT,
                mileage INTEGER,
                status TEXT,
                photo_url TEXT,
                upload_time TEXT,
                performer TEXT,
                FOREIGN KEY (truck_id) REFERENCES trucks (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                amount REAL,
                date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calendar_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_year TEXT,
                jobs_left INTEGER,
                days_left INTEGER,
                rain_days INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Initialize sample data
        cursor = conn.execute("SELECT COUNT(*) FROM operators WHERE name = 'Jacob'")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO operators (name, password) VALUES (?, ?)", ("Jacob", "password123"))
        cursor = conn.execute("SELECT COUNT(*) FROM trucks")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO trucks (name, status) VALUES (?, ?)", ("TICK 1", "Available"))
            conn.execute("INSERT INTO trucks (name, status) VALUES (?, ?)", ("TICK 2", "Available"))
            conn.execute("INSERT INTO trucks (name, status) VALUES (?, ?)", ("TICK 3", "Available"))
        cursor = conn.execute("SELECT COUNT(*) FROM settings WHERE key = 'call_number'")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("call_number", "555-123-4567"))
        cursor = conn.execute("SELECT COUNT(*) FROM settings WHERE key = 'rescheduling_rules'")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("rescheduling_rules", "[]"))
        conn.commit()

# Models
class Operator(BaseModel):
    name: str
    password: str
    clock_in: str = None
    clock_out: str = None

class OperatorLogin(BaseModel):
    username: str
    password: str

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
    upload_time: str = None
    notes: str = None

class Truck(BaseModel):
    name: str
    status: str = "Available"
    oil_change_date: str = "N/A"
    tire_status: str = "N/A"
    def_level: str = "N/A"
    emissions_date: str = "N/A"
    insurance_date: str = "N/A"
    gas_type: str = "diesel"

class TruckInsurance(BaseModel):
    truck_id: int
    company: str
    premium: float
    start_date: str
    expiration_date: str
    payment_due_date: str
    payment_amount: float = None
    payment_method: str = None
    pdf_url: str = None

class TruckMaintenance(BaseModel):
    truck_id: int
    maintenance_type: str
    mileage: int
    status: str = "Pending"
    photo_url: str = None
    upload_time: str = None
    performer: str = None

class Sale(BaseModel):
    customer_id: int
    amount: float
    date: str

class CalendarData(BaseModel):
    month_year: str
    jobs_left: int
    days_left: int
    rain_days: int

class SettingsRule(BaseModel):
    key: str
    value: str

# Authentication
def verify_password(username: str, password: str):
    with get_db() as conn:
        cursor = conn.execute("SELECT password FROM operators WHERE name = ?", (username,))
        stored_password = cursor.fetchone()
        return stored_password and stored_password[0] == password

@app.post("/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not verify_password(form_data.username, form_data.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    with get_db() as conn:
        clock_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE operators SET clock_in = ? WHERE name = ?", (clock_in, form_data.username))
        conn.commit()
        return {"message": "Login successful", "clock_in": clock_in}

# Endpoints
@app.get("/")
def home():
    return {"message": "Main Software Backend - Serving Operator and Salesman Apps"}

@app.post("/operators/", response_model=Operator)
def add_operator(operator: Operator):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO operators (name, password) VALUES (?, ?)",
            (operator.name, operator.password)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **operator.dict(exclude={"password"})}

@app.get("/operators/", response_model=List[Operator])
def list_operators():
    with get_db() as conn:
        cursor = conn.execute("SELECT id, name, clock_in, clock_out FROM operators")
        return [dict(row) for row in cursor.fetchall()]

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

@app.get("/customers/{customer_id}/photos", response_model=List[dict])
def get_customer_photos(customer_id: int):
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT j.photo_url, j.upload_time, c.name as customer_name
            FROM jobs j
            JOIN customers c ON j.customer_id = c.id
            WHERE j.customer_id = ? AND j.photo_url IS NOT NULL
            ORDER BY j.upload_time DESC
        """, (customer_id,))
        return [dict(row) for row in cursor.fetchall()]

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
def update_job_status(job_id: int, status: str, photo_url: str = None):
    with get_db() as conn:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE jobs SET status = ?, upload_time = ? WHERE id = ?", (status, current_time, job_id))
        if status == "START":
            conn.execute("UPDATE jobs SET start_time = ? WHERE id = ?", (current_time, job_id))
        elif status == "STOP":
            conn.execute("UPDATE jobs SET stop_time = ? WHERE id = ?", (current_time, job_id))
        elif status == "PHOTO":
            if not photo_url:
                raise HTTPException(status_code=400, detail="Photo URL required")
            conn.execute("UPDATE jobs SET photo_url = ?, status = ?, upload_time = ? WHERE id = ?", (photo_url, "COMPLETED", current_time, job_id))
        elif status == "NOT COMPLETED":
            conn.execute("UPDATE jobs SET status = ?, stop_time = ?, upload_time = ? WHERE id = ?", (status, current_time, current_time, job_id))
        conn.commit()
        cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return dict(cursor.fetchone())

@app.post("/trucks/", response_model=Truck)
def add_truck(truck: Truck):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO trucks (name, status, oil_change_date, tire_status, def_level, emissions_date, insurance_date, gas_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (truck.name, truck.status, truck.oil_change_date, truck.tire_status, truck.def_level, truck.emissions_date, truck.insurance_date, truck.gas_type)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **truck.dict()}

@app.get("/trucks/", response_model=List[Truck])
def list_trucks():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM trucks")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/truck_insurance/", response_model=TruckInsurance)
def add_truck_insurance(insurance: TruckInsurance):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO truck_insurance (truck_id, company, premium, start_date, expiration_date, payment_due_date, payment_amount, payment_method, pdf_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (insurance.truck_id, insurance.company, insurance.premium, insurance.start_date, insurance.expiration_date, insurance.payment_due_date, insurance.payment_amount, insurance.payment_method, insurance.pdf_url)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **insurance.dict()}

@app.post("/truck_maintenance/", response_model=TruckMaintenance)
def add_maintenance(maintenance: TruckMaintenance):
    with get_db() as conn:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            "INSERT INTO truck_maintenance (truck_id, maintenance_type, mileage, status, photo_url, upload_time, performer) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (maintenance.truck_id, maintenance.maintenance_type, maintenance.mileage, maintenance.status, maintenance.photo_url, current_time, maintenance.performer)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **maintenance.dict()}

@app.get("/sales/", response_model=List[Sale])
def list_sales():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM sales")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/sales/", response_model=Sale)
def add_sale(sale: Sale):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO sales (customer_id, amount, date) VALUES (?, ?, ?)",
            (sale.customer_id, sale.amount, sale.date)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **sale.dict()}

@app.get("/calendar/")
def get_calendar_data(month_year: str = None):
    today = datetime.now()
    current_month_year = today.strftime("%B %Y").upper()
    if month_year and month_year.lower() == "current":
        month_year = current_month_year
    elif not month_year:
        month_year = current_month_year
    year = int(month_year.split()[-1])
    month = month_year.split()[0]
    reset_date = datetime(year, 1, 1)
    march_start = datetime(year, 3, 1)

    with get_db() as conn:
        if today >= reset_date and today < march_start and year >= datetime.now().year:
            jobs_left = 0
        else:
            cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE strftime('%Y-%m', start_time) = ? AND status != 'COMPLETED'", (today.strftime("%Y-%m"),))
            jobs_left = cursor.fetchone()[0] if cursor.fetchone() else 0
        days_left = (datetime(year, today.month + 1, 1) - today).days if today.month < 12 else (datetime(year + 1, 1, 1) - today).days
        rain_days = 2  # Placeholder for OpenWeatherMap
        return {"month_year": month_year, "jobs_left": jobs_left, "days_left": days_left, "rain_days": rain_days}

@app.post("/schedule_jobs/")
def schedule_jobs():
    return {"message": "AI scheduling triggered (placeholder)"}

@app.get("/settings/call_number")
def get_call_number():
    with get_db() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = 'call_number'")
        return {"call_number": cursor.fetchone()[0]}

@app.get("/settings/rescheduling_rules")
def get_rescheduling_rules():
    with get_db() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = 'rescheduling_rules'")
        rules = cursor.fetchone()
        return {"rescheduling_rules": rules[0] if rules else "[]"}

@app.post("/end_of_day/")
def end_of_day(operator_id: int):
    with get_db() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = 'rescheduling_rules'")
        rules = cursor.fetchone()
        rules_json = rules[0] if rules else "[]"
        if not rules_json or rules_json == "[]":
            return {"message": "Rescheduling rules not set in Main Software settings. Please configure rules."}
        # Placeholder: Parse rules (to be implemented in Main Software)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute("SELECT * FROM jobs WHERE operator_id = ? AND status != 'COMPLETED'", (operator_id,))
        incomplete_jobs = [dict(row) for row in cursor.fetchall()]
        for job in incomplete_jobs:
            new_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")  # Default until rules are set
            conn.execute("UPDATE jobs SET status = 'NOT COMPLETED', stop_time = ?, upload_time = ?, notes = ? WHERE id = ?", 
                         (current_time, current_time, f"Moved to {new_date}", job["id"]))
            conn.execute("INSERT INTO jobs (operator_id, customer_id, address, status, start_time) VALUES (?, ?, ?, ?, ?)",
                         (job["operator_id"], job["customer_id"], job["address"], "GO", new_date))
        conn.commit()
    return {"message": "End of day completed, incomplete jobs rescheduled based on placeholder rules."}

# Requirements.txt (unchanged)
"""
fastapi
uvicorn
pydantic
fastapi-security
requests
python-multipart
"""
