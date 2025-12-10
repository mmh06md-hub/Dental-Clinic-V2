🏥 Dental Clinic Management System V2 – MongoDB Edition
📄 Overview

A Python-based console application that manages doctors, patients, appointments, and reviews for a dental clinic.

This version expands the foundational code into a full backend structure, using:

Object-Oriented Programming

Modular service architecture

MongoDB storage

Pydantic models

Logging and exception handling

Designed to resemble how a real system would be built in production.

⚙️ Features
👩‍⚕️ Doctors

Add new doctor (name, specialty, phone, email)

Stored in database

Search by name or specialty

Rating updates from patient reviews

🧍 Patients

Register patients with personal and medical info

Emergency contact structure

Search by name, phone, email, or doctor

📅 Appointments

Schedule appointments with date, time, and service

Cancel with reason

Prevent conflicts

View by doctor or all

⭐ Reviews

Add reviews for doctors

Update doctor rating dynamically

View doctor reviews

🧠 Concepts Demonstrated (New Additions)

This project integrates multiple concepts from the lectures, not just basic Python.

🧩 Modular Design & Layered Architecture

The project is split into layers:

config → database connection
models → data structures
services → business logic
main → user interface


Each layer has a single responsibility, making the system cleaner, scalable, and easier to maintain.

📦 Data Models with Validation (Pydantic)

Doctor, Patient, Appointment, and Review are typed models:

Fields are validated automatically

Invalid data is rejected before reaching the database

Dates, phone formats, and enums are enforced

Example:

appointment = Appointment(
    patient_name="John",
    doctor_name="Dr. Sara",
    date="2025-02-20",
    time="10:00"
)


This ensures data integrity.

🗄️ Database Integration (MongoDB)

Instead of saving to JSON files, all data is now stored permanently in MongoDB.

Benefits:

Fast queries

Advanced filtering

No file corruption

Shared access

Collections used:

doctors

patients

appointments

reviews

🚨 Error Handling & Logging

The application uses structured logging:

logger.info("[OK] Appointment booked")
logger.error("[FAIL] Database not connected")


This makes debugging easier and mimics real-world production systems.

🔐 Safe Fallback Mode

If MongoDB is not running, the program does not crash — it runs in a limited mode:

if self.db is None:
    logger.warning("[WARN] Database connection failed. Running in limited mode.")


This demonstrates:

defensive programming

availability even during failures

📊 Statistics & Computation

The system calculates live statistics:

number of doctors

number of patients

number of appointments

upcoming appointments

This shows how a service layer can aggregate data across multiple sources.

🗄️ Database Structure
clinic_db/
 ├─ doctors
 ├─ patients
 ├─ appointments
 └─ reviews


Each collection stores typed documents with unique IDs, timestamps, and relationships.

▶️ How to Run
1. Start MongoDB
mongod

2. Run the program
python main.py

3. Use the menu to:

Add doctor/patient

Book appointment

Cancel appointment

View lists and statistics

🧰 Technologies Used
Component	Usage
Python	core application
MongoDB	storage
Pydantic	typed models & validation
Logging	structured messages
Datetime	scheduling
UUID	unique IDs
Enums	status & categories
📚 Author

Developed for educational purposes in the Advanced Python course.
All rights reserved for academic evaluation
