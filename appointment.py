"""
Appointment Model

This module defines the Appointment class with booking management,
status tracking, and reminder functionality.

Features:
- Appointment status lifecycle
- DateTime validation
- Service type enumeration
- Automatic confirmation reminders
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
from enum import Enum


class AppointmentStatus(str, Enum):
    """Possible states of an appointment."""
    SCHEDULED = "Scheduled"
    CONFIRMED = "Confirmed"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"
    RESCHEDULED = "Rescheduled"


class ServiceType(str, Enum):
    """Types of dental services available."""
    CONSULTATION = "Consultation"
    CLEANING = "Cleaning"
    FILLING = "Filling"
    ROOT_CANAL = "Root Canal"
    EXTRACTION = "Extraction"
    ORTHODONTICS = "Orthodontics"
    WHITENING = "Whitening"
    IMPLANT = "Implant"
    CROWN = "Crown"
    EMERGENCY = "Emergency"
    OTHER = "Other"


class Appointment(BaseModel):
    """
    Appointment model representing a scheduled dental visit.
    
    Attributes:
        id: Unique appointment identifier
        patient_name: Name of the patient
        patient_phone: Patient's contact number
        doctor_name: Name of the dentist
        date: Appointment date (YYYY-MM-DD)
        time: Appointment time (HH:MM)
        service_type: Type of dental service
        status: Current status of appointment
        notes: Additional notes or special requirements
        created_at: When appointment was created
        reminder_sent: Whether reminder notification was sent
        duration_minutes: Expected duration of appointment
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8], alias="_id")
    patient_name: str = Field(..., min_length=1, max_length=100)
    patient_phone: str = Field(..., min_length=7, max_length=20)
    doctor_name: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., description="Format: YYYY-MM-DD")
    time: str = Field(..., description="Format: HH:MM")
    service_type: ServiceType = Field(default=ServiceType.CONSULTATION)
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
    reminder_sent: bool = Field(default=False)
    duration_minutes: int = Field(default=30, ge=15, le=180)
    cancellation_reason: Optional[str] = Field(default=None, max_length=200)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format and ensure it's in the future."""
        try:
            date_obj = datetime.strptime(v, "%Y-%m-%d")
            # Appointments must be at least 1 hour in the future
            if date_obj.date() < datetime.now().date():
                raise ValueError('Appointment date must be in the future')
            return v
        except ValueError as e:
            raise ValueError(f'Date must be in YYYY-MM-DD format. Error: {str(e)}')

    @field_validator('time')
    @classmethod
    def validate_time(cls, v):
        """Validate time format."""
        try:
            datetime.strptime(v, "%H:%M")
            # Ensure time is during business hours (08:00 - 20:00)
            hour = int(v.split(':')[0])
            if hour < 8 or hour >= 20:
                raise ValueError('Appointments must be scheduled between 08:00 and 20:00')
            return v
        except ValueError as e:
            raise ValueError(f'Time must be in HH:MM format (08:00-20:00). Error: {str(e)}')

    def get_datetime(self) -> datetime:
        """Return combined datetime object."""
        return datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")

    def is_upcoming(self) -> bool:
        """Check if appointment is in the future."""
        return self.get_datetime() > datetime.now()

    def is_overdue(self) -> bool:
        """Check if appointment time has passed without completion."""
        if self.status == AppointmentStatus.COMPLETED:
            return False
        return self.get_datetime() < datetime.now()

    def remind_soon(self) -> bool:
        """Check if appointment is within 24 hours."""
        appointment_time = self.get_datetime()
        time_until_appointment = appointment_time - datetime.now()
        return timedelta(0) < time_until_appointment <= timedelta(hours=24)

    def confirm(self) -> None:
        """Confirm the appointment."""
        if self.status == AppointmentStatus.SCHEDULED:
            self.status = AppointmentStatus.CONFIRMED

    def cancel(self, reason: str = "No reason provided") -> None:
        """Cancel the appointment with optional reason."""
        if self.status not in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            self.status = AppointmentStatus.CANCELLED
            self.cancellation_reason = reason

    def mark_completed(self) -> None:
        """Mark appointment as completed."""
        if self.is_overdue():
            self.status = AppointmentStatus.COMPLETED

    def __str__(self) -> str:
        """String representation."""
        return (f"Appointment: {self.patient_name} with Dr. {self.doctor_name} "
                f"on {self.date} at {self.time} ({self.status})")

    def __repr__(self) -> str:
        """Developer representation."""
        return f"Appointment({self.id})"
