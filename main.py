# Add to tables in startup
conn.execute("""
    ALTER TABLE jobs ADD COLUMN IF NOT EXISTS upload_time TEXT
""")  # Add upload_time if not exists
# Update jobs model and endpoint
class Job(BaseModel):
    operator_id: int
    customer_id: int
    address: str
    status: str = "GO"
    start_time: str = None
    stop_time: str = None
    photo_url: str = None
    upload_time: str = None

@app.put("/jobs/{job_id}/status")
def update_job_status(job_id: int, status: str, photo_url: str = None):
    with get_db() as conn:
        current_time = "datetime('now')"
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

# Update trucks with attributes
class Truck(BaseModel):
    name: str
    status: str = "Available"
    oil_change_date: str = "N/A"
    tire_status: str = "N/A"
    def_level: str = "N/A"
    emissions_date: str = "N/A"
    insurance_date: str = "N/A"
    gas_type: str = "diesel"
