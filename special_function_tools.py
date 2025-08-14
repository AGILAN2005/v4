# #special_function_tools.py

# from typing import Optional, Dict, Any, List
# from livekit.agents import function_tool
# from datetime import date, datetime
# from dateutil import parser as dtparser
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from contextlib import contextmanager
# import os

# from scheduler import AppointmentScheduler
# from ORM import Base, Doctor, Patient, Appointment, Specialization
# from utils.logger import logger
# from utils.exceptions import *
# from utils.rate_limiter import rate_limiter
# from utils.date_parser import date_parser
# from utils.language_support import language_manager
# from config import settings

# # -------------------------
# # Database Setup with Connection Pooling
# # -------------------------
# DATABASE_URL = settings.DATABASE_URL
# engine = create_engine(
#     DATABASE_URL, 
#     echo=False,
#     pool_size=10,
#     max_overflow=20,
#     pool_pre_ping=True,
#     pool_recycle=3600
# )
# SessionLocal = sessionmaker(bind=engine)

# # Ensure tables are created
# Base.metadata.create_all(engine)

# @contextmanager
# def get_db_session():
#     """Context manager for database sessions with proper cleanup"""
#     session = SessionLocal()
#     try:
#         yield session
#         session.commit()
#     except Exception as e:
#         session.rollback()
#         logger.error(f"Database session error: {e}")
#         raise
#     finally:
#         session.close()

# def get_scheduler_with_session(session):
#     """Get scheduler instance with session"""
#     return AppointmentScheduler(session)

# def handle_rate_limiting(identifier: str, max_requests: int = 5, window: int = 300) -> Optional[Dict[str, Any]]:
#     """Handle rate limiting for function calls"""
#     if not rate_limiter.is_allowed(identifier, max_requests, window):
#         remaining_time = rate_limiter.get_remaining_time(identifier, window)
#         return {
#             "ok": False, 
#             "error": f"Too many requests. Please wait {remaining_time} seconds before trying again.",
#             "error_code": "RATE_LIMIT_EXCEEDED"
#         }
#     return None

# @function_tool(
#     name="register_patient", 
#     description="Register a new patient or update existing patient details. Args: name (str), phone (str), age (int, optional), location (str, optional), language (str, optional - 'en', 'hi', 'ta')"
# )
# async def register_patient(name: str, phone: str, age: Optional[int] = None, 
#                     location: Optional[str] = None, language: str = 'en') -> Dict[str, Any]:
    
#     # Rate limiting
#     rate_limit_result = handle_rate_limiting(f"register_patient:{phone}")
#     if rate_limit_result:
#         return rate_limit_result
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             patient = scheduler.register_patient(
#                 name=name, phone=phone, age=age, 
#                 location=location, language=language
#             )
            
#             logger.info("Patient registration successful", 
#                        patient_id=patient.patient_id, 
#                        phone_hash=patient.phone_hash[:8])
            
#             return {
#                 "ok": True,
#                 "patient_id": patient.patient_id,
#                 "name": patient.name,
#                 "phone": phone,
#                 "is_new_patient": patient.first_visit,
#                 "message": language_manager.get_message(
#                     "patient_registered" if patient.first_visit else "patient_found", 
#                     language
#                 )
#             }
            
#         except (PatientNotFoundError, InvalidDateError) as e:
#             logger.warning(f"Patient registration validation error: {e}")
#             return {"ok": False, "error": str(e), "error_code": "VALIDATION_ERROR"}
#         except Exception as e:
#             logger.error(f"Patient registration error: {e}")
#             return {"ok": False, "error": "Failed to register patient. Please try again.", "error_code": "SYSTEM_ERROR"}

# @function_tool(
#     name="find_patient_enhanced", 
#     description="Find patient by phone number or name with fuzzy matching. Args: query (str) - phone number or name"
# )
# async def find_patient_enhanced(query: str) -> Dict[str, Any]:
    
#     # Rate limiting
#     rate_limit_result = handle_rate_limiting(f"find_patient:{query}")
#     if rate_limit_result:
#         return rate_limit_result
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             patients = scheduler.enhanced_patient_search(query)
            
#             result = []
#             for p in patients:
#                 result.append({
#                     "patient_id": p.patient_id,
#                     "name": p.name,
#                     "phone": p.phone,
#                     "age": p.age,
#                     "location": p.location,
#                     "preferred_language": p.preferred_language or 'en'
#                 })
            
#             logger.info(f"Patient search completed", query_type="enhanced", results_count=len(result))
            
#             return {
#                 "ok": True,
#                 "patients": result,
#                 "count": len(result),
#                 "query": query
#             }
            
#         except Exception as e:
#             logger.error(f"Enhanced patient search error: {e}")
#             return {"ok": False, "error": "Search failed. Please try again.", "error_code": "SEARCH_ERROR"}

# @function_tool(
#     name="recommend_doctor", 
#     description="Recommend a doctor based on specialization and desired date. Args: specialization (str), desired_date (str, YYYY-MM-DD or natural language), patient_id (int, optional), first_visit (bool, optional), patient_location (str, optional)"
# )
# async def recommend_doctor(specialization: str, desired_date: str, patient_id: Optional[int] = None, 
#                     first_visit: bool = True, patient_location: Optional[str] = None) -> Dict[str, Any]:
    
#     # Rate limiting
#     rate_limit_result = handle_rate_limiting(f"recommend_doctor:{patient_id or 'anonymous'}")
#     if rate_limit_result:
#         return rate_limit_result
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             # Parse date with enhanced validation
#             on_date = date_parser.parse_natural_language_date(desired_date, "booking")
            
#             doctor = scheduler.recommend_doctor(
#                 patient_id=patient_id,
#                 specialization=specialization,
#                 on_date=on_date,
#                 first_visit=first_visit,
#                 patient_location=patient_location
#             )
            
#             if doctor:
#                 logger.info("Doctor recommendation successful", 
#                            doctor_id=doctor.doctor_id,
#                            specialization=specialization,
#                            date=on_date.isoformat())
                
#                 return {
#                     "ok": True,
#                     "doctor_id": doctor.doctor_id,
#                     "name": doctor.name,
#                     "qualification": doctor.qualification,
#                     "specializations": [s.name for s in doctor.specializations],
#                     "consultation_fee": doctor.consultation_fee,
#                     "experience_years": doctor.experience_years,
#                     "working_hours": {
#                         "start": doctor.working_start.strftime("%H:%M"),
#                         "end": doctor.working_end.strftime("%H:%M")
#                     }
#                 }
#             else:
#                 logger.warning("No doctor found for recommendation", 
#                               specialization=specialization, 
#                               date=on_date.isoformat())
#                 return {
#                     "ok": False,
#                     "error": f"No doctors available for {specialization} on {on_date.strftime('%B %d, %Y')}.",
#                     "error_code": "NO_DOCTOR_AVAILABLE",
#                     "alternatives": {
#                         "message": "Try choosing a different date or specialization.",
#                         "suggested_action": "get_alternative_dates"
#                     }
#                 }
                
#         except InvalidDateError as e:
#             logger.warning(f"Date validation error in doctor recommendation: {e}")
#             return {"ok": False, "error": str(e), "error_code": "INVALID_DATE"}
#         except Exception as e:
#             logger.error(f"Doctor recommendation error: {e}")
#             return {"ok": False, "error": "Failed to recommend doctor. Please try again.", "error_code": "SYSTEM_ERROR"}

# @function_tool(
#     name="get_available_slots_enhanced", 
#     description="Get available appointment slots for a doctor on a specific date with intelligent ordering. Args: doctor_id (int), date (str, YYYY-MM-DD), preferred_time (str, optional - 'morning', 'afternoon', 'evening')"
# )
# async def get_available_slots_enhanced(doctor_id: int, date: str, preferred_time: Optional[str] = None) -> Dict[str, Any]:
    
#     # Rate limiting
#     rate_limit_result = handle_rate_limiting(f"get_slots:{doctor_id}")
#     if rate_limit_result:
#         return rate_limit_result
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             target_date = date_parser.parse_natural_language_date(date, "availability")
            
#             doctor = scheduler.get_doctor_by_id(doctor_id)
#             if not doctor:
#                 return {"ok": False, "error": f"Doctor with ID {doctor_id} not found.", "error_code": "DOCTOR_NOT_FOUND"}
            
#             if not scheduler.is_doctor_working_on(doctor, target_date):
#                 working_days = ', '.join(doctor.working_days or [])
#                 return {
#                     "ok": False,
#                     "error": f"Dr. {doctor.name} is not available on {target_date.strftime('%A')}. Working days: {working_days}",
#                     "error_code": "DOCTOR_NOT_WORKING",
#                     "working_days": doctor.working_days
#                 }
            
#             booked_slots = scheduler.get_booked_slots(doctor_id, target_date)
#             available_slots = scheduler.generate_available_slots(
#                 doctor.working_start, doctor.working_end, booked_slots, preferred_time
#             )
            
#             logger.info("Slot availability check completed", 
#                        doctor_id=doctor_id,
#                        date=target_date.isoformat(),
#                        total_available=len(available_slots))
            
#             return {
#                 "ok": True,
#                 "doctor_name": doctor.name,
#                 "date": target_date.isoformat(),
#                 "available_slots": available_slots,
#                 "total_available": len(available_slots),
#                 "booked_slots_count": len(booked_slots),
#                 "working_hours": {
#                     "start": doctor.working_start.strftime("%H:%M"),
#                     "end": doctor.working_end.strftime("%H:%M")
#                 }
#             }
            
#         except InvalidDateError as e:
#             logger.warning(f"Date validation error in slot availability: {e}")
#             return {"ok": False, "error": str(e), "error_code": "INVALID_DATE"}
#         except Exception as e:
#             logger.error(f"Slot availability error: {e}")
#             return {"ok": False, "error": "Failed to get available slots. Please try again.", "error_code": "SYSTEM_ERROR"}

# @function_tool(
#     name="book_appointment_enhanced", 
#     description="Book an appointment with enhanced validation and notifications. Args: patient_id (int), doctor_id (int), date (str, YYYY-MM-DD), start_time (str, HH:MM), send_sms (bool, optional)"
# )
# async def book_appointment_enhanced(patient_id: int, doctor_id: int, date: str, start_time: str, send_sms: bool = True) -> Dict[str, Any]:
    
#     # Rate limiting with stricter limits for booking
#     rate_limit_result = handle_rate_limiting(f"book_appointment:{patient_id}", max_requests=3, window=300)
#     if rate_limit_result:
#         return rate_limit_result
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             target_date = date_parser.parse_natural_language_date(date, "booking")
            
#             appointment = scheduler.book_appointment(
#                 patient_id=patient_id,
#                 doctor_id=doctor_id,
#                 on_date=target_date,
#                 start_time_str=start_time,
#                 send_notification=send_sms,
#                 user_session="phone_agent"
#             )
            
#             logger.info("Appointment booking successful", 
#                        appointment_id=appointment.appointment_id,
#                        patient_id=patient_id,
#                        doctor_id=doctor_id)
            
#             return {
#                 "ok": True,
#                 "appointment": {
#                     "appointment_id": appointment.appointment_id,
#                     "patient_id": appointment.patient_id,
#                     "doctor_id": appointment.doctor_id,
#                     "doctor_name": appointment.doctor.name,
#                     "patient_name": appointment.patient.name,
#                     "date": appointment.appointment_date.isoformat(),
#                     "start_time": appointment.start_time.strftime("%H:%M"),
#                     "end_time": appointment.end_time.strftime("%H:%M"),
#                     "status": appointment.status
#                 },
#                 "confirmation": {
#                     "message": f"Appointment confirmed with Dr. {appointment.doctor.name} on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.start_time.strftime('%I:%M %p')}",
#                     "sms_sent": send_sms,
#                     "appointment_reference": f"APT{appointment.appointment_id:06d}"
#                 }
#             }
            
#         except (SlotUnavailableError, BookingConflictError) as e:
#             logger.warning(f"Appointment booking conflict: {e}")
#             return {"ok": False, "error": str(e), "error_code": "BOOKING_CONFLICT"}
#         except (PatientNotFoundError, DoctorNotFoundError) as e:
#             logger.warning(f"Appointment booking entity error: {e}")
#             return {"ok": False, "error": str(e), "error_code": "ENTITY_NOT_FOUND"}
#         except InvalidDateError as e:
#             logger.warning(f"Date validation error in booking: {e}")
#             return {"ok": False, "error": str(e), "error_code": "INVALID_DATE"}
#         except Exception as e:
#             logger.error(f"Appointment booking error: {e}")
#             return {"ok": False, "error": "Failed to book appointment. Please try again.", "error_code": "SYSTEM_ERROR"}

# @function_tool(
#     name="reschedule_appointment_enhanced", 
#     description="Reschedule an existing appointment with validation and notifications. Args: appointment_id (int), new_date (str, YYYY-MM-DD), new_time (str, HH:MM), send_sms (bool, optional)"
# )
# async def reschedule_appointment_enhanced(appointment_id: int, new_date: str, new_time: str, send_sms: bool = True) -> Dict[str, Any]:
    
#     # Rate limiting
#     rate_limit_result = handle_rate_limiting(f"reschedule:{appointment_id}")
#     if rate_limit_result:
#         return rate_limit_result
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             target_date = date_parser.parse_natural_language_date(new_date, "rescheduling")
            
#             appointment = scheduler.reschedule_appointment(
#                 appointment_id=appointment_id,
#                 new_date=target_date,
#                 new_time_str=new_time,
#                 send_notification=send_sms,
#                 user_session="phone_agent"
#             )
            
#             logger.info("Appointment rescheduling successful", 
#                        appointment_id=appointment_id,
#                        new_date=target_date.isoformat(),
#                        new_time=new_time)
            
#             return {
#                 "ok": True,
#                 "appointment": {
#                     "appointment_id": appointment.appointment_id,
#                     "patient_name": appointment.patient.name,
#                     "doctor_name": appointment.doctor.name,
#                     "new_date": appointment.appointment_date.isoformat(),
#                     "new_time": appointment.start_time.strftime("%H:%M"),
#                     "status": appointment.status
#                 },
#                 "confirmation": {
#                     "message": f"Appointment rescheduled to {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.start_time.strftime('%I:%M %p')}",
#                     "sms_sent": send_sms
#                 }
#             }
            
#         except (SlotUnavailableError, BookingConflictError) as e:
#             logger.warning(f"Appointment rescheduling conflict: {e}")
#             return {"ok": False, "error": str(e), "error_code": "RESCHEDULE_CONFLICT"}
#         except InvalidDateError as e:
#             logger.warning(f"Date validation error in rescheduling: {e}")
#             return {"ok": False, "error": str(e), "error_code": "INVALID_DATE"}
#         except Exception as e:
#             logger.error(f"Appointment rescheduling error: {e}")
#             return {"ok": False, "error": "Failed to reschedule appointment. Please try again.", "error_code": "SYSTEM_ERROR"}

# @function_tool(
#     name="cancel_appointment_enhanced", 
#     description="Cancel an appointment with validation and notifications. Args: appointment_id (int), send_sms (bool, optional)"
# )
# async def cancel_appointment_enhanced(appointment_id: int, send_sms: bool = True) -> Dict[str, Any]:
    
#     # Rate limiting
#     rate_limit_result = handle_rate_limiting(f"cancel:{appointment_id}")
#     if rate_limit_result:
#         return rate_limit_result
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             appointment = scheduler.cancel_appointment(
#                 appointment_id=appointment_id,
#                 send_notification=send_sms,
#                 user_session="phone_agent"
#             )
            
#             if not appointment:
#                 return {"ok": False, "error": f"Appointment {appointment_id} not found or already cancelled.", "error_code": "APPOINTMENT_NOT_FOUND"}
            
#             logger.info("Appointment cancellation successful", 
#                        appointment_id=appointment_id)
            
#             return {
#                 "ok": True,
#                 "appointment_id": appointment_id,
#                 "status": "cancelled",
#                 "confirmation": {
#                     "message": f"Appointment with Dr. {appointment.doctor.name} on {appointment.appointment_date.strftime('%B %d, %Y')} has been cancelled",
#                     "sms_sent": send_sms
#                 }
#             }
            
#         except BookingConflictError as e:
#             logger.warning(f"Appointment cancellation conflict: {e}")
#             return {"ok": False, "error": str(e), "error_code": "CANCELLATION_ERROR"}
#         except Exception as e:
#             logger.error(f"Appointment cancellation error: {e}")
#             return {"ok": False, "error": "Failed to cancel appointment. Please try again.", "error_code": "SYSTEM_ERROR"}

# @function_tool(
#     name="get_appointment_analytics", 
#     description="Get appointment booking analytics for hospital management. Args: days (int, optional - default 30)"
# )
# async def get_appointment_analytics(days: int = 30) -> Dict[str, Any]:
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             analytics = scheduler.get_booking_analytics(days)
            
#             logger.info("Analytics request completed", days=days)
            
#             return {
#                 "ok": True,
#                 "analytics": analytics,
#                 "generated_at": datetime.now().isoformat()
#             }
            
#         except Exception as e:
#             logger.error(f"Analytics generation error: {e}")
#             return {"ok": False, "error": "Failed to generate analytics.", "error_code": "ANALYTICS_ERROR"}

# @function_tool(
#     name="get_doctor_availability", 
#     description="Get doctor availability summary for next N days. Args: doctor_id (int), days_ahead (int, optional - default 7)"
# )
# async def get_doctor_availability(doctor_id: int, days_ahead: int = 7) -> Dict[str, Any]:
    
#     with get_db_session() as session:
#         scheduler = get_scheduler_with_session(session)
#         try:
#             availability = scheduler.get_doctor_availability_summary(doctor_id, days_ahead)
            
#             logger.info("Doctor availability check completed", 
#                        doctor_id=doctor_id, 
#                        days_ahead=days_ahead)
            
#             return {
#                 "ok": True,
#                 "availability_summary": availability
#             }
            
#         except DoctorNotFoundError as e:
#             return {"ok": False, "error": str(e), "error_code": "DOCTOR_NOT_FOUND"}
#         except Exception as e:
#             logger.error(f"Doctor availability error: {e}")
#             return {"ok": False, "error": "Failed to get doctor availability.", "error_code": "SYSTEM_ERROR"}

# # Legacy function tools for backward compatibility
# @function_tool(name="register_patient_legacy", description="Legacy patient registration")
# async def register_patient_legacy(name: str, phone: str, age: Optional[int] = None, location: Optional[str] = None) -> Dict[str, Any]:
#     return register_patient(name, phone, age, location)

# @function_tool(name="find_patient", description="Legacy patient search")
# async def find_patient(q: str) -> Dict[str, Any]:
#     result = find_patient_enhanced(q)
#     if result["ok"]:
#         return {"ok": True, "patients": [{"id": p["patient_id"], "name": p["name"], "phone": p["phone"]} for p in result["patients"]]}
#     return result

# @function_tool(name="get_available_slots", description="Legacy slot availability")
# async def get_available_slots(doctor_id: int, on_date: str) -> Dict[str, Any]:
#     result = get_available_slots_enhanced(doctor_id, on_date)
#     if result["ok"]:
#         return {"ok": True, "slots": result["available_slots"]}
#     return result

# @function_tool(name="book_appointment", description="Legacy appointment booking")
# async def book_appointment(patient_id: int, doctor_id: int, on_date: str, start_time: str) -> Dict[str, Any]:
#     result = book_appointment_enhanced(patient_id, doctor_id, on_date, start_time,True)
# #sjhvfsjf


#     if result["ok"]:
#        return {
#            "ok": True,
#            "appointment": {
#                "appointment_id": result["appointment"]["appointment_id"],
#                "patient_id": result["appointment"]["patient_id"],
#                "doctor_id": result["appointment"]["doctor_id"],
#                "date": result["appointment"]["date"],
#                "start_time": result["appointment"]["start_time"],
#            }
#        }
#     return result

# @function_tool(name="reschedule_appointment", description="Legacy appointment rescheduling")
# async def reschedule_appointment(appointment_id: int, new_date: str, new_time: str) -> Dict[str, Any]:
#    result = reschedule_appointment_enhanced(appointment_id, new_date, new_time, True)
#    if result["ok"]:
#        return {
#            "ok": True,
#            "appointment": {
#                "appointment_id": result["appointment"]["appointment_id"],
#                "patient_id": result["appointment"]["patient_id"],
#                "doctor_id": result["appointment"]["doctor_id"],
#                "date": result["appointment"]["new_date"],
#                "start_time": result["appointment"]["new_time"],
#            }
#        }
#    return result

# @function_tool(name="cancel_appointment", description="Legacy appointment cancellation")
# async def cancel_appointment(appointment_id: int) -> Dict[str, Any]:
#    result = cancel_appointment_enhanced(appointment_id, True)
#    if result["ok"]:
#        return {"ok": True, "id": appointment_id, "status": "cancelled"}
#    return result


# special_function_tools.py

from typing import Optional, Dict, Any, List
from livekit.agents import function_tool
from datetime import date, datetime
from contextlib import contextmanager

# Updated imports for Google Sheets
from scheduler import AppointmentScheduler
from utils.logger import logger
from utils.exceptions import *
from utils.rate_limiter import rate_limiter
from utils.date_parser import date_parser
from utils.language_support import language_manager
from config import settings

# Initialize scheduler with Google Sheets backend
scheduler = AppointmentScheduler()

def handle_rate_limiting(identifier: str, max_requests: int = 5, window: int = 300) -> Optional[Dict[str, Any]]:
    """Handle rate limiting for function calls"""
    if not rate_limiter.is_allowed(identifier, max_requests, window):
        remaining_time = rate_limiter.get_remaining_time(identifier, window)
        return {
            "ok": False, 
            "error": f"Too many requests. Please wait {remaining_time} seconds before trying again.",
            "error_code": "RATE_LIMIT_EXCEEDED"
        }
    return None

@function_tool(
    name="register_patient", 
    description="Register a new patient or update existing patient details. Args: name (str), phone (str), age (int, optional), location (str, optional), language (str, optional - 'en', 'hi', 'ta')"
)
async def register_patient(name: str, phone: str, age: Optional[int] = None, 
                    location: Optional[str] = None, language: str = 'en') -> Dict[str, Any]:
    
    # Rate limiting
    rate_limit_result = handle_rate_limiting(f"register_patient:{phone}")
    if rate_limit_result:
        return rate_limit_result
    
    try:
        patient = scheduler.register_patient(
            name=name, phone=phone, age=age, 
            location=location, language=language
        )
        
        logger.info("Patient registration successful", 
                   patient_id=patient.patient_id, 
                   name=patient.name)
        
        return {
            "ok": True,
            "patient_id": patient.patient_id,
            "name": patient.name,
            "phone": phone,
            "is_new_patient": patient.first_visit,
            "message": language_manager.get_message(
                "patient_registered" if patient.first_visit else "patient_found", 
                language
            )
        }
        
    except (PatientNotFoundError, InvalidDateError) as e:
        logger.warning(f"Patient registration validation error: {e}")
        return {"ok": False, "error": str(e), "error_code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.error(f"Patient registration error: {e}")
        return {"ok": False, "error": "Failed to register patient. Please try again.", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="find_patient_enhanced", 
    description="Find patient by phone number or name with fuzzy matching. Args: query (str) - phone number or name"
)
async def find_patient_enhanced(query: str) -> Dict[str, Any]:
    
    # Rate limiting
    rate_limit_result = handle_rate_limiting(f"find_patient:{query}")
    if rate_limit_result:
        return rate_limit_result
    
    try:
        patients = scheduler.enhanced_patient_search(query)
        
        result = []
        for p in patients:
            result.append({
                "patient_id": p.patient_id,
                "name": p.name,
                "phone": p.phone,
                "age": p.age,
                "location": p.location,
                "preferred_language": p.preferred_language or 'en'
            })
        
        logger.info(f"Patient search completed", query_type="enhanced", results_count=len(result))
        
        return {
            "ok": True,
            "patients": result,
            "count": len(result),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Enhanced patient search error: {e}")
        return {"ok": False, "error": "Search failed. Please try again.", "error_code": "SEARCH_ERROR"}

@function_tool(
    name="get_available_specializations",
    description="Get list of all available medical specializations and their descriptions"
)
async def get_available_specializations() -> Dict[str, Any]:
    try:
        specializations = scheduler.get_all_specializations()
        
        # Enhanced specialization information for the agent
        detailed_specs = {
            "Cardiology": {
                "name": "Cardiology",
                "description": "Heart and cardiovascular system specialists",
                "common_conditions": ["chest pain", "heart problems", "blood pressure", "palpitations"]
            },
            "Orthopedics": {
                "name": "Orthopedics", 
                "description": "Bone, joint, and muscle specialists",
                "common_conditions": ["back pain", "joint pain", "fractures", "arthritis", "sports injuries"]
            },
            "General Medicine": {
                "name": "General Medicine",
                "description": "General health and medical care",
                "common_conditions": ["fever", "general checkup", "diabetes", "hypertension"]
            },
            "Pediatrics": {
                "name": "Pediatrics",
                "description": "Children's health specialists",
                "common_conditions": ["child health", "vaccination", "growth problems", "pediatric care"]
            },
            "Gynecology": {
                "name": "Gynecology", 
                "description": "Women's health and reproductive system",
                "common_conditions": ["women's health", "pregnancy", "menstrual problems", "reproductive health"]
            },
            "Dermatology": {
                "name": "Dermatology",
                "description": "Skin, hair, and nail specialists", 
                "common_conditions": ["skin problems", "acne", "hair loss", "rashes"]
            },
            "Neurology": {
                "name": "Neurology",
                "description": "Nervous system and brain specialists",
                "common_conditions": ["headache", "stroke", "epilepsy", "neurological problems"]
            },
            "ENT": {
                "name": "ENT",
                "description": "Ear, nose, and throat specialists",
                "common_conditions": ["throat pain", "ear problems", "hearing loss", "sinus issues"]
            },
            "Ophthalmology": {
                "name": "Ophthalmology",
                "description": "Eye and vision care specialists",
                "common_conditions": ["eye problems", "vision issues", "cataracts", "eye pain"]
            },
            "Psychiatry": {
                "name": "Psychiatry",
                "description": "Mental health and behavioral specialists",
                "common_conditions": ["depression", "anxiety", "mental health", "stress"]
            }
        }
        
        available_detailed = []
        for spec in specializations:
            if spec in detailed_specs:
                available_detailed.append(detailed_specs[spec])
            else:
                available_detailed.append({
                    "name": spec,
                    "description": f"{spec} specialist",
                    "common_conditions": []
                })
        
        return {
            "ok": True,
            "specializations": available_detailed,
            "count": len(available_detailed)
        }
        
    except Exception as e:
        logger.error(f"Error getting specializations: {e}")
        return {"ok": False, "error": "Failed to get specializations", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="get_doctors_by_specialization",
    description="Get detailed information about doctors for a specific specialization. Args: specialization (str)"
)
async def get_doctors_by_specialization(specialization: str) -> Dict[str, Any]:
    try:
        doctors_info = scheduler.get_doctors_info_by_specialization(specialization)
        
        if not doctors_info:
            return {
                "ok": False,
                "error": f"No doctors found for {specialization}",
                "error_code": "NO_DOCTORS_FOUND",
                "available_specializations": scheduler.get_all_specializations()
            }
        
        # Format for agent communication
        formatted_doctors = []
        for doctor in doctors_info:
            formatted_doctors.append({
                "doctor_id": doctor["doctor_id"],
                "name": doctor["name"],
                "qualification": doctor["qualification"],
                "experience": f"{doctor['experience_years']} years of experience",
                "consultation_fee": f"₹{doctor['consultation_fee']}",
                "working_hours": doctor["working_hours"],
                "working_days": ", ".join(doctor["working_days"]),
                "specializations": ", ".join(doctor["specializations"])
            })
        
        return {
            "ok": True,
            "specialization": specialization,
            "doctors": formatted_doctors,
            "count": len(formatted_doctors),
            "message": f"Found {len(formatted_doctors)} excellent doctors for {specialization}"
        }
        
    except Exception as e:
        logger.error(f"Error getting doctors for {specialization}: {e}")
        return {"ok": False, "error": f"Failed to get doctors for {specialization}", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="recommend_doctor", 
    description="Recommend a doctor based on specialization and desired date with intelligent suggestions. Args: specialization (str), desired_date (str, natural language like 'tomorrow', 'next Monday', '15th December'), patient_id (int, optional), first_visit (bool, optional), patient_location (str, optional)"
)
async def recommend_doctor(specialization: str, desired_date: str, patient_id: Optional[int] = None, 
                    first_visit: bool = True, patient_location: Optional[str] = None) -> Dict[str, Any]:
    
    # Rate limiting
    rate_limit_result = handle_rate_limiting(f"recommend_doctor:{patient_id or 'anonymous'}")
    if rate_limit_result:
        return rate_limit_result
    
    try:
        # Parse date with enhanced validation
        on_date = date_parser.parse_natural_language_date(desired_date, "booking")
        
        # Get current datetime info for better recommendations
        datetime_info = date_parser.get_current_datetime_info()
        
        doctor = scheduler.recommend_doctor(
            patient_id=patient_id,
            specialization=specialization,
            on_date=on_date,
            first_visit=first_visit,
            patient_location=patient_location
        )
        
        if doctor:
            # Get availability for this doctor on the requested date
            available_slots = []
            try:
                booked_slots = scheduler.get_booked_slots(doctor.doctor_id, on_date)
                available_slots = scheduler.generate_available_slots(
                    doctor.working_start, doctor.working_end, booked_slots
                )
            except Exception as e:
                logger.warning(f"Could not get slots for recommended doctor: {e}")
            
            formatted_date = date_parser.format_date_for_display(on_date)
            
            logger.info("Doctor recommendation successful", 
                       doctor_id=doctor.doctor_id,
                       specialization=specialization,
                       date=on_date.isoformat())
            
            return {
                "ok": True,
                "doctor": {
                    "doctor_id": doctor.doctor_id,
                    "name": doctor.name,
                    "qualification": doctor.qualification,
                    "specializations": doctor.specializations,
                    "consultation_fee": doctor.consultation_fee,
                    "experience_years": doctor.experience_years,
                    "working_hours": {
                        "start": doctor.working_start,
                        "end": doctor.working_end,
                        "display": f"{doctor.working_start} to {doctor.working_end}"
                    },
                    "working_days": doctor.working_days
                },
                "date_info": {
                    "requested_date": desired_date,
                    "parsed_date": on_date.isoformat(),
                    "formatted_date": formatted_date,
                    "day_of_week": on_date.strftime("%A")
                },
                "availability": {
                    "total_slots": len(available_slots),
                    "sample_slots": available_slots[:5] if available_slots else [],
                    "is_available": len(available_slots) > 0
                },
                "recommendation_reason": "Based on availability and experience" + (
                    " (continuing with your previous doctor)" if not first_visit and patient_id else ""
                )
            }
        else:
            # Get alternative suggestions
            all_doctors = scheduler.get_doctors_by_specialization(specialization)
            alternatives = []
            
            for alt_doctor in all_doctors[:3]:  # Top 3 alternatives
                try:
                    alt_slots = scheduler.get_booked_slots(alt_doctor.doctor_id, on_date)
                    alt_available = scheduler.generate_available_slots(
                        alt_doctor.working_start, alt_doctor.working_end, alt_slots
                    )
                    if alt_available:
                        alternatives.append({
                            "doctor_id": alt_doctor.doctor_id,
                            "name": alt_doctor.name,
                            "available_slots": len(alt_available),
                            "experience_years": alt_doctor.experience_years
                        })
                except Exception:
                    continue
            
            formatted_date = date_parser.format_date_for_display(on_date)
            
            logger.warning("No doctor found for recommendation", 
                          specialization=specialization, 
                          date=on_date.isoformat())
            
            return {
                "ok": False,
                "error": f"No doctors available for {specialization} on {formatted_date}.",
                "error_code": "NO_DOCTOR_AVAILABLE",
                "alternatives": {
                    "message": f"However, I found these doctors for {specialization}:",
                    "doctors": alternatives,
                    "suggestions": [
                        f"Try a different date - would {(on_date + datetime.timedelta(days=1)).strftime('%A')} work?",
                        "Consider morning or evening slots if available",
                        "I can check availability for the entire week"
                    ]
                }
            }
            
    except InvalidDateError as e:
        logger.warning(f"Date validation error in doctor recommendation: {e}")
        
        # Provide helpful date suggestions
        date_suggestions = date_parser.get_relative_date_suggestions()
        suggestion_text = []
        for desc, date_obj in date_suggestions[:5]:
            suggestion_text.append(f"{desc} ({date_obj.strftime('%B %d')})")
        
        return {
            "ok": False, 
            "error": str(e), 
            "error_code": "INVALID_DATE",
            "date_suggestions": {
                "message": "Here are some date options you can try:",
                "suggestions": suggestion_text
            }
        }
    except Exception as e:
        logger.error(f"Doctor recommendation error: {e}")
        return {"ok": False, "error": "Failed to recommend doctor. Please try again.", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="get_available_slots_enhanced", 
    description="Get available appointment slots for a doctor on a specific date with intelligent ordering and time preferences. Args: doctor_id (int), date (str, natural language), preferred_time (str, optional - 'morning', 'afternoon', 'evening')"
)
async def get_available_slots_enhanced(doctor_id: int, date: str, preferred_time: Optional[str] = None) -> Dict[str, Any]:
    
    # Rate limiting
    rate_limit_result = handle_rate_limiting(f"get_slots:{doctor_id}")
    if rate_limit_result:
        return rate_limit_result
    
    try:
        target_date = date_parser.parse_natural_language_date(date, "availability")
        
        doctor = scheduler.get_doctor_by_id(doctor_id)
        if not doctor:
            return {"ok": False, "error": f"Doctor with ID {doctor_id} not found.", "error_code": "DOCTOR_NOT_FOUND"}
        
        if not scheduler.is_doctor_working_on(doctor, target_date):
            working_days = ', '.join(doctor.working_days or [])
            formatted_date = date_parser.format_date_for_display(target_date)
            return {
                "ok": False,
                "error": f"Dr. {doctor.name} is not available on {formatted_date}. Working days: {working_days}",
                "error_code": "DOCTOR_NOT_WORKING",
                "working_days": doctor.working_days,
                "alternative_dates": [
                    (desc, date_obj.isoformat()) 
                    for desc, date_obj in date_parser.get_relative_date_suggestions(target_date)
                    if scheduler.is_doctor_working_on(doctor, date_obj)
                ][:3]
            }
        
        booked_slots = scheduler.get_booked_slots(doctor_id, target_date)
        available_slots = scheduler.generate_available_slots(
            doctor.working_start, doctor.working_end, booked_slots, preferred_time
        )
        
        # Categorize slots by time of day
        morning_slots = [slot for slot in available_slots if int(slot.split(':')[0]) < 12]
        afternoon_slots = [slot for slot in available_slots if 12 <= int(slot.split(':')[0]) < 17]
        evening_slots = [slot for slot in available_slots if int(slot.split(':')[0]) >= 17]
        
        formatted_date = date_parser.format_date_for_display(target_date)
        
        logger.info("Slot availability check completed", 
                   doctor_id=doctor_id,
                   date=target_date.isoformat(),
                   total_available=len(available_slots))
        
        return {
            "ok": True,
            "doctor": {
                "name": doctor.name,
                "qualification": doctor.qualification,
                "consultation_fee": doctor.consultation_fee
            },
            "date_info": {
                "requested_date": date,
                "parsed_date": target_date.isoformat(),
                "formatted_date": formatted_date,
                "day_of_week": target_date.strftime("%A")
            },
            "availability": {
                "total_available": len(available_slots),
                "all_slots": available_slots,
                "by_time_period": {
                    "morning": {"slots": morning_slots, "count": len(morning_slots)},
                    "afternoon": {"slots": afternoon_slots, "count": len(afternoon_slots)},
                    "evening": {"slots": evening_slots, "count": len(evening_slots)}
                },
                "recommended_slots": available_slots[:6],  # Top 6 recommended slots
                "booked_slots_count": len(booked_slots)
            },
            "working_hours": {
                "start": doctor.working_start,
                "end": doctor.working_end,
                "display": f"{doctor.working_start} to {doctor.working_end}"
            }
        }
        
    except InvalidDateError as e:
        logger.warning(f"Date validation error in slot availability: {e}")
        
        date_suggestions = date_parser.get_relative_date_suggestions()
        return {
            "ok": False, 
            "error": str(e), 
            "error_code": "INVALID_DATE",
            "date_suggestions": [
                f"{desc} ({date_obj.strftime('%B %d')})" 
                for desc, date_obj in date_suggestions[:5]
            ]
        }
    except Exception as e:
        logger.error(f"Slot availability error: {e}")
        return {"ok": False, "error": "Failed to get available slots. Please try again.", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="book_appointment_enhanced", 
    description="Book an appointment with comprehensive validation, confirmation details, and notifications. Args: patient_id (int), doctor_id (int), date (str, natural language), start_time (str, HH:MM), send_sms (bool, optional)"
)
async def book_appointment_enhanced(patient_id: int, doctor_id: int, date: str, start_time: str, send_sms: bool = True) -> Dict[str, Any]:
    
    # Rate limiting with stricter limits for booking
    rate_limit_result = handle_rate_limiting(f"book_appointment:{patient_id}", max_requests=3, window=300)
    if rate_limit_result:
        return rate_limit_result
    
    try:
        target_date = date_parser.parse_natural_language_date(date, "booking")
        
        appointment = scheduler.book_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            on_date=target_date,
            start_time_str=start_time,
            send_notification=send_sms,
            user_session="phone_agent"
        )
        
        # Get comprehensive appointment details
        formatted_date = date_parser.format_date_for_display(target_date)
        
        # Convert 24-hour time to 12-hour format for display
        try:
            time_obj = datetime.strptime(start_time, "%H:%M")
            display_time = time_obj.strftime("%I:%M %p")
        except:
            display_time = start_time
        
        logger.info("Appointment booking successful", 
                   appointment_id=appointment.appointment_id,
                   patient_id=patient_id,
                   doctor_id=doctor_id)
        
        return {
            "ok": True,
            "appointment": {
                "appointment_id": appointment.appointment_id,
                "reference_number": f"APT{appointment.appointment_id:06d}",
                "patient": {
                    "patient_id": appointment.patient_id,
                    "name": appointment.patient_name
                },
                "doctor": {
                    "doctor_id": appointment.doctor_id,
                    "name": appointment.doctor_name
                },
                "schedule": {
                    "date": appointment.appointment_date,
                    "start_time": appointment.start_time,
                    "end_time": appointment.end_time,
                    "formatted_date": formatted_date,
                    "display_time": display_time,
                    "day_of_week": target_date.strftime("%A")
                },
                "status": appointment.status,
                "booking_source": "phone"
            },
            "confirmation": {
                "message": f"Appointment confirmed with Dr. {appointment.doctor_name} on {formatted_date} at {display_time}",
                "instructions": [
                    "Please arrive 15 minutes early",
                    "Bring a valid ID and any previous medical reports",
                    "You will receive an SMS confirmation shortly"
                ],
                "reference_number": f"APT{appointment.appointment_id:06d}",
                "sms_sent": send_sms
            },
            "next_steps": {
                "cancellation": "Call us to cancel if needed",
                "rescheduling": "Call us to reschedule if needed", 
                "preparation": "Bring relevant medical history and reports"
            }
        }
        
    except (SlotUnavailableError, BookingConflictError) as e:
        logger.warning(f"Appointment booking conflict: {e}")
        
        # Try to suggest alternative slots
        try:
            target_date = date_parser.parse_natural_language_date(date, "booking")
            doctor = scheduler.get_doctor_by_id(doctor_id)
            if doctor:
                booked_slots = scheduler.get_booked_slots(doctor_id, target_date)
                available_alternatives = scheduler.generate_available_slots(
                    doctor.working_start, doctor.working_end, booked_slots
                )
                
                return {
                    "ok": False, 
                    "error": str(e), 
                    "error_code": "BOOKING_CONFLICT",
                    "alternatives": {
                        "message": f"The {start_time} slot is not available, but here are other options:",
                        "available_slots": available_alternatives[:6],
                        "date": date_parser.format_date_for_display(target_date)
                    }
                }
        except:
            pass
        
        return {"ok": False, "error": str(e), "error_code": "BOOKING_CONFLICT"}
        
    except (PatientNotFoundError, DoctorNotFoundError) as e:
        logger.warning(f"Appointment booking entity error: {e}")
        return {"ok": False, "error": str(e), "error_code": "ENTITY_NOT_FOUND"}
    except InvalidDateError as e:
        logger.warning(f"Date validation error in booking: {e}")
        return {"ok": False, "error": str(e), "error_code": "INVALID_DATE"}
    except Exception as e:
        logger.error(f"Appointment booking error: {e}")
        return {"ok": False, "error": "Failed to book appointment. Please try again.", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="reschedule_appointment_enhanced", 
    description="Reschedule an existing appointment with validation and comprehensive confirmation. Args: appointment_id (int), new_date (str, natural language), new_time (str, HH:MM), send_sms (bool, optional)"
)
async def reschedule_appointment_enhanced(appointment_id: int, new_date: str, new_time: str, send_sms: bool = True) -> Dict[str, Any]:
    
    # Rate limiting
    rate_limit_result = handle_rate_limiting(f"reschedule:{appointment_id}")
    if rate_limit_result:
        return rate_limit_result
    
    try:
        target_date = date_parser.parse_natural_language_date(new_date, "rescheduling")
        
        # Get current appointment details before rescheduling
        current_appointment = scheduler.sheets.get_appointment_by_id(appointment_id)
        if not current_appointment:
            return {"ok": False, "error": f"Appointment {appointment_id} not found.", "error_code": "APPOINTMENT_NOT_FOUND"}
        
        old_date_formatted = date_parser.format_date_for_display(
            datetime.strptime(current_appointment.appointment_date, "%Y-%m-%d").date()
        )
        old_time_display = datetime.strptime(current_appointment.start_time, "%H:%M").strftime("%I:%M %p")
        
        appointment = scheduler.reschedule_appointment(
            appointment_id=appointment_id,
            new_date=target_date,
            new_time_str=new_time,
            send_notification=send_sms,
            user_session="phone_agent"
        )
        
        formatted_date = date_parser.format_date_for_display(target_date)
        display_time = datetime.strptime(new_time, "%H:%M").strftime("%I:%M %p")
        
        logger.info("Appointment rescheduling successful", 
                   appointment_id=appointment_id,
                   new_date=target_date.isoformat(),
                   new_time=new_time)
        
        return {
            "ok": True,
            "appointment": {
                "appointment_id": appointment.appointment_id,
                "reference_number": f"APT{appointment.appointment_id:06d}",
                "patient_name": appointment.patient_name,
                "doctor_name": appointment.doctor_name,
                "old_schedule": {
                    "date": old_date_formatted,
                    "time": old_time_display
                },
                "new_schedule": {
                    "date": appointment.appointment_date,
                    "start_time": appointment.start_time,
                    "end_time": appointment.end_time,
                    "formatted_date": formatted_date,
                    "display_time": display_time,
                    "day_of_week": target_date.strftime("%A")
                },
                "status": appointment.status
            },
            "confirmation": {
                "message": f"Appointment successfully rescheduled from {old_date_formatted} at {old_time_display} to {formatted_date} at {display_time}",
                "instructions": [
                    "Please arrive 15 minutes early for your new appointment time",
                    "Bring a valid ID and any previous medical reports",
                    "You will receive an SMS confirmation for the new schedule"
                ],
                "sms_sent": send_sms
            }
        }
        
    except (SlotUnavailableError, BookingConflictError) as e:
        logger.warning(f"Appointment rescheduling conflict: {e}")
        
        # Suggest alternative slots for rescheduling
        try:
            target_date = date_parser.parse_natural_language_date(new_date, "rescheduling")
            current_appointment = scheduler.sheets.get_appointment_by_id(appointment_id)
            if current_appointment:
                doctor = scheduler.get_doctor_by_id(current_appointment.doctor_id)
                if doctor:
                    booked_slots = scheduler.get_booked_slots(current_appointment.doctor_id, target_date)
                    available_alternatives = scheduler.generate_available_slots(
                        doctor.working_start, doctor.working_end, booked_slots
                    )
                    
                    return {
                        "ok": False, 
                        "error": str(e), 
                        "error_code": "RESCHEDULE_CONFLICT",
                        "alternatives": {
                            "message": f"The {new_time} slot on {new_date} is not available. Here are other options:",
                            "available_slots": available_alternatives[:6],
                            "date": date_parser.format_date_for_display(target_date)
                        }
                    }
        except:
            pass
            
        return {"ok": False, "error": str(e), "error_code": "RESCHEDULE_CONFLICT"}
    except InvalidDateError as e:
        logger.warning(f"Date validation error in rescheduling: {e}")
        return {"ok": False, "error": str(e), "error_code": "INVALID_DATE"}
    except Exception as e:
        logger.error(f"Appointment rescheduling error: {e}")
        return {"ok": False, "error": "Failed to reschedule appointment. Please try again.", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="cancel_appointment_enhanced", 
    description="Cancel an appointment with validation, confirmation details, and notifications. Args: appointment_id (int), send_sms (bool, optional)"
)
async def cancel_appointment_enhanced(appointment_id: int, send_sms: bool = True) -> Dict[str, Any]:
    
    # Rate limiting
    rate_limit_result = handle_rate_limiting(f"cancel:{appointment_id}")
    if rate_limit_result:
        return rate_limit_result
    
    try:
        # Get appointment details before cancellation
        current_appointment = scheduler.sheets.get_appointment_by_id(appointment_id)
        if not current_appointment:
            return {"ok": False, "error": f"Appointment {appointment_id} not found or already cancelled.", "error_code": "APPOINTMENT_NOT_FOUND"}
        
        # Format date and time for display
        appointment_date_obj = datetime.strptime(current_appointment.appointment_date, "%Y-%m-%d").date()
        formatted_date = date_parser.format_date_for_display(appointment_date_obj)
        display_time = datetime.strptime(current_appointment.start_time, "%H:%M").strftime("%I:%M %p")
        
        appointment = scheduler.cancel_appointment(
            appointment_id=appointment_id,
            send_notification=send_sms,
            user_session="phone_agent"
        )
        
        if not appointment:
            return {"ok": False, "error": f"Appointment {appointment_id} not found or already cancelled.", "error_code": "APPOINTMENT_NOT_FOUND"}
        
        logger.info("Appointment cancellation successful", 
                   appointment_id=appointment_id)
        
        return {
            "ok": True,
            "cancellation": {
                "appointment_id": appointment_id,
                "reference_number": f"APT{appointment_id:06d}",
                "patient_name": appointment.patient_name,
                "doctor_name": appointment.doctor_name,
                "cancelled_schedule": {
                    "date": formatted_date,
                    "time": display_time,
                    "day_of_week": appointment_date_obj.strftime("%A")
                },
                "status": "cancelled",
                "cancellation_time": datetime.now().strftime("%I:%M %p on %B %d, %Y")
            },
            "confirmation": {
                "message": f"Appointment with Dr. {appointment.doctor_name} on {formatted_date} at {display_time} has been successfully cancelled",
                "instructions": [
                    "You will receive an SMS confirmation of the cancellation",
                    "No cancellation fee will be charged",
                    "You can book a new appointment anytime"
                ],
                "sms_sent": send_sms
            },
            "rebooking_help": {
                "message": "Would you like to book a new appointment?",
                "options": [
                    "Book with the same doctor for a different date",
                    "Book with a different specialist",
                    "Call back later to book"
                ]
            }
        }
        
    except BookingConflictError as e:
        logger.warning(f"Appointment cancellation conflict: {e}")
        return {"ok": False, "error": str(e), "error_code": "CANCELLATION_ERROR"}
    except Exception as e:
        logger.error(f"Appointment cancellation error: {e}")
        return {"ok": False, "error": "Failed to cancel appointment. Please try again.", "error_code": "SYSTEM_ERROR"}

@function_tool(
    name="get_appointment_analytics", 
    description="Get appointment booking analytics for hospital management. Args: days (int, optional - default 30)"
)
async def get_appointment_analytics(days: int = 30) -> Dict[str, Any]:
    
    try:
        analytics = scheduler.get_booking_analytics(days)
        
        logger.info("Analytics request completed", days=days)
        
        return {
            "ok": True,
            "analytics": analytics,
            "generated_at": datetime.now().isoformat(),
            "period": f"Last {days} days"
        }
        
    except Exception as e:
        logger.error(f"Analytics generation error: {e}")
        return {"ok": False, "error": "Failed to generate analytics.", "error_code": "ANALYTICS_ERROR"}

@function_tool(
    name="get_doctor_availability", 
    description="Get doctor availability summary for next N days. Args: doctor_id (int), days_ahead (int, optional - default 7)"
)
async def get_doctor_availability(doctor_id: int, days_ahead: int = 7) -> Dict[str, Any]:
    
    try:
        availability = scheduler.get_doctor_availability_summary(doctor_id, days_ahead)
        
        logger.info("Doctor availability check completed", 
                   doctor_id=doctor_id, 
                   days_ahead=days_ahead)
        
        return {
            "ok": True,
            "availability_summary": availability
        }
        
    except DoctorNotFoundError as e:
        return {"ok": False, "error": str(e), "error_code": "DOCTOR_NOT_FOUND"}
    except Exception as e:
        logger.error(f"Doctor availability error: {e}")
        return {"ok": False, "error": "Failed to get doctor availability.", "error_code": "SYSTEM_ERROR"}

# Legacy function tools for backward compatibility (simplified)
@function_tool(name="register_patient_legacy", description="Legacy patient registration")
async def register_patient_legacy(name: str, phone: str, age: Optional[int] = None, location: Optional[str] = None) -> Dict[str, Any]:
    return await register_patient(name, phone, age, location)

@function_tool(name="find_patient", description="Legacy patient search")  
async def find_patient(q: str) -> Dict[str, Any]:
    result = await find_patient_enhanced(q)
    if result["ok"]:
        return {"ok": True, "patients": [{"id": p["patient_id"], "name": p["name"], "phone": p["phone"]} for p in result["patients"]]}
    return result

@function_tool(name="get_available_slots", description="Legacy slot availability")
async def get_available_slots(doctor_id: int, on_date: str) -> Dict[str, Any]:
    result = await get_available_slots_enhanced(doctor_id, on_date)
    if result["ok"]:
        return {"ok": True, "slots": result["availability"]["all_slots"]}
    return result

@function_tool(name="book_appointment", description="Legacy appointment booking")
async def book_appointment(patient_id: int, doctor_id: int, on_date: str, start_time: str) -> Dict[str, Any]:
    result = await book_appointment_enhanced(patient_id, doctor_id, on_date, start_time, True)
    if result["ok"]:
        return {
            "ok": True,
            "appointment": {
                "appointment_id": result["appointment"]["appointment_id"],
                "patient_id": result["appointment"]["patient"]["patient_id"],
                "doctor_id": result["appointment"]["doctor"]["doctor_id"],
                "date": result["appointment"]["schedule"]["date"],
                "start_time": result["appointment"]["schedule"]["start_time"],
            }
        }
    return result

@function_tool(name="reschedule_appointment", description="Legacy appointment rescheduling")
async def reschedule_appointment(appointment_id: int, new_date: str, new_time: str) -> Dict[str, Any]:
    result = await reschedule_appointment_enhanced(appointment_id, new_date, new_time, True)
    if result["ok"]:
        return {
            "ok": True,
            "appointment": {
                "appointment_id": result["appointment"]["appointment_id"],
                "date": result["appointment"]["new_schedule"]["date"],
                "start_time": result["appointment"]["new_schedule"]["start_time"],
            }
        }
    return result

@function_tool(name="cancel_appointment", description="Legacy appointment cancellation")
async def cancel_appointment(appointment_id: int) -> Dict[str, Any]:
    result = await cancel_appointment_enhanced(appointment_id, True)
    if result["ok"]:
        return {"ok": True, "id": appointment_id, "status": "cancelled"}
    return result

    