from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List
from uuid import uuid4, UUID
from datetime import datetime
import pytz
import sqlite3
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

IST = pytz.timezone('Asia/Kolkata')

# SQLite in-memory DB setup
conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE classes (
    id TEXT PRIMARY KEY,
    name TEXT,
    datetime TEXT,
    instructor TEXT,
    available_slots INTEGER
)
''')

cursor.execute('''
CREATE TABLE bookings (
    id TEXT PRIMARY KEY,
    class_id TEXT,
    client_name TEXT,
    client_email TEXT,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
''')
conn.commit()

# Models
class FitnessClassCreate(BaseModel):
    name: str
    dateTime: str  # ISO 8601, e.g., "2025-06-15T10:00:00"
    instructor: str
    availableSlots: int

class BookingCreate(BaseModel):
    class_id: UUID
    client_name: str
    client_email: EmailStr

class FitnessClassOut(BaseModel):
    id: UUID
    name: str
    dateTime: str
    instructor: str
    availableSlots: int

class BookingOut(BaseModel):
    id: UUID
    class_id: UUID
    client_name: str
    client_email: EmailStr

# Endpoints

@app.post("/classes")
def create_class(data: FitnessClassCreate):
    try:
        class_id = str(uuid4())
        local_time = IST.localize(datetime.fromisoformat(data.dateTime))
        utc_time = local_time.astimezone(pytz.utc)
        cursor.execute('''
            INSERT INTO classes (id, name, datetime, instructor, available_slots)
            VALUES (?, ?, ?, ?, ?)
        ''', (class_id, data.name, utc_time.isoformat(), data.instructor, data.availableSlots))
        conn.commit()
        return {"id": class_id}
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=400, detail="Invalid data format or internal error")

@app.get("/classes", response_model=List[FitnessClassOut])
def get_classes():
    cursor.execute('SELECT * FROM classes')
    rows = cursor.fetchall()
    result = []
    for row in rows:
        local_time = pytz.utc.localize(datetime.fromisoformat(row[2])).astimezone(IST)
        result.append({
            "id": row[0],
            "name": row[1],
            "dateTime": local_time.isoformat(),
            "instructor": row[3],
            "availableSlots": row[4]
        })
    return result

@app.post("/book")
def book_class(data: BookingCreate):
    cursor.execute('SELECT available_slots FROM classes WHERE id = ?', (str(data.class_id),))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Class not found")
    if row[0] <= 0:
        raise HTTPException(status_code=400, detail="No slots available")
    
    booking_id = str(uuid4())
    cursor.execute('''
        INSERT INTO bookings (id, class_id, client_name, client_email)
        VALUES (?, ?, ?, ?)
    ''', (booking_id, str(data.class_id), data.client_name, data.client_email))
    
    cursor.execute('''
        UPDATE classes SET available_slots = available_slots - 1 WHERE id = ?
    ''', (str(data.class_id),))
    conn.commit()
    return {"booking_id": booking_id}

@app.get("/bookings", response_model=List[BookingOut])
def get_bookings(email: EmailStr):
    cursor.execute('SELECT * FROM bookings WHERE client_email = ?', (email,))
    rows = cursor.fetchall()
    return [{
        "id": row[0],
        "class_id": row[1],
        "client_name": row[2],
        "client_email": row[3]
    } for row in rows]
