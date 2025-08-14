# #scheduler.py

# from datetime import datetime, timedelta, date as date_class, time as time_class
# from typing import List, Optional, Dict, Tuple
# import re
# import pandas as pd
# from sqlalchemy import func, desc, and_, or_
# from sqlalchemy.orm import Session

# from ORM import Doctor, Patient, Appointment, Specialization, AuditLog
# from utils.logger import logger
# from utils.exceptions import *
# from utils.cache_manager import cache_manager
# from utils.security import security_manager
# from utils.notifications import notification_manager
# from fuzzywuzzy import fuzz, process
# import json

# # Helper: normalize specialization string -> list of specializations
# def split_specializations(raw: str) -> List[str]:
#     """
#     Splits a specialization cell into separate specialization strings.
#     Handles commas, semicolons, ampersands, slashes and 'and'.
#     Trims whitespace and removes empty parts.
#     """
#     if raw is None:
#         return []
#     s = str(raw)
#     # Replace common delimiters with comma
#     s = re.sub(r'[/;&]| and | & ', ',', s, flags=re.IGNORECASE)
#     parts = [p.strip() for p in s.split(',') if p.strip()]
#     return parts

# class AppointmentScheduler:
#     def __init__(self, db_session: Session, slot_minutes: int = 30):
#         """
#         db_session: a SQLAlchemy session
#         slot_minutes: slot size in minutes
#         """
#         self.db = db_session
#         self.slot_minutes = slot_minutes

#     def _log_action(self, action: str, table_name: str, record_id: int, 
#                    old_values: dict = None, new_values: dict = None, user_session: str = None):
#         """Log actions for audit trail"""
#         try:
#             audit_log = AuditLog(
#                 action=action,
#                 table_name=table_name,
#                 record_id=record_id,
#                 user_session=user_session,
#                 old_values=json.dumps(old_values) if old_values else None,
#                 new_values=json.dumps(new_values) if new_values else None
#             )
#             self.db.add(audit_log)
#             self.db.flush()  # Don't commit here, let the caller handle it
#         except Exception as e:
#             logger.error(f"Failed to log audit trail: {e}")

#     # ---------------------------
#     # Doctor / Patient Utilities
#     # ---------------------------
#     def get_doctors_by_specialization(self, specialization: str, use_cache: bool = True) -> List[Doctor]:
#         """Return doctors who have the given specialization with caching support"""
        
#         # Try cache first
#         if use_cache:
#             cached_doctors = cache_manager.get_cached_doctors_by_specialization(specialization)
#             if cached_doctors:
#                 logger.debug(f"Retrieved {len(cached_doctors)} doctors from cache for {specialization}")
#                 # Convert cached data back to Doctor objects (lightweight)
#                 return [
#                     Doctor(
#                         doctor_id=d["doctor_id"],
#                         name=d["name"],
#                         qualification=d["qualification"],
#                         working_start=datetime.strptime(d["working_start"], "%H:%M:%S").time(),
#                         working_end=datetime.strptime(d["working_end"], "%H:%M:%S").time(),
#                         working_days=d["working_days"]
#                     ) for d in cached_doctors
#                 ]
        
#         # Database query
#         doctors = (self.db.query(Doctor)
#                   .join(Doctor.specializations)
#                   .filter(and_(
#                       Specialization.name == specialization,
#                       Doctor.is_active == True
#                   ))
#                   .all())
        
#         # Cache the result
#         if use_cache and doctors:
#             doctor_data = []
#             for d in doctors:
#                 doctor_data.append({
#                     "doctor_id": d.doctor_id,
#                     "name": d.name,
#                     "qualification": d.qualification,
#                     "working_start": d.working_start.strftime("%H:%M:%S"),
#                     "working_end": d.working_end.strftime("%H:%M:%S"),
#                     "working_days": d.working_days or []
#                 })
#             cache_manager.cache_doctors_by_specialization(specialization, doctor_data)
#             logger.debug(f"Cached {len(doctors)} doctors for {specialization}")
        
#         return doctors

#     def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
#         """Get doctor by ID with active status check"""
#         return self.db.query(Doctor).filter(and_(
#             Doctor.doctor_id == doctor_id,
#             Doctor.is_active == True
#         )).first()

#     def get_patient_by_phone(self, phone: str) -> Optional[Patient]:
#         """Get patient by phone number with security"""
#         if not security_manager.validate_phone_format(phone):
#             raise InvalidDateError("Invalid phone number format")
        
#         return self.db.query(Patient).filter(and_(
#             Patient.phone == phone,
#             Patient.is_active == True
#         )).first()

#     def enhanced_patient_search(self, query: str) -> List[Patient]:
#         """Enhanced patient search with fuzzy matching"""
#         query = security_manager.sanitize_input(query)
        
#         if not query:
#             return []
        
#         # Direct phone number match (highest priority)
#         if query.isdigit() and len(query) >= 7:
#             phone_matches = self.db.query(Patient).filter(and_(
#                 Patient.phone.contains(query),
#                 Patient.is_active == True
#             )).limit(5).all()
#             if phone_matches:
#                 return phone_matches
        
#         # Name-based search with fuzzy matching
#         all_patients = self.db.query(Patient).filter(
#             Patient.is_active == True
#         ).limit(100).all()  # Limit to prevent performance issues
        
#         if not all_patients:
#             return []
        
#         # Fuzzy match on names
#         patient_names = [(p.name, p) for p in all_patients if p.name]
#         matches = process.extractBests(
#             query, patient_names, 
#             scorer=fuzz.token_sort_ratio, 
#             score_cutoff=70, 
#             limit=5
#         )
        
#         return [match[0][1] for match in matches]

#     def register_patient(self, name: str, phone: str, age: int = None,
#                         location: str = None, first_visit: bool = True,
#                         visit_type: Optional[str] = None, language: str = 'en') -> Patient:
#         """Register or update patient with enhanced security and validation"""
        
#         # Input validation and sanitization
#         name = security_manager.sanitize_input(name)
#         phone = security_manager.sanitize_input(phone)
        
#         if not name or not phone:
#             raise PatientNotFoundError("Name and phone number are required")
        
#         if not security_manager.validate_phone_format(phone):
#             raise InvalidDateError("Invalid phone number format")
        
#         # Check for existing patient
#         existing = self.get_patient_by_phone(phone)
#         if existing:
#             # Update basic info if missing or changed
#             old_values = {
#                 "name": existing.name,
#                 "age": existing.age,
#                 "location": existing.location,
#                 "preferred_language": existing.preferred_language
#             }
            
#             updated = False
#             if name and name != existing.name:
#                 existing.name = name
#                 updated = True
#             if age and age != existing.age:
#                 existing.age = age
#                 updated = True
#             if location and location != existing.location:
#                 existing.location = location
#                 updated = True
#             if language != existing.preferred_language:
#                 existing.preferred_language = language
#                 updated = True
            
#             if updated:
#                 existing.updated_at = datetime.utcnow()
#                 self.db.flush()
                
#                 new_values = {
#                     "name": existing.name,
#                     "age": existing.age,
#                     "location": existing.location,
#                     "preferred_language": existing.preferred_language
#                 }
#                 self._log_action("UPDATE", "patients", existing.patient_id, old_values, new_values)
            
#             return existing

#         # Create new patient
#         phone_hash = security_manager.hash_phone(phone)
        
#         patient = Patient(
#             name=name,
#             phone=phone,
#             phone_hash=phone_hash,
#             age=age,
#             location=location,
#             first_visit=first_visit,
#             visit_type=visit_type,
#             preferred_language=language
#         )
        
#         self.db.add(patient)
#         self.db.flush()
        
#         # Log creation
#         new_values = {
#             "name": patient.name,
#             "phone": "***hidden***",  # Don't log full phone
#             "age": patient.age,
#             "location": patient.location
#         }
#         self._log_action("CREATE", "patients", patient.patient_id, None, new_values)
        
#         logger.info(f"New patient registered", patient_id=patient.patient_id, name=name)
#         return patient

#     def get_patient_last_doctor(self, patient_id: int) -> Optional[int]:
#         """Get patient's last visited doctor"""
#         appt = (self.db.query(Appointment)
#                 .filter(and_(
#                     Appointment.patient_id == patient_id,
#                     Appointment.status.in_(['completed', 'scheduled'])
#                 ))
#                 .order_by(
#                     Appointment.appointment_date.desc(), 
#                     Appointment.start_time.desc()
#                 )
#                 .first())
#         return appt.doctor_id if appt else None

#     # ---------------------------
#     # Slot generation & queries
#     # ---------------------------
#     def is_doctor_working_on(self, doctor: Doctor, on_date: date_class) -> bool:
#         """Check if doctor is working on given date"""
#         if not doctor.working_days:
#             return False
        
#         weekday_short = on_date.strftime('%a')  # e.g. 'Tue'
#         return weekday_short in doctor.working_days

#     def get_booked_slots(self, doctor_id: int, on_date: date_class, use_cache: bool = True) -> List[time_class]:
#         """Get booked appointment slots for a doctor on a date with caching"""
        
#         # Try cache first
#         if use_cache:
#             cache_key = f"booked_slots:{doctor_id}:{on_date.isoformat()}"
#             cached_slots = cache_manager.get(cache_key)
#             if cached_slots is not None:
#                 return [datetime.strptime(slot, "%H:%M:%S").time() for slot in cached_slots]
        
#         # Database query
#         rows = (self.db.query(Appointment.start_time)
#                 .filter(and_(
#                     Appointment.doctor_id == doctor_id,
#                     Appointment.appointment_date == on_date,
#                     Appointment.status.in_(['scheduled', 'confirmed'])
#                 ))
#                 .all())
        
#         booked_times = [r[0] for r in rows]
        
#         # Cache the result
#         if use_cache:
#             cache_key = f"booked_slots:{doctor_id}:{on_date.isoformat()}"
#             cached_data = [t.strftime("%H:%M:%S") for t in booked_times]
#             cache_manager.set(cache_key, cached_data, ttl=1800)  # Cache for 30 minutes
        
#         return booked_times

#     def generate_available_slots(self, start_time: time_class, end_time: time_class,
#                                 booked_slots: List[time_class], 
#                                 preferred_time: str = None) -> List[str]:
#         """Generate available slots with intelligent ordering"""
#         slots = []
#         today = datetime.today()
#         current = datetime.combine(today, start_time)
#         end_dt = datetime.combine(today, end_time)
#         delta = timedelta(minutes=self.slot_minutes)
#         booked_set = {b.strftime("%H:%M") for b in booked_slots}

#         # Generate all available slots
#         while current + delta <= end_dt:
#             slot_str = current.strftime("%H:%M")
#             if slot_str not in booked_set:
#                 slots.append(slot_str)
#             current += delta
        
#         if not slots:
#             return []
        
#         # Intelligent slot ordering based on preferences
#         if preferred_time:
#             slots = self._sort_slots_by_preference(slots, preferred_time)
        
#         return slots

#     def _sort_slots_by_preference(self, slots: List[str], preferred_time: str) -> List[str]:
#         """Sort slots based on patient preference"""
#         slot_scores = []
        
#         for slot in slots:
#             score = 100  # Base score
#             hour = int(slot.split(':')[0])
            
#             # Time preference scoring
#             if preferred_time == 'morning' and 9 <= hour <= 12:
#                 score += 30
#             elif preferred_time == 'afternoon' and 13 <= hour <= 16:
#                 score += 30
#             elif preferred_time == 'evening' and 17 <= hour <= 20:
#                 score += 30
            
#             # Avoid typical rush hours
#             if hour in [10, 15]:
#                 score -= 10
            
#             # Prefer round hours and half hours
#             minute = int(slot.split(':')[1])
#             if minute in [0, 30]:
#                 score += 5
            
#             slot_scores.append((slot, score))
        
#         # Sort by score (descending)
#         slot_scores.sort(key=lambda x: x[1], reverse=True)
#         return [slot for slot, score in slot_scores]

#     # ---------------------------
#     # Doctor recommendation with ML-like logic
#     # ---------------------------
#     def get_least_booked_doctor(self, specialization: str, on_date: date_class, 
#                                patient_location: str = None) -> Optional[Doctor]:
#         """Get least booked doctor with location preference"""
#         doctors = self.get_doctors_by_specialization(specialization)
#         if not doctors:
#             return None
        
#         best_doctor = None
#         best_score = -1
        
#         for doctor in doctors:
#             if not self.is_doctor_working_on(doctor, on_date):
#                 continue
                
#             # Base score calculation
#             booking_count = self.db.query(Appointment).filter(and_(
#                 Appointment.doctor_id == doctor.doctor_id,
#                 Appointment.appointment_date == on_date,
#                 Appointment.status.in_(['scheduled', 'confirmed'])
#             )).count()
            
#             # Calculate score (lower bookings = higher score)
#             score = 100 - (booking_count * 10)
            
#             # Experience bonus
#             if doctor.experience_years:
#                 score += min(doctor.experience_years * 2, 20)  # Max 20 points for experience
            
#             # Location preference (if patient location is known)
#             # This is a simplified implementation - in real world, you'd have doctor locations
#             if patient_location and doctor.name:  # Simplified location matching
#                 # This would be more sophisticated in production
#                 score += 5
            
#             if best_doctor is None or score > best_score:
#                 best_doctor = doctor
#                 best_score = score
        
#         return best_doctor

#     def recommend_doctor(self, patient_id: Optional[int], specialization: str,
#                         on_date: date_class, first_visit: bool = True, 
#                         patient_location: str = None) -> Optional[Doctor]:
#         """Intelligent doctor recommendation with patient history consideration"""
        
#         # For follow-up visits, try to get the same doctor
#         if not first_visit and patient_id:
#             last_doc_id = self.get_patient_last_doctor(patient_id)
#             if last_doc_id:
#                 last_doctor = self.get_doctor_by_id(last_doc_id)
#                 if (last_doctor and 
#                     self.is_doctor_working_on(last_doctor, on_date)):
                    
#                     # Check if the last doctor has the required specialization
#                     doctor_specs = {s.name for s in last_doctor.specializations}
#                     if specialization in doctor_specs:
#                         logger.info(f"Recommended same doctor for follow-up", 
#                                    doctor_id=last_doctor.doctor_id, 
#                                    patient_id=patient_id)
#                         return last_doctor
        
#         # For first visits or if last doctor is not available, get least booked
#         recommended = self.get_least_booked_doctor(specialization, on_date, patient_location)
        
#         if recommended:
#             logger.info(f"Recommended doctor based on availability", 
#                        doctor_id=recommended.doctor_id, 
#                        specialization=specialization,
#                        date=on_date.isoformat())
        
#         return recommended

#     # ---------------------------
#     # Enhanced Booking with notifications
#     # ---------------------------
#     def book_appointment(self, patient_id: int, doctor_id: int, on_date: date_class, 
#                         start_time_str: str, duration_minutes: Optional[int] = None,
#                         send_notification: bool = True, user_session: str = None) -> Appointment:
#         """Book appointment with enhanced validation and notifications"""
        
#         duration_minutes = duration_minutes or self.slot_minutes
        
#         try:
#             start_dt_time = datetime.strptime(start_time_str, "%H:%M").time()
#         except ValueError:
#             raise InvalidDateError(f"Invalid time format: {start_time_str}. Use HH:MM format.")
        
#         # Validate entities exist
#         patient = self.db.query(Patient).filter(and_(
#             Patient.patient_id == patient_id,
#             Patient.is_active == True
#         )).first()
#         if not patient:
#             raise PatientNotFoundError(f"Patient with ID {patient_id} not found")
        
#         doctor = self.db.query(Doctor).filter(and_(
#             Doctor.doctor_id == doctor_id,
#             Doctor.is_active == True
#         )).first()
#         if not doctor:
#             raise DoctorNotFoundError(f"Doctor with ID {doctor_id} not found")
        
#         # Validate doctor is working on this date
#         if not self.is_doctor_working_on(doctor, on_date):
#             raise DoctorNotFoundError(f"Dr. {doctor.name} is not available on {on_date.strftime('%A')}")
        
#         # Check for slot conflicts
#         today = datetime.today()
#         end_time_obj = (datetime.combine(today, start_dt_time) + timedelta(minutes=duration_minutes)).time()
        
#         existing_appointment = (self.db.query(Appointment)
#                                .filter(and_(
#                                    Appointment.doctor_id == doctor_id,
#                                    Appointment.appointment_date == on_date,
#                                    Appointment.start_time == start_dt_time,
#                                    Appointment.status.in_(['scheduled', 'confirmed'])
#                                ))
#                                .first())
        
#         if existing_appointment:
#             raise SlotUnavailableError(f"The slot {start_time_str} on {on_date} is already booked")
        
#         # Create appointment
#         appointment = Appointment(
#             patient_id=patient_id,
#             doctor_id=doctor_id,
#             appointment_date=on_date,
#             start_time=start_dt_time,
#             end_time=end_time_obj,
#             status='scheduled',
#             booking_source='phone'
#         )
        
#         self.db.add(appointment)
#         self.db.flush()  # Get the appointment ID
        
#         # Log the booking
#         new_values = {
#             "patient_id": patient_id,
#             "doctor_id": doctor_id,
#             "appointment_date": on_date.isoformat(),
#             "start_time": start_time_str,
#             "status": "scheduled"
#         }
#         self._log_action("CREATE", "appointments", appointment.appointment_id, 
#                         None, new_values, user_session)
        
#         # Invalidate relevant caches
#         cache_manager.invalidate_doctor_slots(doctor_id, on_date.isoformat())
        
#         # Send notification
#         if send_notification:
#             try:
#                 # Refresh the appointment to get related data
#                 self.db.refresh(appointment)
#                 notification_manager.send_appointment_confirmation(appointment)
#             except Exception as e:
#                 logger.error(f"Failed to send appointment confirmation: {e}")
#                 # Don't fail the booking if notification fails
        
#         logger.info(f"Appointment booked successfully", 
#                    appointment_id=appointment.appointment_id,
#                    patient_id=patient_id,
#                    doctor_id=doctor_id,
#                    date=on_date.isoformat(),
#                    time=start_time_str)
        
#         return appointment

#     def reschedule_appointment(self, appointment_id: int, new_date: date_class, 
#                               new_time_str: str, send_notification: bool = True,
#                               user_session: str = None) -> Appointment:
#         """Reschedule appointment with validation and notifications"""
        
#         appointment = self.db.query(Appointment).filter(and_(
#             Appointment.appointment_id == appointment_id,
#             Appointment.status.in_(['scheduled', 'confirmed'])
#         )).first()
        
#         if not appointment:
#             raise BookingConflictError(f"Appointment {appointment_id} not found or cannot be rescheduled")
        
#         # Store old values for notification and audit
#         old_date = appointment.appointment_date
#         old_time = appointment.start_time
#         old_values = {
#             "appointment_date": old_date.isoformat(),
#             "start_time": old_time.strftime("%H:%M")
#         }
        
#         # Validate new time format
#         try:
#             new_start_time = datetime.strptime(new_time_str, "%H:%M").time()
#         except ValueError:
#             raise InvalidDateError(f"Invalid time format: {new_time_str}. Use HH:MM format.")
        
#         # Validate doctor is working on new date
#         doctor = appointment.doctor
#         if not self.is_doctor_working_on(doctor, new_date):
#             raise DoctorNotFoundError(f"Dr. {doctor.name} is not available on {new_date.strftime('%A')}")
        
#         # Check for conflicts at the new slot
#         existing = (self.db.query(Appointment)
#                    .filter(and_(
#                        Appointment.doctor_id == appointment.doctor_id,
#                        Appointment.appointment_date == new_date,
#                        Appointment.start_time == new_start_time,
#                        Appointment.appointment_id != appointment_id,
#                        Appointment.status.in_(['scheduled', 'confirmed'])
#                    ))
#                    .first())
        
#         if existing:
#             raise SlotUnavailableError(f"The slot {new_time_str} on {new_date} is already booked")
        
#         # Update the appointment
#         appointment.appointment_date = new_date
#         appointment.start_time = new_start_time
#         appointment.end_time = (datetime.combine(new_date, new_start_time) + 
#                                timedelta(minutes=self.slot_minutes)).time()
#         appointment.updated_at = datetime.utcnow()
        
#         self.db.flush()
        
#         # Log the change
#         new_values = {
#             "appointment_date": new_date.isoformat(),
#             "start_time": new_time_str
#         }
#         self._log_action("UPDATE", "appointments", appointment_id, 
#                         old_values, new_values, user_session)
        
#         # Invalidate caches for both dates
#         cache_manager.invalidate_doctor_slots(appointment.doctor_id, old_date.isoformat())
#         cache_manager.invalidate_doctor_slots(appointment.doctor_id, new_date.isoformat())
        
#         # Send notification
#         if send_notification:
#             try:
#                 notification_manager.send_reschedule_confirmation(
#                     appointment, 
#                     old_date.strftime('%B %d, %Y'),
#                     old_time.strftime('%I:%M %p')
#                 )
#             except Exception as e:
#                 logger.error(f"Failed to send reschedule notification: {e}")
        
#         logger.info(f"Appointment rescheduled successfully", 
#                    appointment_id=appointment_id,
#                    old_date=old_date.isoformat(),
#                    new_date=new_date.isoformat(),
#                    old_time=old_time.strftime("%H:%M"),
#                    new_time=new_time_str)
        
#         return appointment

#     def cancel_appointment(self, appointment_id: int, send_notification: bool = True,
#                           user_session: str = None) -> Optional[Appointment]:
#         """Cancel appointment with validation and notifications"""
        
#         appointment = self.db.query(Appointment).filter(and_(
#             Appointment.appointment_id == appointment_id,
#             Appointment.status.in_(['scheduled', 'confirmed'])
#         )).first()
        
#         if not appointment:
#             raise BookingConflictError(f"Appointment {appointment_id} not found or already cancelled")
        
#         # Store values for notification before deletion
#         patient_name = appointment.patient.name
#         patient_phone = appointment.patient.phone
#         doctor_name = appointment.doctor.name
#         appointment_date = appointment.appointment_date.strftime('%B %d, %Y')
#         appointment_time = appointment.start_time.strftime('%I:%M %p')
#         doctor_id = appointment.doctor_id
#         date_str = appointment.appointment_date.isoformat()
        
#         # Log the cancellation
#         old_values = {
#             "status": appointment.status,
#             "appointment_date": appointment.appointment_date.isoformat(),
#             "start_time": appointment.start_time.strftime("%H:%M")
#         }
        
#         # Update status instead of deleting (better for audit trail)
#         appointment.status = 'cancelled'
#         appointment.updated_at = datetime.utcnow()
        
#         self.db.flush()
        
#         new_values = {"status": "cancelled"}
#         self._log_action("UPDATE", "appointments", appointment_id, 
#                         old_values, new_values, user_session)
        
#         # Invalidate cache
#         cache_manager.invalidate_doctor_slots(doctor_id, date_str)
        
#         # Send notification
#         if send_notification:
#             try:
#                 notification_manager.send_cancellation_confirmation(
#                     patient_name, patient_phone, doctor_name, 
#                     appointment_date, appointment_time
#                 )
#             except Exception as e:
#                 logger.error(f"Failed to send cancellation notification: {e}")
        
#         logger.info(f"Appointment cancelled successfully", 
#                    appointment_id=appointment_id,
#                    patient_name=patient_name,
#                    doctor_name=doctor_name)
#         return appointment
    
#     def find_patient(self, query: str) -> List[Patient]:
#         """Enhanced patient search with fuzzy matching"""
#         return self.enhanced_patient_search(query)

#     # ---------------------------
#     # Analytics and Reporting
#     # ---------------------------
#     def get_booking_analytics(self, days: int = 30) -> Dict:
#         """Get comprehensive booking analytics"""
#         start_date = date_class.today() - timedelta(days=days)
        
#         # Total bookings
#         total_bookings = self.db.query(Appointment).filter(and_(
#             Appointment.appointment_date >= start_date,
#             Appointment.status.in_(['scheduled', 'confirmed', 'completed'])
#         )).count()
        
#         # Bookings by specialization
#         spec_stats = (self.db.query(
#             Specialization.name, func.count(Appointment.appointment_id)
#         ).join(Doctor, Doctor.specializations.any(Specialization.specialization_id == Specialization.specialization_id))
#          .join(Appointment, Appointment.doctor_id == Doctor.doctor_id)
#          .filter(and_(
#              Appointment.appointment_date >= start_date,
#              Appointment.status.in_(['scheduled', 'confirmed', 'completed'])
#          ))
#          .group_by(Specialization.name)
#          .order_by(desc(func.count(Appointment.appointment_id)))
#          .limit(10).all())
        
#         # Most popular doctors
#         doctor_stats = (self.db.query(
#             Doctor.name, func.count(Appointment.appointment_id)
#         ).join(Appointment)
#          .filter(and_(
#              Appointment.appointment_date >= start_date,
#              Appointment.status.in_(['scheduled', 'confirmed', 'completed'])
#          ))
#          .group_by(Doctor.name)
#          .order_by(desc(func.count(Appointment.appointment_id)))
#          .limit(10).all())
        
#         # Daily booking trends
#         daily_bookings = (self.db.query(
#             Appointment.appointment_date, func.count(Appointment.appointment_id)
#         ).filter(and_(
#             Appointment.appointment_date >= start_date,
#             Appointment.status.in_(['scheduled', 'confirmed', 'completed'])
#         ))
#          .group_by(Appointment.appointment_date)
#          .order_by(Appointment.appointment_date)
#          .all())
        
#         # Cancellation rate
#         total_cancelled = self.db.query(Appointment).filter(and_(
#             Appointment.appointment_date >= start_date,
#             Appointment.status == 'cancelled'
#         )).count()
        
#         cancellation_rate = (total_cancelled / (total_bookings + total_cancelled) * 100) if (total_bookings + total_cancelled) > 0 else 0
        
#         return {
#             "total_bookings": total_bookings,
#             "specialization_stats": dict(spec_stats),
#             "top_doctors": dict(doctor_stats),
#             "daily_trends": {str(date): count for date, count in daily_bookings},
#             "cancellation_rate": round(cancellation_rate, 2),
#             "total_cancelled": total_cancelled,
#             "period_days": days
#         }

#     # ---------------------------
#     # Excel Seeding (Enhanced and idempotent)
#     # ---------------------------
#     def seed_doctors_from_excel(self, excel_path: str):
#         """Enhanced doctor seeding with better error handling"""
#         try:
#             df = pd.read_excel(excel_path, engine='openpyxl')
#             logger.info(f"Loading doctors from {excel_path}, found {len(df)} rows")
#         except Exception as e:
#             logger.error(f"Failed to read Excel file {excel_path}: {e}")
#             return
        
#         added_docs, added_specs, added_links = 0, 0, 0
#         errors = []

#         for idx, row in df.iterrows():
#             try:
#                 name = str(row.get("name", "") or row.get("Name", "")).strip()
#                 qualification = str(row.get("qualification", "") or row.get("Qualification", "")).strip()
#                 raw_spec = row.get("specialization", "") or row.get("Specialization", "")
                
#                 # Handle additional fields if present
#                 experience = row.get("experience_years", 0) or 0
#                 fee = row.get("consultation_fee", 500) or 500
                
#                 specs_list = split_specializations(raw_spec)

#                 if not name or not specs_list:
#                     logger.warning(f"Row {idx}: Missing name or specialization, skipping")
#                     continue

#                 # Step 1: Find or Create the Doctor record
#                 doctor = self.db.query(Doctor).filter(and_(
#                     Doctor.name == name,
#                     Doctor.qualification == qualification
#                 )).first()
                
#                 if not doctor:
#                     doctor = Doctor(
#                         name=name,
#                         qualification=qualification,
#                         experience_years=int(experience) if experience else 0,
#                         consultation_fee=int(fee) if fee else 500
#                     )
#                     self.db.add(doctor)
#                     self.db.flush()
#                     added_docs += 1
#                     logger.debug(f"Added doctor: {name} ({qualification})")
                
#                 # Step 2 & 3: Find or create specializations and link them
#                 for spec_name in specs_list:
#                     spec_name = spec_name.strip()
#                     if not spec_name:
#                         continue
                    
#                     specialization = self.db.query(Specialization).filter(
#                         Specialization.name == spec_name
#                     ).first()
                    
#                     if not specialization:
#                         specialization = Specialization(name=spec_name, is_active=True)
#                         self.db.add(specialization)
#                         self.db.flush()
#                         added_specs += 1
#                         logger.debug(f"Added specialization: {spec_name}")
                    
#                     # Link doctor to specialization if not already linked
#                     if specialization not in doctor.specializations:
#                         doctor.specializations.append(specialization)
#                         added_links += 1
#                         logger.debug(f"Linked {name} to {spec_name}")

#             except Exception as e:
#                 error_msg = f"Error processing row {idx}: {e}"
#                 errors.append(error_msg)
#                 logger.error(error_msg)
#                 continue

#         # Commit all changes
#         try:
#             if any([added_docs, added_specs, added_links]):
#                 self.db.commit()
                
#                 # Invalidate relevant caches
#                 cache_manager.invalidate_pattern("doctors:spec:*")
                
#                 logger.info(f"Seeding completed successfully. Added: {added_docs} doctors, {added_specs} specializations, {added_links} links")
#             else:
#                 logger.info("No new data to add (seeder is idempotent)")
                
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Failed to commit seeding changes: {e}")
#             raise

#         if errors:
#             logger.warning(f"Seeding completed with {len(errors)} errors: {errors[:5]}...")  # Show first 5 errors

#     def get_doctor_availability_summary(self, doctor_id: int, days_ahead: int = 7) -> Dict:
#         """Get doctor availability summary for next N days"""
#         doctor = self.get_doctor_by_id(doctor_id)
#         if not doctor:
#             raise DoctorNotFoundError(f"Doctor with ID {doctor_id} not found")
        
#         today = date_class.today()
#         availability = {}
        
#         for i in range(days_ahead):
#             check_date = today + timedelta(days=i)
            
#             if not self.is_doctor_working_on(doctor, check_date):
#                 availability[check_date.isoformat()] = {
#                     "working": False,
#                     "available_slots": 0,
#                     "booked_slots": 0
#                 }
#                 continue
            
#             booked_slots = self.get_booked_slots(doctor_id, check_date)
#             available_slots = self.generate_available_slots(
#                 doctor.working_start, doctor.working_end, booked_slots
#             )
            
#             availability[check_date.isoformat()] = {
#                 "working": True,
#                 "available_slots": len(available_slots),
#                 "booked_slots": len(booked_slots),
#                 "slots": available_slots[:10]  # First 10 slots
#             }
        
#         return {
#             "doctor_name": doctor.name,
#             "doctor_id": doctor_id,
#             "availability": availability
#         }


# scheduler.py

from datetime import datetime, timedelta, date as date_class, time as time_class
from typing import List, Optional, Dict, Tuple
import re

import pandas as pd
from fuzzywuzzy import fuzz, process
import json

# Comment out PostgreSQL imports for now
# from sqlalchemy import func, desc, and_, or_
# from sqlalchemy.orm import Session
# from ORM import Doctor, Patient, Appointment, Specialization, AuditLog

from utils.logger import logger
from utils.exceptions import *
# from utils.cache_manager import cache_manager  # Commented out Redis dependency
from utils.security import security_manager
from utils.notifications import notification_manager
# from utils.google_sheets_manager import sheets_manager, Patient, Doctor, Appointment
from utils.csv_manager import csv_manager,Patient,Doctor,Appointment
# Helper: normalize specialization string -> list of specializations
def split_specializations(raw: str) -> List[str]:
    """
    Splits a specialization cell into separate specialization strings.
    Handles commas, semicolons, ampersands, slashes and 'and'.
    Trims whitespace and removes empty parts.
    """
    if raw is None:
        return []
    s = str(raw)
    # Replace common delimiters with comma
    s = re.sub(r'[/;&]| and | & ', ',', s, flags=re.IGNORECASE)
    parts = [p.strip() for p in s.split(',') if p.strip()]
    return parts

class AppointmentScheduler:
    def __init__(self, slot_minutes: int = 30):
        """
        Initialize scheduler with Google Sheets backend
        slot_minutes: slot size in minutes
        """
        # self.db = db_session  # Commented out for Google Sheets implementation
        self.slot_minutes = slot_minutes
        # self.sheets = sheets_manager
        self.sheets = csv_manager 

    def _log_action(self, action: str, table_name: str, record_id: int, 
                   old_values: dict = None, new_values: dict = None, user_session: str = None):
        """Log actions for audit trail - simplified for Google Sheets"""
        try:
            # For now, just log to application logs
            # In production, this could be implemented with a separate audit sheet
            logger.info(f"AUDIT: {action} on {table_name} - Record {record_id}", 
                       extra={
                           "old_values": old_values,
                           "new_values": new_values,
                           "user_session": user_session
                       })
        except Exception as e:
            logger.error(f"Failed to log audit trail: {e}")

    # ---------------------------
    # Doctor / Patient Utilities
    # ---------------------------
    def get_doctors_by_specialization(self, specialization: str, use_cache: bool = True) -> List[Doctor]:
        """Return doctors who have the given specialization"""
        
        # For Google Sheets, cache is handled internally by the sheets manager
        doctors = self.sheets.get_doctors_by_specialization(specialization)
        
        logger.debug(f"Found {len(doctors)} doctors for specialization: {specialization}")
        return doctors

    def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """Get doctor by ID with active status check"""
        return self.sheets.get_doctor_by_id(doctor_id)

    def get_patient_by_phone(self, phone: str) -> Optional[Patient]:
        """Get patient by phone number with security"""
        if not security_manager.validate_phone_format(phone):
            raise InvalidDateError("Invalid phone number format")
        
        return self.sheets.find_patient_by_phone(phone)

    def enhanced_patient_search(self, query: str) -> List[Patient]:
        """Enhanced patient search with fuzzy matching"""
        query = security_manager.sanitize_input(query)
        
        if not query:
            return []
        
        # Use Google Sheets search
        return self.sheets.search_patients(query)

    def register_patient(self, name: str, phone: str, age: int = None,
                        location: str = None, first_visit: bool = True,
                        visit_type: Optional[str] = None, language: str = 'en') -> Patient:
        """Register or update patient with enhanced security and validation"""
        
        # Input validation and sanitization
        name = security_manager.sanitize_input(name)
        phone = security_manager.sanitize_input(phone)
        
        if not name or not phone:
            raise PatientNotFoundError("Name and phone number are required")
        
        if not security_manager.validate_phone_format(phone):
            raise InvalidDateError("Invalid phone number format")
        
        # Check for existing patient
        existing = self.get_patient_by_phone(phone)
        if existing:
            # Update basic info if missing or changed
            old_values = {
                "name": existing.name,
                "age": existing.age,
                "location": existing.location,
                "preferred_language": existing.preferred_language
            }
            
            updated = False
            update_data = {}
            
            if name and name != existing.name:
                update_data['name'] = name
                updated = True
            if age and age != existing.age:
                update_data['age'] = age
                updated = True
            if location and location != existing.location:
                update_data['location'] = location
                updated = True
            if language != existing.preferred_language:
                update_data['preferred_language'] = language
                updated = True
            
            if updated:
                self.sheets.update_patient(existing.patient_id, update_data)
                
                new_values = {**old_values, **update_data}
                self._log_action("UPDATE", "patients", existing.patient_id, old_values, new_values)
                
                # Update existing patient object with new values
                for key, value in update_data.items():
                    setattr(existing, key, value)
            
            return existing

        # Create new patient
        patient_data = {
            'name': name,
            'phone': phone,
            'age': age,
            'location': location,
            'first_visit': first_visit,
            'visit_type': visit_type,
            'preferred_language': language
        }
        
        patient = self.sheets.create_patient(patient_data)
        
        if patient:
            # Log creation
            new_values = {
                "name": patient.name,
                "phone": "***hidden***",  # Don't log full phone
                "age": patient.age,
                "location": patient.location
            }
            self._log_action("CREATE", "patients", patient.patient_id, None, new_values)
            
            logger.info(f"New patient registered", patient_id=patient.patient_id, name=name)
        
        return patient

    def get_patient_last_doctor(self, patient_id: int) -> Optional[int]:
        """Get patient's last visited doctor - simplified for Google Sheets"""
        try:
            # This would require querying appointments sheet for this patient
            # For now, return None (no last doctor preference)
            return None
        except Exception as e:
            logger.error(f"Failed to get patient's last doctor: {e}")
            return None

    # ---------------------------
    # Slot generation & queries
    # ---------------------------
    def is_doctor_working_on(self, doctor: Doctor, on_date: date_class) -> bool:
        """Check if doctor is working on given date"""
        if not doctor.working_days:
            return False
        
        weekday_short = on_date.strftime('%a')  # e.g. 'Tue'
        return weekday_short in doctor.working_days

    def get_booked_slots(self, doctor_id: int, on_date: date_class, use_cache: bool = True) -> List[str]:
        """Get booked appointment slots for a doctor on a date"""
        
        try:
            appointments = self.sheets.get_appointments_by_doctor_date(doctor_id, on_date.isoformat())
            booked_times = [apt.start_time for apt in appointments if apt.start_time]
            
            logger.debug(f"Found {len(booked_times)} booked slots for doctor {doctor_id} on {on_date}")
            return booked_times
            
        except Exception as e:
            logger.error(f"Failed to get booked slots: {e}")
            return []

    def generate_available_slots(self, start_time: str, end_time: str,
                                booked_slots: List[str], 
                                preferred_time: str = None) -> List[str]:
        """Generate available slots with intelligent ordering"""
        try:
            slots = []
            
            # Parse time strings
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour, end_min = map(int, end_time.split(':'))
            
            # Create datetime objects for calculation
            today = datetime.today().replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            end_dt = datetime.today().replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
            
            delta = timedelta(minutes=self.slot_minutes)
            booked_set = set(booked_slots)
            
            # Generate all available slots
            current = today
            while current + delta <= end_dt:
                slot_str = current.strftime("%H:%M")
                if slot_str not in booked_set:
                    slots.append(slot_str)
                current += delta
            
            if not slots:
                return []
            
            # Intelligent slot ordering based on preferences
            if preferred_time:
                slots = self._sort_slots_by_preference(slots, preferred_time)
            
            return slots
            
        except Exception as e:
            logger.error(f"Failed to generate available slots: {e}")
            return []

    def _sort_slots_by_preference(self, slots: List[str], preferred_time: str) -> List[str]:
        """Sort slots based on patient preference"""
        slot_scores = []
        
        for slot in slots:
            score = 100  # Base score
            hour = int(slot.split(':')[0])
            
            # Time preference scoring
            if preferred_time == 'morning' and 9 <= hour <= 12:
                score += 30
            elif preferred_time == 'afternoon' and 13 <= hour <= 16:
                score += 30
            elif preferred_time == 'evening' and 17 <= hour <= 20:
                score += 30
            
            # Avoid typical rush hours
            if hour in [10, 15]:
                score -= 10
            
            # Prefer round hours and half hours
            minute = int(slot.split(':')[1])
            if minute in [0, 30]:
                score += 5
            
            slot_scores.append((slot, score))
        
        # Sort by score (descending)
        slot_scores.sort(key=lambda x: x[1], reverse=True)
        return [slot for slot, score in slot_scores]

    # ---------------------------
    # Doctor recommendation with ML-like logic
    # ---------------------------
    def get_least_booked_doctor(self, specialization: str, on_date: date_class, 
                               patient_location: str = None) -> Optional[Doctor]:
        """Get least booked doctor with location preference"""
        doctors = self.get_doctors_by_specialization(specialization)
        if not doctors:
            return None
        
        best_doctor = None
        best_score = -1
        
        for doctor in doctors:
            if not self.is_doctor_working_on(doctor, on_date):
                continue
                
            # Base score calculation
            booked_slots = self.get_booked_slots(doctor.doctor_id, on_date)
            booking_count = len(booked_slots)
            
            # Calculate score (lower bookings = higher score)
            score = 100 - (booking_count * 10)
            
            # Experience bonus
            if doctor.experience_years:
                score += min(doctor.experience_years * 2, 20)  # Max 20 points for experience
            
            # Location preference (if patient location is known)
            # This is a simplified implementation - in real world, you'd have doctor locations
            if patient_location and doctor.name:  # Simplified location matching
                # This would be more sophisticated in production
                score += 5
            
            if best_doctor is None or score > best_score:
                best_doctor = doctor
                best_score = score
        
        return best_doctor

    def recommend_doctor(self, patient_id: Optional[int], specialization: str,
                        on_date: date_class, first_visit: bool = True, 
                        patient_location: str = None) -> Optional[Doctor]:
        """Intelligent doctor recommendation with patient history consideration"""
        
        # For follow-up visits, try to get the same doctor
        if not first_visit and patient_id:
            last_doc_id = self.get_patient_last_doctor(patient_id)
            if last_doc_id:
                last_doctor = self.get_doctor_by_id(last_doc_id)
                if (last_doctor and 
                    self.is_doctor_working_on(last_doctor, on_date)):
                    
                    # Check if the last doctor has the required specialization
                    if specialization in last_doctor.specializations:
                        logger.info(f"Recommended same doctor for follow-up", 
                                   doctor_id=last_doctor.doctor_id, 
                                   patient_id=patient_id)
                        return last_doctor
        
        # For first visits or if last doctor is not available, get least booked
        recommended = self.get_least_booked_doctor(specialization, on_date, patient_location)
        
        if recommended:
            logger.info(f"Recommended doctor based on availability", 
                       doctor_id=recommended.doctor_id, 
                       specialization=specialization,
                       date=on_date.isoformat())
        
        return recommended

    # ---------------------------
    # Enhanced Booking with notifications
    # ---------------------------
    def book_appointment(self, patient_id: int, doctor_id: int, on_date: date_class, 
                        start_time_str: str, duration_minutes: Optional[int] = None,
                        send_notification: bool = True, user_session: str = None) -> Appointment:
        """Book appointment with enhanced validation and notifications"""
        
        duration_minutes = duration_minutes or self.slot_minutes
        
        try:
            # Validate time format
            datetime.strptime(start_time_str, "%H:%M")
        except ValueError:
            raise InvalidDateError(f"Invalid time format: {start_time_str}. Use HH:MM format.")
        
        # Validate entities exist
        patient = self.sheets.get_patient_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(f"Patient with ID {patient_id} not found")
        
        doctor = self.sheets.get_doctor_by_id(doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor with ID {doctor_id} not found")
        
        # Validate doctor is working on this date
        if not self.is_doctor_working_on(doctor, on_date):
            raise DoctorNotFoundError(f"Dr. {doctor.name} is not available on {on_date.strftime('%A')}")
        
        # Check for slot conflicts
        existing_appointments = self.sheets.get_appointments_by_doctor_date(doctor_id, on_date.isoformat())
        
        for existing_apt in existing_appointments:
            if existing_apt.start_time == start_time_str:
                raise SlotUnavailableError(f"The slot {start_time_str} on {on_date} is already booked")
        
        # Calculate end time
        start_dt = datetime.strptime(start_time_str, "%H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_time_str = end_dt.strftime("%H:%M")
        
        # Create appointment
        appointment_data = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'appointment_date': on_date.isoformat(),
            'start_time': start_time_str,
            'end_time': end_time_str,
            'status': 'scheduled',
            'booking_source': 'phone'
        }
        
        appointment = self.sheets.create_appointment(appointment_data)
        
        if not appointment:
            raise Exception("Failed to create appointment in database")
        
        # Log the booking
        new_values = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": on_date.isoformat(),
            "start_time": start_time_str,
            "status": "scheduled"
        }
        self._log_action("CREATE", "appointments", appointment.appointment_id, 
                        None, new_values, user_session)
        
        # Send notification
        if send_notification:
            try:
                appointment.patient = patient
                appointment.doctor = doctor
                notification_manager.send_appointment_confirmation(appointment)
            except Exception as e:
                logger.error(f"Failed to send appointment confirmation: {e}")
                # Don't fail the booking if notification fails
        
        logger.info(f"Appointment booked successfully", 
                   appointment_id=appointment.appointment_id,
                   patient_id=patient_id,
                   doctor_id=doctor_id,
                   date=on_date.isoformat(),
                   time=start_time_str)
        
        return appointment

    def reschedule_appointment(self, appointment_id: int, new_date: date_class, 
                              new_time_str: str, send_notification: bool = True,
                              user_session: str = None) -> Appointment:
        """Reschedule appointment with validation and notifications"""
        
        appointment = self.sheets.get_appointment_by_id(appointment_id)
        
        if not appointment or appointment.status not in ['scheduled', 'confirmed']:
            raise BookingConflictError(f"Appointment {appointment_id} not found or cannot be rescheduled")
        
        # Store old values for notification and audit
        old_date = appointment.appointment_date
        old_time = appointment.start_time
        old_values = {
            "appointment_date": old_date,
            "start_time": old_time
        }
        
        # Validate new time format
        try:
            datetime.strptime(new_time_str, "%H:%M")
        except ValueError:
            raise InvalidDateError(f"Invalid time format: {new_time_str}. Use HH:MM format.")
        
        # Validate doctor is working on new date
        doctor = self.sheets.get_doctor_by_id(appointment.doctor_id)
        if not self.is_doctor_working_on(doctor, new_date):
            raise DoctorNotFoundError(f"Dr. {doctor.name} is not available on {new_date.strftime('%A')}")
        
        # Check for conflicts at the new slot
        existing_appointments = self.sheets.get_appointments_by_doctor_date(appointment.doctor_id, new_date.isoformat())
        
        for existing_apt in existing_appointments:
            if existing_apt.start_time == new_time_str and existing_apt.appointment_id != appointment_id:
                raise SlotUnavailableError(f"The slot {new_time_str} on {new_date} is already booked")
        
        # Calculate new end time
        start_dt = datetime.strptime(new_time_str, "%H:%M")
        end_dt = start_dt + timedelta(minutes=self.slot_minutes)
        new_end_time = end_dt.strftime("%H:%M")
        
        # Update the appointment
        update_data = {
            'appointment_date': new_date.isoformat(),
            'start_time': new_time_str,
            'end_time': new_end_time
        }
        
        success = self.sheets.update_appointment(appointment_id, update_data)
        
        if not success:
            raise Exception("Failed to update appointment")
        
        # Update appointment object
        appointment.appointment_date = new_date.isoformat()
        appointment.start_time = new_time_str
        appointment.end_time = new_end_time
        
        # Log the change
        new_values = {
            "appointment_date": new_date.isoformat(),
            "start_time": new_time_str
        }
        self._log_action("UPDATE", "appointments", appointment_id, 
                        old_values, new_values, user_session)
        
        # Send notification
        if send_notification:
            try:
                notification_manager.send_reschedule_confirmation(
                    appointment, 
                    old_date,
                    old_time
                )
            except Exception as e:
                logger.error(f"Failed to send reschedule notification: {e}")
        
        logger.info(f"Appointment rescheduled successfully", 
                   appointment_id=appointment_id,
                   old_date=old_date,
                   new_date=new_date.isoformat(),
                   old_time=old_time,
                   new_time=new_time_str)
        
        return appointment

    def cancel_appointment(self, appointment_id: int, send_notification: bool = True,
                          user_session: str = None) -> Optional[Appointment]:
        """Cancel appointment with validation and notifications"""
        
        appointment = self.sheets.get_appointment_by_id(appointment_id)
        
        if not appointment or appointment.status not in ['scheduled', 'confirmed']:
            raise BookingConflictError(f"Appointment {appointment_id} not found or already cancelled")
        
        # Store values for notification before updating
        patient_name = appointment.patient_name
        doctor_name = appointment.doctor_name
        appointment_date = appointment.appointment_date
        appointment_time = appointment.start_time
        
        # Log the cancellation
        old_values = {
            "status": appointment.status,
            "appointment_date": appointment.appointment_date,
            "start_time": appointment.start_time
        }
        
        # Update status instead of deleting (better for audit trail)
        update_data = {'status': 'cancelled'}
        success = self.sheets.update_appointment(appointment_id, update_data)
        
        if not success:
            raise Exception("Failed to cancel appointment")
        
        appointment.status = 'cancelled'
        
        new_values = {"status": "cancelled"}
        self._log_action("UPDATE", "appointments", appointment_id, 
                        old_values, new_values, user_session)
        
        # Send notification
        if send_notification:
            try:
                # For Google Sheets, we need to get patient phone from patient record
                patient = self.sheets.get_patient_by_id(appointment.patient_id)
                patient_phone = patient.phone if patient else ""
                
                notification_manager.send_cancellation_confirmation(
                    patient_name, patient_phone, doctor_name, 
                    appointment_date, appointment_time
                )
            except Exception as e:
                logger.error(f"Failed to send cancellation notification: {e}")
        
        logger.info(f"Appointment cancelled successfully", 
                   appointment_id=appointment_id,
                   patient_name=patient_name,
                   doctor_name=doctor_name)
        return appointment
    
    def find_patient(self, query: str) -> List[Patient]:
        """Enhanced patient search with fuzzy matching"""
        return self.enhanced_patient_search(query)

    # ---------------------------
    # Analytics and Reporting
    # ---------------------------
    def get_booking_analytics(self, days: int = 30) -> Dict:
        """Get comprehensive booking analytics"""
        try:
            return self.sheets.get_booking_analytics(days)
        except Exception as e:
            logger.error(f"Failed to get booking analytics: {e}")
            return {
                "total_bookings": 0,
                "specialization_stats": {},
                "top_doctors": {},
                "cancellation_rate": 0,
                "total_cancelled": 0,
                "period_days": days
            }

    def get_doctor_availability_summary(self, doctor_id: int, days_ahead: int = 7) -> Dict:
        """Get doctor availability summary for next N days"""
        doctor = self.get_doctor_by_id(doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor with ID {doctor_id} not found")
        
        today = date_class.today()
        availability = {}
        
        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            
            if not self.is_doctor_working_on(doctor, check_date):
                availability[check_date.isoformat()] = {
                    "working": False,
                    "available_slots": 0,
                    "booked_slots": 0
                }
                continue
            
            booked_slots = self.get_booked_slots(doctor_id, check_date)
            available_slots = self.generate_available_slots(
                doctor.working_start, doctor.working_end, booked_slots
            )
            
            availability[check_date.isoformat()] = {
                "working": True,
                "available_slots": len(available_slots),
                "booked_slots": len(booked_slots),
                "slots": available_slots[:10]  # First 10 slots
            }
        
        return {
            "doctor_name": doctor.name,
            "doctor_id": doctor_id,
            "availability": availability
        }

    # ---------------------------
    # Utility Methods for Agent
    # ---------------------------
    def get_all_specializations(self) -> List[str]:
        """Get all available specializations"""
        return self.sheets.get_all_specializations()
    
    def get_doctors_info_by_specialization(self, specialization: str) -> List[Dict]:
        """Get detailed doctor information for agent communication"""
        doctors = self.get_doctors_by_specialization(specialization)
        
        doctor_info = []
        for doctor in doctors:
            info = {
                "doctor_id": doctor.doctor_id,
                "name": doctor.name,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "consultation_fee": doctor.consultation_fee,
                "specializations": doctor.specializations,
                "working_hours": f"{doctor.working_start} to {doctor.working_end}",
                "working_days": doctor.working_days
            }
            doctor_info.append(info)
        
        return doctor_info

    # ---------------------------
    # Excel/CSV Seeding (for Google Sheets)
    # ---------------------------
    def seed_doctors_from_excel(self, excel_path: str):
        """Seed doctors from Excel file into Google Sheets"""
        try:
            df = pd.read_excel(excel_path, engine='openpyxl')
            logger.info(f"Loading doctors from {excel_path}, found {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to read Excel file {excel_path}: {e}")
            return
        
        added_docs = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                name = str(row.get("name", "") or row.get("Name", "")).strip()
                qualification = str(row.get("qualification", "") or row.get("Qualification", "")).strip()
                raw_spec = row.get("specialization", "") or row.get("Specialization", "")
                
                # Handle additional fields if present
                experience = row.get("experience_years", 0) or 0
                fee = row.get("consultation_fee", 500) or 500
                
                specs_list = split_specializations(raw_spec)

                if not name or not specs_list:
                    logger.warning(f"Row {idx}: Missing name or specialization, skipping")
                    continue

                # Check if doctor already exists (basic check by name)
                existing_doctors = self.sheets.search_patients(name)  # Using patient search as example
                # For doctors, we'd need a similar search method
                
                # Create doctor data
                doctor_data = {
                    'name': name,
                    'qualification': qualification,
                    'specializations': ','.join(specs_list),
                    'experience_years': int(experience) if experience else 0,
                    'consultation_fee': int(fee) if fee else 500,
                    'working_start': '09:00',
                    'working_end': '18:00',
                    'working_days': 'Mon,Tue,Wed,Thu,Fri,Sat',
                    'is_active': True
                }
                
                # For Google Sheets implementation, we'd need to add this to doctors sheet
                # This is simplified - in production you'd have a create_doctor method
                logger.info(f"Would add doctor: {name} with specializations: {specs_list}")
                added_docs += 1

            except Exception as e:
                error_msg = f"Error processing row {idx}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue

        logger.info(f"Seeding completed. Processed: {added_docs} doctors")
        
        if errors:
            logger.warning(f"Seeding completed with {len(errors)} errors: {errors[:5]}...")  # Show first 5 errors
            