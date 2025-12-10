"""
Professional Chatbot Service (Upgraded)

Intelligent conversational AI for appointment booking with:
- Conversation state machine with ConversationState enum
- Full input validation (dates, times, phone numbers)
- Context memory per user session
- Follow-up questions and error recovery
"""

from src.services.clinic_service import ClinicService
from src.models.appointment import Appointment, AppointmentStatus, ServiceType
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import re


class ConversationState:
    """Conversation stage constants."""
    START = "start"
    GREETING = "greeting"
    PROBLEM_ASSESSMENT = "problem_assessment"
    SERVICE_SELECTION = "service_selection"
    DATE_SELECTION = "date_selection"
    TIME_SELECTION = "time_selection"
    PHONE_COLLECTION = "phone_collection"
    DOCTOR_SELECTION = "doctor_selection"
    CONFIRMATION = "confirmation"
    BOOKING_COMPLETE = "booking_complete"

    # New states for enhanced functionality
    INTENT_DETECTION = "intent_detection"
    CANCEL_START = "cancel_start"
    CANCEL_CONFIRMATION = "cancel_confirmation"
    RESCHEDULE_START = "reschedule_start"
    RESCHEDULE_APPOINTMENT_SELECTION = "reschedule_appointment_selection"
    RESCHEDULE_DATE_SELECTION = "reschedule_date_selection"
    RESCHEDULE_TIME_SELECTION = "reschedule_time_selection"
    RESCHEDULE_CONFIRMATION = "reschedule_confirmation"
    VIEW_START = "view_start"
    VIEW_RESULTS = "view_results"


class ChatBotService:
    """
    Professional dental clinic chatbot.
    
    Manages multi-turn conversations with patients, collects appointment info,
    validates inputs, and books appointments in MongoDB.
    """

    def __init__(self):
        """Initialize chatbot with clinic service access."""
        self.clinic = ClinicService()
        self.sessions: Dict[str, dict] = {}
        self.available_services = [s.value for s in ServiceType]

    def _create_session(self, user_name: str) -> dict:
        """Create new conversation session for a user."""
        return {
            "state": ConversationState.START,
            "user_name": user_name,
            "data": {
                "patient_name": user_name,
                "problem": None,
                "service_type": None,
                "date": None,
                "time": None,
                "doctor_name": None,
                "phone": None,
                "notes": None
            },
            "validation_errors": [],
            "attempt_count": 0,
            "created_at": datetime.now()
        }

    def _get_or_create_session(self, user_name: str) -> dict:
        """Get existing session or create new one."""
        if user_name not in self.sessions:
            self.sessions[user_name] = self._create_session(user_name)
        return self.sessions[user_name]

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        pattern = r'^[\d\s\-\+\(\)]{7,20}$'
        return bool(re.match(pattern, phone.strip()))

    def _is_valid_date(self, date_str: str) -> Tuple[bool, Optional[str]]:
        """Validate date format and ensure it's in the future."""
        try:
            date_obj = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            # Appointments must be at least 1 day in the future
            if date_obj.date() < datetime.now().date():
                return False, "Date must be in the future"
            # Can't book more than 90 days ahead
            if date_obj.date() > datetime.now().date() + timedelta(days=90):
                return False, "Cannot book appointments more than 3 months in advance"
            return True, None
        except ValueError:
            return False, "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-12-25)"

    def _is_valid_time(self, time_str: str) -> Tuple[bool, Optional[str]]:
        """Validate time format and business hours."""
        try:
            time_obj = datetime.strptime(time_str.strip(), "%H:%M")
            hour = time_obj.hour
            minute = time_obj.minute
            
            # Business hours: 08:00 - 20:00
            if hour < 8 or hour >= 20:
                return False, "Clinic hours are 08:00 to 20:00"
            
            # Check for 30-minute intervals only
            if minute not in [0, 30]:
                return False, "Please select time on 30-minute intervals (e.g., 14:00 or 14:30)"
            
            return True, None
        except ValueError:
            return False, "Invalid time format. Please use HH:MM (e.g., 14:30)"

    def _cleanup_old_sessions(self, max_age_hours: int = 1):
        """Remove sessions older than max_age_hours."""
        now = datetime.now()
        expired_users = []
        
        for user_name, session in self.sessions.items():
            created = session.get("created_at", now)
            age = (now - created).total_seconds() / 3600
            if age > max_age_hours:
                expired_users.append(user_name)
        
        for user_name in expired_users:
            del self.sessions[user_name]

    def get_response(self, user_input: str, user_name: str = "Guest") -> str:
        """
        Main entry point: process user input and return response.

        Implements state machine for multi-turn appointment booking and management.
        """
        # Cleanup old sessions every 10 interactions
        if len(self.sessions) % 10 == 0:
            self._cleanup_old_sessions()

        session = self._get_or_create_session(user_name)
        state = session["state"]
        user_input = user_input.strip()

        # Handle global commands
        if user_input.lower() in ["cancel", "exit", "quit"]:
            session["state"] = ConversationState.START
            return "Conversation cancelled. Type anything to start over!"

        if user_input.lower() == "restart":
            self.sessions[user_name] = self._create_session(user_name)
            return self._handle_greeting(self.sessions[user_name])

        # Detect intent at START state
        if state == ConversationState.START:
            intent = self._detect_intent(user_input)
            if intent == "book":
                return self._handle_greeting(session)
            elif intent == "cancel":
                return self._handle_cancel_start(session)
            elif intent == "reschedule":
                return self._handle_reschedule_start(session)
            elif intent == "view":
                return self._handle_view_start(session)
            else:
                # Default to booking if intent unclear
                return self._handle_intent_detection(session)

        # Route by state
        if state == ConversationState.INTENT_DETECTION:
            return self._handle_intent_detection_response(session, user_input)
        elif state == ConversationState.GREETING:
            return self._handle_problem_assessment(session, user_input)
        elif state == ConversationState.PROBLEM_ASSESSMENT:
            return self._handle_service_selection(session, user_input)
        elif state == ConversationState.SERVICE_SELECTION:
            return self._handle_date_selection(session, user_input)
        elif state == ConversationState.DATE_SELECTION:
            return self._handle_time_selection(session, user_input)
        elif state == ConversationState.TIME_SELECTION:
            return self._handle_phone_collection(session, user_input)
        elif state == ConversationState.PHONE_COLLECTION:
            return self._handle_doctor_selection(session, user_input)
        elif state == ConversationState.DOCTOR_SELECTION:
            return self._handle_confirmation(session, user_input)
        elif state == ConversationState.CONFIRMATION:
            return self._handle_booking_confirmation(session, user_input)
        elif state == ConversationState.BOOKING_COMPLETE:
            return self._handle_followup(session, user_input)
        # New states for enhanced functionality
        elif state == ConversationState.CANCEL_START:
            return self._handle_cancel_appointment_selection(session, user_input)
        elif state == ConversationState.CANCEL_CONFIRMATION:
            return self._handle_cancel_confirmation(session, user_input)
        elif state == ConversationState.RESCHEDULE_START:
            return self._handle_reschedule_appointment_selection(session, user_input)
        elif state == ConversationState.RESCHEDULE_APPOINTMENT_SELECTION:
            return self._handle_reschedule_appointment_selection_response(session, user_input)
        elif state == ConversationState.RESCHEDULE_DATE_SELECTION:
            return self._handle_reschedule_date_selection(session, user_input)
        elif state == ConversationState.RESCHEDULE_TIME_SELECTION:
            return self._handle_reschedule_time_selection(session, user_input)
        elif state == ConversationState.RESCHEDULE_CONFIRMATION:
            return self._handle_reschedule_confirmation(session, user_input)
        elif state == ConversationState.VIEW_START:
            return self._handle_view_appointments(session, user_input)
        elif state == ConversationState.VIEW_RESULTS:
            return self._handle_view_followup(session, user_input)
        else:
            return "I'm not sure what to do. Type 'restart' to begin again."

    def _greet_user(self, user_name: str) -> str:
        """Generate personalized greeting."""
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        return (
            f"{greeting}, {user_name}!\n\n"
            f"Welcome to DentalClinic Pro - Your appointment assistant.\n"
            f"I'm here to help you book an appointment quickly and easily.\n"
            f"(Type 'cancel' anytime to exit)"
        )

    def _handle_greeting(self, session: dict) -> str:
        """Handle initial greeting."""
        session["state"] = ConversationState.GREETING
        return self._greet_user(session["user_name"])

    def _handle_problem_assessment(self, session: dict, user_input: str) -> str:
        """Collect and assess patient's dental problem."""
        session["data"]["problem"] = user_input
        session["state"] = ConversationState.PROBLEM_ASSESSMENT

        # Empathetic response based on keywords
        problem_lower = user_input.lower()
        if any(w in problem_lower for w in ["emergency", "urgent", "severe", "pain"]):
            response = "[URGENT] I understand this is urgent! We have emergency slots available.\n\n"
        elif any(w in problem_lower for w in ["clean", "routine", "checkup"]):
            response = "[ROUTINE] Great! Routine maintenance is important for healthy teeth.\n\n"
        elif any(w in problem_lower for w in ["cosmetic", "whiten", "brighten"]):
            response = "[COSMETIC] We offer cosmetic services! Let's get your smile perfect.\n\n"
        else:
            response = "[INFO] Thank you for sharing that. I'm here to help.\n\n"

        response += "What service would you like?\n"
        for i, service in enumerate(self.available_services[:6], 1):
            response += f"  {i}. {service}\n"
        response += f"  ... ({len(self.available_services)} services available)\n"
        response += "\nOr type the service name directly:"

        session["state"] = ConversationState.SERVICE_SELECTION
        return response

    def _handle_service_selection(self, session: dict, user_input: str) -> str:
        """Handle service type selection."""
        user_input_lower = user_input.lower().strip()

        # Try to match service
        selected_service = None

        # First, try to match by number
        try:
            service_index = int(user_input.strip()) - 1
            if 0 <= service_index < len(self.available_services):
                selected_service = self.available_services[service_index]
        except ValueError:
            pass

        # If not matched by number, try to match by name
        if not selected_service:
            for service in ServiceType:
                if user_input_lower in service.value.lower():
                    selected_service = service.value
                    break

        if not selected_service:
            return (
                f"[ERROR] I don't recognize '{user_input}'.\n\n"
                f"Available services:\n"
                + "\n".join(f"  - {s}" for s in self.available_services)
            )

        session["data"]["service_type"] = selected_service
        session["state"] = ConversationState.DATE_SELECTION

        return (
            f"[OK] Great! You selected: {selected_service}\n\n"
            f"[DATE] When would you like to come in?\n"
            f"Please provide a date (YYYY-MM-DD)\n"
            f"Example: {(datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')}"
        )

    def _handle_date_selection(self, session: dict, user_input: str) -> str:
        """Handle date selection with validation."""
        is_valid, error_msg = self._is_valid_date(user_input)

        if not is_valid:
            if user_input.strip().isdigit():
                return f"[ERROR] That looks like a service number. If you meant to select a different service, type 'restart' to start over.\n\n{error_msg}\n\nPlease try again (YYYY-MM-DD)"
            else:
                return f"[ERROR] {error_msg}\n\nPlease try again (YYYY-MM-DD)"

        session["data"]["date"] = user_input.strip()
        session["state"] = ConversationState.TIME_SELECTION

        return (
            f"[OK] Date confirmed: {user_input.strip()}\n\n"
            f"[TIME] What time works for you?\n"
            f"Please provide time in HH:MM format (e.g., 14:30)\n"
            f"Available: 08:00 - 20:00 (30-minute intervals)"
        )

    def _handle_time_selection(self, session: dict, user_input: str) -> str:
        """Handle time selection with validation."""
        is_valid, error_msg = self._is_valid_time(user_input)
        
        if not is_valid:
            return f"[ERROR] {error_msg}\n\nPlease try again (HH:MM)"

        session["data"]["time"] = user_input.strip()
        session["state"] = ConversationState.PHONE_COLLECTION
        
        return (
            f"[OK] Time confirmed: {user_input.strip()}\n\n"
            f"[PHONE] What's your phone number?\n"
            f"We need this to confirm your appointment and send reminders."
        )

    def _handle_phone_collection(self, session: dict, user_input: str) -> str:
        """Handle phone number collection and validation."""
        if not self._is_valid_phone(user_input):
            return "[ERROR] Please provide a valid phone number (7-20 digits)\n\nExample: +1-555-123-4567"

        session["data"]["phone"] = user_input.strip()
        session["state"] = ConversationState.DOCTOR_SELECTION
        
        # Get available doctors
        doctors = self.clinic.get_all_doctors()
        
        if not doctors:
            doctors_text = "  - Any available doctor (automatic assignment)"
        else:
            # Show top 5 doctors
            doctors_text = "\n".join(
                f"  - Dr. {d.full_name} ({d.specialty.value}) - Rating: {d.patient_rating}/5"
                for d in doctors[:5]
            )
            if len(doctors) > 5:
                doctors_text += f"\n  ... and {len(doctors)-5} more doctors"

        return (
            f"[OK] Phone confirmed: {user_input.strip()}\n\n"
            f"[DOCTOR] Which doctor would you prefer?\n"
            f"{doctors_text}\n\n"
            f"Or type 'any' for next available doctor"
        )

    def _handle_doctor_selection(self, session: dict, user_input: str) -> str:
        """Handle doctor selection."""
        doctor_input = user_input.strip().lower()
        
        if doctor_input == "any":
            session["data"]["doctor_name"] = "Any"
        else:
            # Verify doctor exists
            doctor = self.clinic.get_doctor_by_name(user_input)
            if not doctor:
                return f"[ERROR] Doctor '{user_input}' not found. Please try:\n  - 'any' for automatic assignment\n  - Full doctor name (e.g., 'John Smith')"
            session["data"]["doctor_name"] = doctor.full_name

        session["state"] = ConversationState.CONFIRMATION
        
        # Prepare summary
        data = session["data"]
        summary = (
            f"[REVIEW] Please review your appointment details:\n\n"
            f"Name: {data['patient_name']}\n"
            f"Phone: {data['phone']}\n"
            f"Service: {data['service_type']}\n"
            f"Date: {data['date']}\n"
            f"Time: {data['time']}\n"
            f"Doctor: {data['doctor_name']}\n\n"
            f"Is this correct? (yes/no)"
        )
        
        return summary

    def _handle_confirmation(self, session: dict, user_input: str) -> str:
        """Handle final confirmation before booking."""
        response_lower = user_input.strip().lower()
        
        if response_lower in ["yes", "y", "ok", "correct", "sure"]:
            return self._book_appointment(session)
        elif response_lower in ["no", "n", "cancel", "edit"]:
            session["state"] = ConversationState.START
            return "[CANCEL] Appointment cancelled.\n\nType anything to start over."
        else:
            return "[ERROR] Please answer with 'yes' or 'no'"

    def _book_appointment(self, session: dict) -> str:
        """Create and save appointment to database."""
        try:
            data = session["data"]
            
            # Create appointment object
            appointment = Appointment(
                patient_name=data["patient_name"],
                patient_phone=data["phone"],
                doctor_name=data["doctor_name"],
                date=data["date"],
                time=data["time"],
                service_type=data["service_type"],
                status=AppointmentStatus.SCHEDULED,
                notes=f"Issue: {data['problem']}"
            )

            # Save to database
            success, message = self.clinic.book_appointment_validated(
                patient_name=data["patient_name"],
                patient_phone=data["phone"],
                doctor_name=data["doctor_name"],
                date=data["date"],
                time=data["time"],
                service_type=data["service_type"],
                notes=f"Patient reported: {data['problem']}"
            )

            if success:
                session["state"] = ConversationState.BOOKING_COMPLETE
                return (
                    f"[SUCCESS] Appointment booked successfully!\n\n"
                    f"Confirmation Details:\n"
                    f"Appointment ID: {appointment.id}\n"
                    f"Date: {data['date']} at {data['time']}\n"
                    f"Doctor: Dr. {data['doctor_name']}\n"
                    f"Service: {data['service_type']}\n\n"
                    f"Confirmation sent to {data['phone']}\n"
                    f"Please call 30 minutes before your appointment.\n\n"
                    f"Thank you!"
                )
            else:
                return f"[ERROR] Booking failed: {message}\n\nPlease try again or contact support."

        except Exception as e:
            return f"[ERROR] Error booking appointment: {str(e)}\n\nPlease try again later."

    def _handle_followup(self, session: dict, user_input: str) -> str:
        """Handle post-booking interactions."""
        if "restart" in user_input.lower():
            self.sessions[session["user_name"]] = self._create_session(session["user_name"])
            return "[RESTART] Starting new appointment booking...\n" + self._greet_user(session["user_name"])
        elif any(w in user_input.lower() for w in ["thank", "thanks", "bye", "goodbye"]):
            return "[END] You're welcome! Have a great day and take care of your smile!"
        else:
            return (
                "[INFO] Is there anything else I can help you with?\n"
                f"Type 'restart' to book another appointment or 'bye' to exit."
            )

    def _detect_intent(self, user_input: str) -> str:
        """Detect user intent from initial input."""
        input_lower = user_input.lower().strip()

        # Keywords for different intents
        book_keywords = ["book", "schedule", "appointment", "make", "new", "create", "set up"]
        cancel_keywords = ["cancel", "delete", "remove", "stop"]
        reschedule_keywords = ["reschedule", "change", "modify", "update", "move"]
        view_keywords = ["view", "see", "show", "list", "check", "my", "upcoming", "appointments"]

        if any(keyword in input_lower for keyword in cancel_keywords):
            return "cancel"
        elif any(keyword in input_lower for keyword in reschedule_keywords):
            return "reschedule"
        elif any(keyword in input_lower for keyword in view_keywords):
            return "view"
        elif any(keyword in input_lower for keyword in book_keywords):
            return "book"
        else:
            return "unknown"

    def _handle_intent_detection(self, session: dict) -> str:
        """Handle unclear intent by asking user to clarify."""
        session["state"] = ConversationState.INTENT_DETECTION
        return (
            f"Hello! I'm your dental clinic assistant.\n\n"
            f"What would you like to do?\n\n"
            f"1. 📅 Book a new appointment\n"
            f"2. ❌ Cancel an existing appointment\n"
            f"3. 🔄 Reschedule an appointment\n"
            f"4. 👀 View my appointments\n\n"
            f"Please type the number or describe what you need:"
        )

    def _handle_intent_detection_response(self, session: dict, user_input: str) -> str:
        """Handle user's response to intent clarification."""
        input_lower = user_input.lower().strip()

        if input_lower in ["1", "book", "booking", "schedule", "appointment"]:
            return self._handle_greeting(session)
        elif input_lower in ["2", "cancel", "cancellation"]:
            return self._handle_cancel_start(session)
        elif input_lower in ["3", "reschedule", "change"]:
            return self._handle_reschedule_start(session)
        elif input_lower in ["4", "view", "see", "show"]:
            return self._handle_view_start(session)
        else:
            return (
                f"[ERROR] I didn't understand that option.\n\n"
                f"Please choose:\n"
                f"1. Book appointment\n"
                f"2. Cancel appointment\n"
                f"3. Reschedule appointment\n"
                f"4. View appointments"
            )

    # ==================== CANCEL APPOINTMENT ====================

    def _handle_cancel_start(self, session: dict) -> str:
        """Start cancel appointment flow."""
        session["state"] = ConversationState.CANCEL_START
        return (
            f"[CANCEL] Let's cancel your appointment.\n\n"
            f"Please provide your name or phone number to find your appointments:"
        )

    def _handle_cancel_appointment_selection(self, session: dict, user_input: str) -> str:
        """Find and display appointments for cancellation."""
        # Try to find appointments by name or phone
        appointments = self.clinic.get_patient_appointments(user_input.strip())

        if not appointments:
            return (
                f"[ERROR] No appointments found for '{user_input}'.\n\n"
                f"Please check your name or phone number and try again."
            )

        # Filter to show only cancellable appointments (not completed/cancelled)
        cancellable = [apt for apt in appointments if apt.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]]

        if not cancellable:
            return (
                f"[INFO] You don't have any upcoming appointments that can be cancelled.\n\n"
                f"All your appointments are either completed or already cancelled."
            )

        session["data"]["available_appointments"] = cancellable
        session["state"] = ConversationState.CANCEL_CONFIRMATION

        response = "[APPOINTMENTS] Here are your upcoming appointments:\n\n"
        for i, apt in enumerate(cancellable, 1):
            response += f"{i}. {apt.date} at {apt.time} - Dr. {apt.doctor_name} ({apt.service_type.value})\n"

        response += f"\nWhich appointment would you like to cancel? (Enter the number)"
        return response

    def _handle_cancel_confirmation(self, session: dict, user_input: str) -> str:
        """Handle appointment cancellation confirmation."""
        try:
            appointment_index = int(user_input.strip()) - 1
            available_appointments = session["data"].get("available_appointments", [])

            if appointment_index < 0 or appointment_index >= len(available_appointments):
                return f"[ERROR] Invalid selection. Please enter a number between 1 and {len(available_appointments)}"

            appointment = available_appointments[appointment_index]

            # Cancel the appointment
            success = self.clinic.cancel_appointment(appointment.id, "Cancelled via chatbot")

            if success:
                session["state"] = ConversationState.START
                return (
                    f"[SUCCESS] Appointment cancelled successfully!\n\n"
                    f"Cancelled: {appointment.date} at {appointment.time} with Dr. {appointment.doctor_name}\n\n"
                    f"If you need to book a new appointment, just let me know!"
                )
            else:
                return "[ERROR] Failed to cancel appointment. Please try again or contact support."

        except ValueError:
            return "[ERROR] Please enter a valid number."

    # ==================== RESCHEDULE APPOINTMENT ====================

    def _handle_reschedule_start(self, session: dict) -> str:
        """Start reschedule appointment flow."""
        session["state"] = ConversationState.RESCHEDULE_START
        return (
            f"[RESCHEDULE] Let's reschedule your appointment.\n\n"
            f"Please provide your name or phone number to find your appointments:"
        )

    def _handle_reschedule_appointment_selection(self, session: dict, user_input: str) -> str:
        """Find and display appointments for rescheduling."""
        # Try to find appointments by name or phone
        appointments = self.clinic.get_patient_appointments(user_input.strip())

        if not appointments:
            return (
                f"[ERROR] No appointments found for '{user_input}'.\n\n"
                f"Please check your name or phone number and try again."
            )

        # Filter to show only reschedulable appointments (scheduled/confirmed)
        reschedulable = [apt for apt in appointments if apt.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]]

        if not reschedulable:
            return (
                f"[INFO] You don't have any upcoming appointments that can be rescheduled.\n\n"
                f"All your appointments are either completed or cancelled."
            )

        session["data"]["available_appointments"] = reschedulable
        session["state"] = ConversationState.RESCHEDULE_APPOINTMENT_SELECTION

        response = "[APPOINTMENTS] Here are your upcoming appointments:\n\n"
        for i, apt in enumerate(reschedulable, 1):
            response += f"{i}. {apt.date} at {apt.time} - Dr. {apt.doctor_name} ({apt.service_type.value})\n"

        response += f"\nWhich appointment would you like to reschedule? (Enter the number)"
        return response

    def _handle_reschedule_appointment_selection_response(self, session: dict, user_input: str) -> str:
        """Handle appointment selection for rescheduling."""
        try:
            appointment_index = int(user_input.strip()) - 1
            available_appointments = session["data"].get("available_appointments", [])

            if appointment_index < 0 or appointment_index >= len(available_appointments):
                return f"[ERROR] Invalid selection. Please enter a number between 1 and {len(available_appointments)}"

            appointment = available_appointments[appointment_index]
            session["data"]["selected_appointment"] = appointment
            session["state"] = ConversationState.RESCHEDULE_DATE_SELECTION

            return (
                f"[OK] Selected appointment: {appointment.date} at {appointment.time} with Dr. {appointment.doctor_name}\n\n"
                f"[NEW DATE] What is your new preferred date?\n"
                f"Please provide date in YYYY-MM-DD format:"
            )

        except ValueError:
            return "[ERROR] Please enter a valid number."

    def _handle_reschedule_date_selection(self, session: dict, user_input: str) -> str:
        """Handle new date selection for rescheduling."""
        is_valid, error_msg = self._is_valid_date(user_input)

        if not is_valid:
            return f"[ERROR] {error_msg}\n\nPlease try again (YYYY-MM-DD)"

        session["data"]["new_date"] = user_input.strip()
        session["state"] = ConversationState.RESCHEDULE_TIME_SELECTION

        return (
            f"[OK] New date confirmed: {user_input.strip()}\n\n"
            f"[NEW TIME] What time works for you?\n"
            f"Please provide time in HH:MM format (e.g., 14:30)\n"
            f"Available: 08:00 - 20:00 (30-minute intervals)"
        )

    def _handle_reschedule_time_selection(self, session: dict, user_input: str) -> str:
        """Handle new time selection for rescheduling."""
        is_valid, error_msg = self._is_valid_time(user_input)

        if not is_valid:
            return f"[ERROR] {error_msg}\n\nPlease try again (HH:MM)"

        session["data"]["new_time"] = user_input.strip()
        session["state"] = ConversationState.RESCHEDULE_CONFIRMATION

        appointment = session["data"]["selected_appointment"]
        new_date = session["data"]["new_date"]
        new_time = session["data"]["new_time"]

        return (
            f"[REVIEW] Please confirm the rescheduling:\n\n"
            f"Current: {appointment.date} at {appointment.time} with Dr. {appointment.doctor_name}\n"
            f"New: {new_date} at {new_time} with Dr. {appointment.doctor_name}\n\n"
            f"Is this correct? (yes/no)"
        )

    def _handle_reschedule_confirmation(self, session: dict, user_input: str) -> str:
        """Handle rescheduling confirmation."""
        response_lower = user_input.strip().lower()

        if response_lower in ["yes", "y", "ok", "correct", "sure"]:
            appointment = session["data"]["selected_appointment"]
            new_date = session["data"]["new_date"]
            new_time = session["data"]["new_time"]

            success = self.clinic.reschedule_appointment(appointment.id, new_date, new_time)

            if success:
                session["state"] = ConversationState.START
                return (
                    f"[SUCCESS] Appointment rescheduled successfully!\n\n"
                    f"New appointment: {new_date} at {new_time} with Dr. {appointment.doctor_name}\n"
                    f"Service: {appointment.service_type.value}\n\n"
                    f"Thank you!"
                )
            else:
                return "[ERROR] Failed to reschedule appointment. Please try again or contact support."
        elif response_lower in ["no", "n", "cancel"]:
            session["state"] = ConversationState.START
            return "[CANCEL] Rescheduling cancelled.\n\nType anything to start over."
        else:
            return "[ERROR] Please answer with 'yes' or 'no'"

    # ==================== VIEW APPOINTMENTS ====================

    def _handle_view_start(self, session: dict) -> str:
        """Start view appointments flow."""
        session["state"] = ConversationState.VIEW_START
        return (
            f"[VIEW] Let's check your appointments.\n\n"
            f"Please provide your name or phone number:"
        )

    def _handle_view_appointments(self, session: dict, user_input: str) -> str:
        """Display user's appointments."""
        appointments = self.clinic.get_patient_appointments(user_input.strip())

        if not appointments:
            session["state"] = ConversationState.START
            return (
                f"[INFO] No appointments found for '{user_input}'.\n\n"
                f"If you'd like to book an appointment, just let me know!"
            )

        session["state"] = ConversationState.VIEW_RESULTS

        response = f"[APPOINTMENTS] Here are your appointments:\n\n"

        # Sort appointments by date
        appointments.sort(key=lambda x: x.get_datetime())

        for apt in appointments:
            status_emoji = {
                AppointmentStatus.SCHEDULED: "📅",
                AppointmentStatus.CONFIRMED: "✅",
                AppointmentStatus.COMPLETED: "✔️",
                AppointmentStatus.CANCELLED: "❌",
                AppointmentStatus.NO_SHOW: "🚫",
                AppointmentStatus.RESCHEDULED: "🔄"
            }.get(apt.status, "❓")

            response += f"{status_emoji} {apt.date} at {apt.time} - Dr. {apt.doctor_name}\n"
            response += f"   Service: {apt.service_type.value} | Status: {apt.status.value}\n"

            if apt.notes:
                response += f"   Notes: {apt.notes}\n"
            response += "\n"

        response += "Would you like to book a new appointment, cancel, or reschedule any of these? (book/cancel/reschedule/no)"
        return response

    def _handle_view_followup(self, session: dict, user_input: str) -> str:
        """Handle follow-up after viewing appointments."""
        input_lower = user_input.lower().strip()

        if input_lower in ["book", "booking", "new", "schedule"]:
            return self._handle_greeting(session)
        elif input_lower in ["cancel", "cancellation"]:
            return self._handle_cancel_start(session)
        elif input_lower in ["reschedule", "change"]:
            return self._handle_reschedule_start(session)
        elif input_lower in ["no", "nothing", "thanks", "bye"]:
            session["state"] = ConversationState.START
            return "[END] You're welcome! Have a great day and take care of your smile!"
        else:
            return (
                "[INFO] What would you like to do next?\n"
                f"Type 'book' for new appointment, 'cancel' to cancel, 'reschedule' to change, or 'no' to exit."
            )
