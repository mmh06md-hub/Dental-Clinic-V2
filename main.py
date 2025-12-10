"""
Main CLI Entry Point - Dental Clinic Management System (Clean Version)
"""

import sys
import logging
from typing import Optional
from dataclasses import dataclass
from abc import ABC

from src.services.clinic_service import ClinicService
from src.services.chatbot_service import ChatBotService
from src.models.doctor import Doctor, MedicalSpecialty
from src.models.patient import Patient, EmergencyContact, Gender

# ===== Logging Setup =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ===== Utility Functions =====
def safe_int_input(prompt: str, default: Optional[int] = None) -> int:
    while True:
        try:
            value = input(prompt).strip()
            if not value and default is not None:
                return default
            return int(value)
        except ValueError:
            print("Invalid number. Try again!")

def safe_email_input(prompt: str) -> Optional[str]:
    while True:
        email = input(prompt).strip()
        if not email:
            return None
        if "@" in email and "." in email:
            return email
        print("Invalid email format. Try again or leave blank.")

# ===== Base Person Class =====
@dataclass
class Person(ABC):
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

# ===== Clinic CLI =====
class ClinicCLI:
    def __init__(self):
        self.clinic = ClinicService()
        self.bot = ChatBotService()

    # ----- Doctor Methods -----
    def add_doctor_cli(self):
        print("\n--- Add New Doctor ---")
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        license_number = input("License Number: ").strip()
        phone = input("Phone: ").strip()
        email = safe_email_input("Email (optional): ")

        print("\nSpecialties:")
        for i, spec in enumerate(MedicalSpecialty, 1):
            print(f"  {i}. {spec.value}")
        spec_choice = safe_int_input("Select specialty (number): ")
        spec_list = list(MedicalSpecialty)
        if 1 <= spec_choice <= len(spec_list):
            specialty = spec_list[spec_choice - 1]
        else:
            print("Invalid specialty selection.")
            return

        new_doc = Doctor(
            first_name=first_name,
            last_name=last_name,
            license_number=license_number,
            phone=phone,
            email=email,
            specialty=specialty
        )

        if self.clinic.add_doctor(new_doc):
            print(f"✔️ Doctor {new_doc.full_name} added successfully!")
        else:
            print("❌ Failed to add doctor.")

    # ----- Patient Methods -----
    def register_patient_cli(self):
        print("\n--- Register New Patient ---")
        f_name = input("First Name: ").strip()
        l_name = input("Last Name: ").strip()
        age = safe_int_input("Age: ")
        if age < 0 or age > 150:
            print("Age must be between 0 and 150")
            return

        print("\nGender:")
        for i, gen in enumerate(Gender, 1):
            print(f"  {i}. {gen.value}")
        gender_choice = safe_int_input("Select gender (number): ")
        gender_list = list(Gender)
        if 1 <= gender_choice <= len(gender_list):
            gender = gender_list[gender_choice - 1]
        else:
            print("❌ Invalid gender selection.")
            return

        phone = input("Phone: ").strip()

        print("\n--- Emergency Contact ---")
        ec_f_name = input("Contact First Name: ").strip()
        ec_l_name = input("Contact Last Name: ").strip()
        ec_phone = input("Contact Phone: ").strip()
        ec_email = safe_email_input("Contact Email (optional): ")
        ec_relationship = input("Relationship: ").strip()

        ec = EmergencyContact(
            first_name=ec_f_name,
            last_name=ec_l_name,
            phone=ec_phone,
            email=ec_email,
            relationship=ec_relationship
        )

        new_pat = Patient(
            first_name=f_name,
            last_name=l_name,
            age=age,
            gender=gender,
            phone=phone,
            emergency_contact=ec
        )

        if self.clinic.add_patient(new_pat):
            print(f"✔️ Patient {new_pat.full_name} registered successfully!")
        else:
            print("❌ Failed to register patient.")

    # ----- Listing Methods -----
    def list_doctors_cli(self):
        doctors = self.clinic.get_all_doctors()
        if not doctors:
            print("📭 No doctors found.")
        else:
            print("\n--- DOCTORS LIST ---")
            for i, d in enumerate(doctors, 1):
                print(f"{i}. Dr. {d.full_name} | {d.specialty.value} | {d.phone}")

    def list_patients_cli(self):
        patients = self.clinic.get_all_patients()
        if not patients:
            print("📭 No patients found.")
        else:
            print("\n--- PATIENTS LIST ---")
            for i, p in enumerate(patients, 1):
                print(f"{i}. {p.full_name} | Age: {p.age} | {p.phone}")

    # ----- Search Methods -----
    def search_patient_cli(self):
        term = input("Enter name or phone: ").strip()
        results = self.clinic.find_patient(term)
        if not results:
            print("❌ No match found.")
        else:
            print(f"✔️ Found {len(results)} result(s):")
            for p in results:
                print(f"• {p.full_name} | Phone: {p.phone}")

    # ----- AI Chat -----
    def ai_chat_cli(self):
        print("\nAI Assistant (type 'exit' to stop)")
        name = input("Your name: ").strip() or "Guest"
        while True:
            msg = input("You: ").strip()
            if msg.lower() == "exit":
                print("👋 Bye!")
                break
            reply = self.bot.get_response(msg, name)
            print("Assistant:", reply)

    # ----- Clinic Stats -----
    def clinic_stats_cli(self):
        stats = self.clinic.get_clinic_stats()
        print("\n--- CLINIC STATS ---")
        print(stats)

    # ===== Main Loop =====
    def run(self):
        while True:
            print("\n" + "=" * 50)
            print(" DENTAL CLINIC MANAGER V2 ")
            print("=" * 50)
            print("1. Add New Doctor")
            print("2. Register New Patient")
            print("3. List All Doctors")
            print("4. List All Patients")
            print("5. Search Patient")
            print("6. AI Assistant (Chat)")
            print("7. Clinic Statistics")
            print("8. Exit")
            choice = input("\nSelect Option (1-8): ").strip()

            options = {
                "1": self.add_doctor_cli,
                "2": self.register_patient_cli,
                "3": self.list_doctors_cli,
                "4": self.list_patients_cli,
                "5": self.search_patient_cli,
                "6": self.ai_chat_cli,
                "7": self.clinic_stats_cli
            }

            if choice == "8":
                print("👋 Goodbye!")
                break
            elif choice in options:
                try:
                    options[choice]()
                except Exception as e:
                    logging.error(f"Error executing option {choice}: {e}")
            else:
                print("❌ Invalid choice. Select 1-8.")

# ===== Main Entry =====
if __name__ == "__main__":
    try:
        cli = ClinicCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        logging.critical(f"Critical Error: {e}")
        sys.exit(1)
