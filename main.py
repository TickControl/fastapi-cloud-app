from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Tick Control, LLC API"}

# Database context manager
@contextmanager
def get_db():
    try:
        conn = sqlite3.connect('tickcontrol.db')
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
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

class Customer(BaseModel):
    id: int | None
    name: str
    phone: str | None
    address: str
    email: str | None
    service_frequency: str | None
    notes: str | None

# Endpoints
@app.get("/operators/", response_model=list[Operator])
def list_operators():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT id, name, clock_in, clock_out FROM operators")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_operators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching operators: {str(e)}")

@app.post("/login/")
def login(login: Login):
    try:
        logger.info(f"Login attempt for username: {login.username}")
        with get_db() as conn:
            cursor = conn.execute("SELECT id, name FROM operators WHERE name = ? AND password = ?", (login.username, login.password))
            operator = cursor.fetchone()
            if operator:
                logger.info(f"Operator found: {operator['name']}")
                conn.execute("UPDATE operators SET clock_in = ? WHERE id = ?", (datetime.now().isoformat(), operator['id']))
                conn.commit()
                return {"message": "Login successful", "clock_in": datetime.now().isoformat()}
            logger.warning(f"Invalid credentials for username: {login.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.put("/operators/")
def clock_out(operator_data: dict):
    try:
        with get_db() as conn:
            if "clock_out" in operator_data:
                conn.execute("UPDATE operators SET clock_out = ? WHERE name = (SELECT name FROM operators WHERE clock_in IS NOT NULL AND clock_out IS NULL LIMIT 1)", (operator_data["clock_out"],))
                conn.commit()
            return {"message": "Clock out updated"}
    except Exception as e:
        logger.error(f"Error in clock_out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating clock out: {str(e)}")

@app.post("/end_of_day/")
def end_of_day(operator_id: int):
    try:
        with get_db() as conn:
            conn.execute("UPDATE operators SET clock_out = ? WHERE id = ?", (datetime.now().isoformat(), operator_id))
            conn.commit()
            return {"message": "End of day processed"}
    except Exception as e:
        logger.error(f"Error in end_of_day: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing end of day: {str(e)}")

@app.get("/trucks/", response_model=list[Truck])
def list_trucks():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT id, name FROM trucks")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_trucks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching trucks: {str(e)}")

@app.get("/jobs/", response_model=list[Job])
def list_jobs():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT id, customer_name, phone, address, notes, status FROM jobs")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@app.put("/jobs/{job_id}/status")
def update_job_status(job_id: int, status_data: dict):
    try:
        with get_db() as conn:
            if "status" in status_data:
                conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status_data["status"], job_id))
                conn.commit()
            return {"message": "Job status updated"}
    except Exception as e:
        logger.error(f"Error in update_job_status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating job status: {str(e)}")

@app.get("/calendar/")
def get_calendar(month_year: str):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT COUNT(*) as jobs_left FROM jobs WHERE status != 'COMPLETED'")
            jobs_left = cursor.fetchone()[0]
            return {"month_year": month_year, "jobs_left": jobs_left}
    except Exception as e:
        logger.error(f"Error in get_calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching calendar: {str(e)}")

@app.post("/truck_maintenance/")
def add_maintenance(maintenance: Maintenance):
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO truck_maintenance (truck_id, maintenance_type, mileage, performer) VALUES (?, ?, ?, ?)",
                         (maintenance.truck_id, maintenance.maintenance_type, maintenance.mileage, maintenance.performer))
            conn.commit()
            return {"message": "Maintenance record added"}
    except Exception as e:
        logger.error(f"Error in add_maintenance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding maintenance record: {str(e)}")

@app.get("/settings/call_number")
def get_call_number():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = 'call_number'")
            result = cursor.fetchone()
            return {"call_number": result[0] if result else "555-123-4567"}
    except Exception as e:
        logger.error(f"Error in get_call_number: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching call number: {str(e)}")

# Customer Endpoints
@app.get("/customers/", response_model=list[Customer])
def list_customers():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT id, name, phone, address, email, service_frequency, notes FROM customers")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_customers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {str(e)}")

@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT id, name, phone, address, email, service_frequency, notes FROM customers WHERE id = ?", (customer_id,))
            customer = cursor.fetchone()
            if customer:
                return dict(customer)
            raise HTTPException(status_code=404, detail="Customer not found")
    except Exception as e:
        logger.error(f"Error in get_customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching customer: {str(e)}")

@app.post("/customers/", response_model=Customer)
def create_customer(customer: Customer):
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO customers (name, phone, address, email, service_frequency, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (customer.name, customer.phone, customer.address, customer.email, customer.service_frequency, customer.notes)
            )
            conn.commit()
            customer_id = cursor.lastrowid
            return {**customer.dict(), "id": customer_id}
    except Exception as e:
        logger.error(f"Error in create_customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")

@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer: Customer):
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE customers SET name = ?, phone = ?, address = ?, email = ?, service_frequency = ?, notes = ? WHERE id = ?",
                (customer.name, customer.phone, customer.address, customer.email, customer.service_frequency, customer.notes, customer_id)
            )
            conn.commit()
            return {**customer.dict(), "id": customer_id}
    except Exception as e:
        logger.error(f"Error in update_customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")

# Initialize database (run once or on startup if needed)
def init_db():
    try:
        # Log database file status
        db_file = 'tickcontrol.db'
        if os.path.exists(db_file):
            logger.info(f"Database file {db_file} exists")
        else:
            logger.info(f"Database file {db_file} does not exist, creating it")

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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT NOT NULL,
                    email TEXT,
                    service_frequency TEXT,
                    notes TEXT
                )
            """)
            # Insert sample data if not exists
            conn.execute("INSERT OR IGNORE INTO operators (name, password) VALUES (?, ?)", ("Jacob", "password123"))
            conn.execute("INSERT OR IGNORE INTO trucks (name) VALUES (?)", ("Truck 1",))
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("call_number", "555-123-4567"))
            conn.execute("INSERT OR IGNORE INTO customers (name, phone, address, email, service_frequency, notes) VALUES (?, ?, ?, ?, ?, ?)",
                         ("John Doe", "555-987-6543", "123 Tick St", "john@example.com", "30 days", "Prefers morning service"))
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing database: {str(e)}")

# Run database initialization on startup
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
