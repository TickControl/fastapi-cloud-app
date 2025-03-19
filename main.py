from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import logging
from cryptography.fernet import Fernet
import base64
import os  # Added for environment variable

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

# Encryption setup for credit cards
key = Fernet.generate_key()
cipher = Fernet(key)

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
    customer_id: int
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
    status: str
    start_date: str | None
    free_resprays: int
    has_pets: int
    has_water: int
    left_review: int
    friendliness: float
    ease_of_work: float
    timeliness_payment: float
    likelihood_stay: float
    trustworthiness: float
    payment_method: str | None

class Invoice(BaseModel):
    id: int | None
    customer_id: int
    spray_id: int | None
    date: str
    invoice_number: str
    amount: float
    payment_method: str | None
    payment_date: str | None
    amount_due: float
    current_age: int

class CreditCard(BaseModel):
    id: int | None
    customer_id: int
    date_added: str
    name_on_card: str
    card_number: str
    expiry: str
    cvv: str
    zip_code: str
    use_debit: int

class InternalNote(BaseModel):
    id: int | None
    customer_id: int
    date: str
    operator: str
    content: str
    priority: str

class OperatorInstruction(BaseModel):
    id: int | None
    customer_id: int
    date: str
    content: str

class Spray(BaseModel):
    id: int | None
    customer_id: int
    date: str
    time: str
    operator: str
    type: str
    test: str
    pesticide: str
    epa: str
    precautionary: str
    concentration: float
    gallons: float
    milliliters: float
    square_feet: float

class Contract(BaseModel):
    id: int | None
    customer_id: int
    file_path: str

# Operator Endpoints
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

# Truck Endpoints
@app.get("/trucks/", response_model=list[Truck])
def list_trucks():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT id, name FROM trucks")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_trucks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching trucks: {str(e)}")

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

# Job Endpoints
@app.get("/jobs/", response_model=list[Job])
def list_jobs():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT id, customer_id, customer_name, phone, address, notes, status FROM jobs")
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

# Calendar Endpoint
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

# Customer Endpoints
@app.get("/customers/", response_model=list[Customer])
def list_customers():
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM customers")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_customers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {str(e)}")

@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
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
                "INSERT INTO customers (name, phone, address, email, service_frequency, notes, status, start_date, free_resprays, has_pets, has_water, left_review, friendliness, ease_of_work, timeliness_payment, likelihood_stay, trustworthiness, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (customer.name, customer.phone, customer.address, customer.email, customer.service_frequency, customer.notes, customer.status, customer.start_date, customer.free_resprays, customer.has_pets, customer.has_water, customer.left_review, customer.friendliness, customer.ease_of_work, customer.timeliness_payment, customer.likelihood_stay, customer.trustworthiness, customer.payment_method)
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
                "UPDATE customers SET name = ?, phone = ?, address = ?, email = ?, service_frequency = ?, notes = ?, status = ?, start_date = ?, free_resprays = ?, has_pets = ?, has_water = ?, left_review = ?, friendliness = ?, ease_of_work = ?, timeliness_payment = ?, likelihood_stay = ?, trustworthiness = ?, payment_method = ? WHERE id = ?",
                (customer.name, customer.phone, customer.address, customer.email, customer.service_frequency, customer.notes, customer.status, customer.start_date, customer.free_resprays, customer.has_pets, customer.has_water, customer.left_review, customer.friendliness, customer.ease_of_work, customer.timeliness_payment, customer.likelihood_stay, customer.trustworthiness, customer.payment_method, customer_id)
            )
            conn.commit()
            return {**customer.dict(), "id": customer_id}
    except Exception as e:
        logger.error(f"Error in update_customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")

# Invoice Endpoints
@app.get("/invoices/customer/{customer_id}", response_model=list[Invoice])
def list_invoices(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM invoices WHERE customer_id = ?", (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching invoices: {str(e)}")

@app.put("/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, status_data: dict):
    try:
        with get_db() as conn:
            if "payment_date" in status_data and "payment_method" in status_data:
                conn.execute("UPDATE invoices SET payment_date = ?, payment_method = ?, amount_due = 0, current_age = 0 WHERE id = ?",
                             (status_data["payment_date"], status_data["payment_method"], invoice_id))
                conn.commit()
            return {"message": "Invoice status updated"}
    except Exception as e:
        logger.error(f"Error in update_invoice_status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating invoice status: {str(e)}")

# Credit Card Endpoints
@app.get("/credit_cards/customer/{customer_id}", response_model=list[CreditCard])
def list_credit_cards(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM credit_cards WHERE customer_id = ?", (customer_id,))
            cards = [dict(row) for row in cursor.fetchall()]
            for card in cards:
                card["card_number"] = cipher.decrypt(base64.b64decode(card["card_number"])).decode()
                card["cvv"] = cipher.decrypt(base64.b64decode(card["cvv"])).decode()
            return cards
    except Exception as e:
        logger.error(f"Error in list_credit_cards: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching credit cards: {str(e)}")

@app.post("/credit_cards/", response_model=CreditCard)
def create_credit_card(credit_card: CreditCard):
    try:
        with get_db() as conn:
            encrypted_card_number = base64.b64encode(cipher.encrypt(credit_card.card_number.encode())).decode()
            encrypted_cvv = base64.b64encode(cipher.encrypt(credit_card.cvv.encode())).decode()
            cursor = conn.execute(
                "INSERT INTO credit_cards (customer_id, date_added, name_on_card, card_number, expiry, cvv, zip_code, use_debit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (credit_card.customer_id, credit_card.date_added, credit_card.name_on_card, encrypted_card_number, credit_card.expiry, encrypted_cvv, credit_card.zip_code, credit_card.use_debit)
            )
            conn.commit()
            credit_card_id = cursor.lastrowid
            return {**credit_card.dict(), "id": credit_card_id}
    except Exception as e:
        logger.error(f"Error in create_credit_card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating credit card: {str(e)}")

@app.delete("/credit_cards/{credit_card_id}")
def delete_credit_card(credit_card_id: int):
    try:
        with get_db() as conn:
            conn.execute("DELETE FROM credit_cards WHERE id = ?", (credit_card_id,))
            conn.commit()
            return {"message": "Credit card deleted"}
    except Exception as e:
        logger.error(f"Error in delete_credit_card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting credit card: {str(e)}")

# Internal Note Endpoints
@app.get("/internal_notes/customer/{customer_id}", response_model=list[InternalNote])
def list_internal_notes(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM internal_notes WHERE customer_id = ?", (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_internal_notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching internal notes: {str(e)}")

@app.post("/internal_notes/", response_model=InternalNote)
def create_internal_note(note: InternalNote):
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO internal_notes (customer_id, date, operator, content, priority) VALUES (?, ?, ?, ?, ?)",
                (note.customer_id, note.date, note.operator, note.content, note.priority)
            )
            conn.commit()
            note_id = cursor.lastrowid
            return {**note.dict(), "id": note_id}
    except Exception as e:
        logger.error(f"Error in create_internal_note: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating internal note: {str(e)}")

# Operator Instruction Endpoints
@app.get("/operator_instructions/customer/{customer_id}", response_model=list[OperatorInstruction])
def list_operator_instructions(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM operator_instructions WHERE customer_id = ?", (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_operator_instructions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching operator instructions: {str(e)}")

@app.post("/operator_instructions/", response_model=OperatorInstruction)
def create_operator_instruction(instruction: OperatorInstruction):
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO operator_instructions (customer_id, date, content) VALUES (?, ?, ?)",
                (instruction.customer_id, instruction.date, instruction.content)
            )
            conn.commit()
            instruction_id = cursor.lastrowid
            return {**instruction.dict(), "id": instruction_id}
    except Exception as e:
        logger.error(f"Error in create_operator_instruction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating operator instruction: {str(e)}")

# Spray Endpoints
@app.get("/sprays/customer/{customer_id}", response_model=list[Spray])
def list_sprays(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM sprays WHERE customer_id = ?", (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_sprays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching sprays: {str(e)}")

# Contract Endpoints
@app.get("/contracts/customer/{customer_id}", response_model=list[Contract])
def list_contracts(customer_id: int):
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM contracts WHERE customer_id = ?", (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in list_contracts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching contracts: {str(e)}")

# Settings Endpoint
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

# Database Initialization
def init_db():
    try:
        with get_db() as conn:
            # Existing tables
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
                    customer_id INTEGER,
                    customer_name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT NOT NULL,
                    notes TEXT,
                    status TEXT NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
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
            # Updated customers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT NOT NULL,
                    email TEXT,
                    service_frequency TEXT,
                    notes TEXT,
                    status TEXT,
                    start_date TEXT,
                    free_resprays INTEGER,
                    has_pets INTEGER,
                    has_water INTEGER,
                    left_review INTEGER,
                    friendliness FLOAT,
                    ease_of_work FLOAT,
                    timeliness_payment FLOAT,
                    likelihood_stay FLOAT,
                    trustworthiness FLOAT,
                    payment_method TEXT
                )
            """)
            # New tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    spray_id INTEGER,
                    date TEXT,
                    invoice_number TEXT,
                    amount FLOAT,
                    payment_method TEXT,
                    payment_date TEXT,
                    amount_due FLOAT,
                    current_age INTEGER,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (spray_id) REFERENCES sprays(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credit_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    date_added TEXT,
                    name_on_card TEXT,
                    card_number TEXT,
                    expiry TEXT,
                    cvv TEXT,
                    zip_code TEXT,
                    use_debit INTEGER,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS internal_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    date TEXT,
                    operator TEXT,
                    content TEXT,
                    priority TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operator_instructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    date TEXT,
                    content TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sprays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    date TEXT,
                    time TEXT,
                    operator TEXT,
                    type TEXT,
                    test TEXT,
                    pesticide TEXT,
                    epa TEXT,
                    precautionary TEXT,
                    concentration FLOAT,
                    gallons FLOAT,
                    milliliters FLOAT,
                    square_feet FLOAT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    file_path TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            # Sample data
            conn.execute("INSERT OR IGNORE INTO operators (name, password) VALUES (?, ?)", ("Jacob", "password123"))
            conn.execute("INSERT OR IGNORE INTO trucks (name) VALUES (?)", ("Truck 1",))
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("call_number", "555-123-4567"))
            conn.execute("INSERT OR IGNORE INTO customers (name, phone, address, email, service_frequency, notes, status, start_date, free_resprays, has_pets, has_water, left_review, friendliness, ease_of_work, timeliness_payment, likelihood_stay, trustworthiness, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         ("Joe Smith", "203-555-5555", "1234 East Main Street, Greenwich, CT 06830", "joesmith@gmail.com", "30 days", "Prefers morning service", "INACTIVE", "2024-09-24", 1, 1, 1, 1, 4.35, 4.75, 2.0, 4.0, 5.0, "MONTHLY CREDIT CARD 1-15 DOG"))
            conn.execute("INSERT OR IGNORE INTO invoices (customer_id, date, invoice_number, amount, payment_method, payment_date, amount_due, current_age) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (1, "2024-10-20", "12345", 103.36, "NA", "NOT YET", 127.72, 7))
            encrypted_card_number = base64.b64encode(cipher.encrypt("1234123412341234".encode())).decode()
            encrypted_cvv = base64.b64encode(cipher.encrypt("477".encode())).decode()
            conn.execute("INSERT OR IGNORE INTO credit_cards (customer_id, date_added, name_on_card, card_number, expiry, cvv, zip_code, use_debit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (1, "2024-04-09", "JOE SMITH", encrypted_card_number, "10/25", encrypted_cvv, "06811", 1))
            conn.execute("INSERT OR IGNORE INTO internal_notes (customer_id, date, operator, content, priority) VALUES (?, ?, ?, ?, ?)",
                         (1, "2024-04-09", "Jacob", "Said they want it next week instead.", "LOW"))
            conn.execute("INSERT OR IGNORE INTO operator_instructions (customer_id, date, content) VALUES (?, ?, ?)",
                         (1, "2024-04-09", "Spray under the front porch."))
            conn.execute("INSERT OR IGNORE INTO sprays (customer_id, date, time, operator, type, test, pesticide, epa, precautionary, concentration, gallons, milliliters, square_feet) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (1, "2024-10-09", "10:30", "JEFF", "FULL", "HUNTER", "PERMANONE", "EPA 432-183", "CAUTION", 0.05, 133.6, 122.2, 145000))
            conn.execute("INSERT OR IGNORE INTO contracts (customer_id, file_path) VALUES (?, ?)",
                         (1, "/path/to/contract.pdf"))
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing database: {str(e)}")

@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Use PORT env var, default to 8000
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
