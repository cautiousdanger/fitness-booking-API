
from pydantic import BaseModel, EmailStr
from uuid import UUID

class FitnessClassCreate(BaseModel):
    name: str
    dateTime: str
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
