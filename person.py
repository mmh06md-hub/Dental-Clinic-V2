from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

class Person(BaseModel):
    """
    Base Person class for Doctor/Patient inheritance.
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8], alias="_id")
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
