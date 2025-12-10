# Dental Clinic Management System v2.0

Professional Python/MongoDB dental clinic management system with advanced features including conversational AI chatbot, appointment booking, doctor/patient management, reviews, and comprehensive statistics.

## Features

### Core Features ✅
- **Doctor Management**: Register doctors with specialties (8 types), licenses, ratings
- **Patient Management**: Register patients with emergency contacts, allergies, medical history, blood type
- **Appointment Booking**: Intelligent booking with double-booking prevention and time validation
- **Reviews & Ratings**: Track doctor performance through patient reviews
- **Search & Filter**: Advanced search across doctors, patients, appointments
- **Analytics**: Real-time clinic statistics and doctor-specific metrics

### Advanced Features ✅
- **Conversational AI Chatbot**: Multi-turn appointment booking with natural language processing
- **State Machine**: Robust conversation flow with context memory
- **Input Validation**: Comprehensive validation for dates, times, phone numbers, emails
- **Web Scraper**: Automatic doctor seeding from clinic websites (bonus feature)
- **Database Hardening**: Retry logic, exponential backoff, automatic indexing
- **Docker Support**: Complete containerization with docker-compose

## Architecture

```
src/
├── models/              # Pydantic data models
│   ├── person.py       # Base Person model
│   ├── doctor.py       # Doctor with MedicalSpecialty enum
│   ├── patient.py      # Patient with Gender, BloodType, EmergencyContact
│   ├── appointment.py  # Appointment with AppointmentStatus, ServiceType
│   └── review.py       # Review with rating validation
├── services/            # Business logic layer
│   ├── clinic_service.py        # CRUD operations, appointment booking
│   ├── chatbot_service.py       # Conversational AI engine
│   └── db.py (config/)          # MongoDB connection with retry logic
├── scrapers/            # Data seeding
│   └── clinic_scraper.py        # Web scraper for doctors
└── __init__.py

main.py                 # Interactive CLI interface
test_run.py            # Comprehensive test suite
requirements.txt       # Python dependencies
Dockerfile             # Container image
docker-compose.yml     # Multi-container orchestration
```

## Installation

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/yourusername/Dental-clinic-V2
cd Dental-clinic-V2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ensure MongoDB is running
mongod --dbpath ./data

# 4. Seed initial doctors (optional)
python -m src.scrapers.clinic_scraper

# 5. Run application
python main.py

# 6. Run tests
python test_run.py
```

### Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop containers
docker-compose down
```

## Usage

### Interactive CLI Menu

```
1. Add Doctor
   - Enter name, specialty (Orthodontics, Endodontics, etc.)
   - Automatically generate license number and phone
   
2. Add Patient
   - Enter demographics, emergency contact
   - Track medical history and allergies
   
3. Book Appointment
   - Validation: Future dates only, 30-min intervals
   - Double-booking prevention
   - Automatic time slot checking
   
4. Search Patient
5. Search Doctor
6. Add Review
7. View Statistics
8. Exit
```

### Chatbot Appointment Booking

Interactive multi-turn conversation:

```
User: I need a dental appointment
Bot: Welcome! What seems to be the problem?
User: I have a toothache
Bot: [URGENT] Let's get you scheduled...
Bot: What service do you need?
... [natural conversation flow]
Bot: [SUCCESS] Appointment booked!
```

### Programmatic Usage

```python
from src.services.clinic_service import ClinicService
from src.models.doctor import Doctor, MedicalSpecialty

service = ClinicService()

# Add doctor
doctor = Doctor(
    first_name="John",
    last_name="Smith",
    specialty=MedicalSpecialty.GENERAL_DENTISTRY,
    license_number="DEN-001-2024",
    phone="555-1001"
)
service.add_doctor(doctor)

# Book appointment
success, message = service.book_appointment_validated(
    patient_name="Alice Johnson",
    patient_phone="555-2001",
    doctor_name="John Smith",
    date="2025-12-15",
    time="14:00",
    service_type="Consultation"
)
print(message)

# Get statistics
stats = service.get_clinic_stats()
print(f"Total Doctors: {stats['total_doctors']}")
```

## Database Schema

### Collections

**doctors**
```json
{
  "_id": "uuid",
  "first_name": "John",
  "last_name": "Smith",
  "full_name": "John Smith",
  "specialty": "General Dentistry",
  "license_number": "DEN-001-2024",
  "phone": "555-1001",
  "patient_rating": 4.5,
  "shifts": ["Monday", "Tuesday", ...]
}
```

**patients**
```json
{
  "_id": "uuid",
  "first_name": "Alice",
  "last_name": "Johnson",
  "full_name": "Alice Johnson",
  "age": 28,
  "gender": "Female",
  "phone": "555-2001",
  "email": "alice@example.com",
  "blood_type": "O+",
  "medical_history": ["Cavity repair 2023"],
  "allergies": ["Penicillin"],
  "emergency_contact": {...}
}
```

**appointments**
```json
{
  "_id": "uuid",
  "patient_name": "Alice Johnson",
  "patient_phone": "555-2001",
  "doctor_name": "John Smith",
  "date": "2025-12-15",
  "time": "14:00",
  "service_type": "Consultation",
  "status": "SCHEDULED",
  "notes": "Patient reported: toothache",
  "created_at": "2025-12-08T10:30:00"
}
```

**reviews**
```json
{
  "_id": "uuid",
  "patient_name": "Alice Johnson",
  "doctor_name": "John Smith",
  "rating": 5,
  "comment": "Excellent service!",
  "created_at": "2025-12-08T15:45:00"
}
```

## Key Features Explained

### MedicalSpecialty Enum
```python
class MedicalSpecialty(str, Enum):
    GENERAL_DENTISTRY = "General Dentistry"
    ORTHODONTICS = "Orthodontics"
    ENDODONTICS = "Endodontics"
    PERIODONTICS = "Periodontics"
    PROSTHODONTICS = "Prosthodontics"
    ORAL_SURGERY = "Oral Surgery"
    PEDIATRIC_DENTISTRY = "Pediatric Dentistry"
    IMPLANTOLOGY = "Implantology"
```

### Double-Booking Prevention
Composite index ensures no doctor can have 2 appointments at the same time:
```python
# Check existing appointments before booking
existing = appointments_collection.find_one({
    "doctor_name": doctor_name,
    "date": date,
    "time": time,
    "status": {"$in": [SCHEDULED, CONFIRMED]}
})
```

### Retry Logic with Exponential Backoff
```python
# Connection attempts: 1s, 2s, 4s
for attempt in range(1, max_retries + 1):
    wait_time = base_wait * (2 ** (attempt - 1))
    # Retry with backoff
```

### Input Validation
- **Phone**: Regex pattern `^[\d\s\-\+\(\)]{7,20}$`
- **Email**: RFC 5322 compliant validation
- **Date**: Must be future date, within 90 days
- **Time**: Business hours 08:00-20:00, 30-minute intervals

## Testing

Run comprehensive test suite:

```bash
python test_run.py
```

Test coverage includes:
- ✅ TEST 1: Adding Doctors
- ✅ TEST 2: Registering Patients
- ✅ TEST 3: Booking Appointments with Validation
- ✅ TEST 4: Search Functionality
- ✅ TEST 5: Patient Reviews
- ✅ TEST 6: Clinic Statistics
- ✅ TEST 7: Chatbot Conversation Flow

## Performance Optimizations

### Database Indexes
```python
# Automatically created on connection
doctors: full_name, specialty, license_number
patients: full_name, phone, email
appointments: doctor_name, date, time, status (composite)
reviews: doctor_name, patient_name
```

### Query Optimization
- Regex search on indexed full_name field
- Composite indexes for multi-field queries
- Connection pooling via PyMongo

## Web Scraper

Bonus feature to seed real doctor data:

```bash
python -m src.scrapers.clinic_scraper
```

Features:
- Scrapes HealthGrades, ZocDoc, and other sources
- Automatically removes "Dr." titles and parses names
- Maps specialties to system enums
- Prevents duplicates with automatic deduplication
- Falls back to mock data when sites unavailable

## Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app
docker-compose logs -f mongodb

# Run tests in container
docker-compose exec app python test_run.py

# Stop services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## Project Structure Highlights

**Professional Patterns Used:**
- ✅ Singleton pattern for database connection
- ✅ State machine for chatbot conversation flow
- ✅ Pydantic models for strict type validation
- ✅ Exponential backoff for resilience
- ✅ Composite indexes for performance
- ✅ Context memory for sessions
- ✅ Error handling and logging throughout

**Bonus Features:**
- ✅ Web scraper for doctor seeding
- ✅ Docker containerization
- ✅ Multi-turn conversational AI
- ✅ Comprehensive test suite
- ✅ Database hardening with retry logic
- ✅ Automatic index creation

## Requirements

- Python 3.14+
- MongoDB 4.0+
- Docker & Docker Compose (for containerized deployment)

### Python Dependencies
```
pymongo>=4.0.0           # MongoDB driver
pydantic>=2.0.0          # Data validation
email-validator>=2.0.0   # Email validation
requests>=2.0.0          # HTTP requests
beautifulsoup4>=4.0.0    # Web scraping
pytest>=7.0.0            # Testing framework
coverage                 # Code coverage
```

## Troubleshooting

### MongoDB Connection Failed
```bash
# Check if MongoDB is running
mongosh

# If not, start MongoDB
mongod --dbpath ./data
```

### Duplicate Doctor Issues
```bash
# Clear existing data
db.doctors.deleteMany({})

# Re-run scraper
python -m src.scrapers.clinic_scraper
```

### Chatbot State Issues
- Clear browser cookies
- Restart Python process
- Check session TTL (default 1 hour)

## Future Enhancements

- [ ] Email notifications for appointments
- [ ] SMS reminders (Twilio integration)
- [ ] Payment processing (Stripe)
- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Machine learning for demand forecasting
- [ ] Video consultation support

## License

MIT License - See LICENSE file for details

## Author

Created as university assignment demonstrating:
- Object-Oriented Programming (OOP)
- Database design (MongoDB)
- Web scraping techniques
- API design
- Testing and quality assurance
- DevOps (Docker)
- Conversational AI patterns

## Support

For issues or questions, please create a GitHub issue or contact the maintainer.

---

**Status**: ✅ Production Ready | **Version**: 2.0.0 | **Last Updated**: December 8, 2025
