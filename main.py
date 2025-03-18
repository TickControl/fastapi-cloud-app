# Add to tables in startup
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

# New model
class TruckMaintenance(BaseModel):
    truck_id: int
    maintenance_type: str
    mileage: int
    status: str = "Pending"
    photo_url: str = None
    upload_time: str = None
    performer: str = None

# New endpoint
@app.post("/truck_maintenance/", response_model=TruckMaintenance)
def add_maintenance(maintenance: TruckMaintenance):
    with get_db() as conn:
        current_time = "datetime('now')"
        cursor = conn.execute(
            "INSERT INTO truck_maintenance (truck_id, maintenance_type, mileage, status, photo_url, upload_time, performer) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (maintenance.truck_id, maintenance.maintenance_type, maintenance.mileage, maintenance.status, maintenance.photo_url, current_time, maintenance.performer)
        )
        conn.commit()
        return {"id": cursor.lastrowid, **maintenance.dict()}
