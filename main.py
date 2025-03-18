# Add to tables in startup
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
# Initialize sample trucks
cursor = conn.execute("SELECT COUNT(*) FROM trucks")
if cursor.fetchone()[0] == 0:
    conn.execute("INSERT INTO trucks (name, status) VALUES (?, ?)", ("TICK 1", "Available"))
    conn.execute("INSERT INTO trucks (name, status) VALUES (?, ?)", ("TICK 2", "Available"))
    conn.execute("INSERT INTO trucks (name, status) VALUES (?, ?)", ("TICK 3", "Available"))
    conn.commit()

# New models
class Truck(BaseModel):
    name: str
    status: str = "Available"
    oil_change_date: str = None
    tire_status: str = None
    def_level: str = None
    emissions_date: str = None
    insurance_date: str = None
    gas_type: str = None

# New endpoints
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
