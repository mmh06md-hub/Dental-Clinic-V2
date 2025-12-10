from src.models.person import Person
from typing import List, Optional
from pydantic import Field
from enum import Enum

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class EmergencyContact(Person):
    relationship: str
    id: Optional[str] = None
    first_name: str
    last_name: str
    phone: str

class Patient(Person):
    age: int = Field(gt=0, lt=150)
    gender: Gender  # Uses the Enum
    blood_type: Optional[str] = None
    medical_history: List[str] = [] 
    emergency_contact: Optional[EmergencyContact] = None