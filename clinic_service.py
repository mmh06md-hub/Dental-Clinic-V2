# src/services/clinic_service.py
from typing import List, Optional
from src.models.doctor import Doctor, MedicalSpecialty
from src.models.patient import Patient

class ClinicService:
    """Service layer for Dental Clinic Management."""

    def __init__(self):
        self._doctors: List[Doctor] = []
        self._patients: List[Patient] = []

    # -------- Doctor Methods --------
    def add_doctor(self, doctor: Doctor) -> bool:
        """Add a new doctor if license number is unique."""
        if any(d.license_number == doctor.license_number for d in self._doctors):
            return False  # Duplicate license
        self._doctors.append(doctor)
        return True

    def get_all_doctors(self) -> List[Doctor]:
        """Return all doctors."""
        return self._doctors

    def find_doctor(self, search_term: str) -> List[Doctor]:
        """Find doctors by name or license."""
        term = search_term.lower()
        return [
            d for d in self._doctors
            if term in d.first_name.lower() or term in d.last_name.lower() or term in d.license_number.lower()
        ]

    # -------- Patient Methods --------
    def add_patient(self, patient: Patient) -> bool:
        """Add a new patient."""
        if any(p.full_name == patient.full_name and p.age == patient.age for p in self._patients):
            return False  # Duplicate patient
        self._patients.append(patient)
        return True

    def get_all_patients(self) -> List[Patient]:
        """Return all patients."""
        return self._patients

    def find_patient(self, search_term: str) -> List[Patient]:
        """Find patients by name or phone."""
        term = search_term.lower()
        return [
            p for p in self._patients
            if term in p.first_name.lower() 
            or term in p.last_name.lower() 
            or term in (p.phone.lower() if p.phone else "")
        ]

    # -------- Clinic Stats --------
    def get_clinic_stats(self) -> dict:
        """Return simple clinic statistics."""
        return {
            "total_doctors": len(self._doctors),
            "total_patients": len(self._patients)
        }
