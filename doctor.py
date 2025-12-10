
from src.models.person import Person
from enum import Enum
from typing import List, Optional

# Example of Doctor model
class MedicalSpecialty(Enum):
    GENERAL = "General"
    ORTHODONTIST = "Orthodontist"
    PEDIATRIC = "Pediatric"
    SURGEON = "Oral Surgeon"

class Doctor(Person):
    license_number: str
    specialty: MedicalSpecialty
