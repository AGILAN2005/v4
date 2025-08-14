#utils/notifications.py

from typing import Optional
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config import settings
from utils.logger import logger
from ORM import Appointment

class NotificationManager:
    def __init__(self):
        self.twilio_client = None
        self.from_number = settings.TWILIO_PHONE_NUMBER
        
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        else:
            logger.warning("Twilio credentials not provided, SMS notifications disabled")
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS message"""
        if not self.twilio_client or not self.from_number:
            logger.warning("SMS not sent: Twilio not configured")
            return False
        
        try:
            # Format phone number
            if not to_number.startswith('+'):
                to_number = f'+91{to_number}'
            
            message_instance = self.twilio_client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully", 
                       message_sid=message_instance.sid, 
                       to=to_number[:5] + "****")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio SMS error: {e}")
            return False
        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            return False
    
    def send_appointment_confirmation(self, appointment: Appointment) -> bool:
        """Send appointment confirmation SMS"""
        if not appointment or not appointment.patient or not appointment.doctor:
            return False
        
        patient = appointment.patient
        doctor = appointment.doctor
        
        message = f"""🏥 Apollo Hospitals - Appointment Confirmed

Dear {patient.name},
Your appointment has been booked:

👨‍⚕️ Doctor: {doctor.name}
📅 Date: {appointment.appointment_date.strftime('%B %d, %Y')}
⏰ Time: {appointment.start_time.strftime('%I:%M %p')}

Please arrive 15 minutes early with valid ID.
For changes, call: 1860-500-1066

Thank you for choosing Apollo Hospitals!"""
        
        return self.send_sms(patient.phone, message)
    
    def send_appointment_reminder(self, appointment: Appointment) -> bool:
        """Send appointment reminder SMS"""
        if not appointment or not appointment.patient or not appointment.doctor:
            return False
        
        patient = appointment.patient
        doctor = appointment.doctor
        
        message = f"""🔔 Appointment Reminder - Apollo Hospitals

Dear {patient.name},
This is a reminder for your appointment tomorrow:

👨‍⚕️ Doctor: {doctor.name}
📅 Date: {appointment.appointment_date.strftime('%B %d, %Y')}
⏰ Time: {appointment.start_time.strftime('%I:%M %p')}

Please bring valid ID and any previous medical records.

Apollo Hospitals"""
        
        return self.send_sms(patient.phone, message)
    
    def send_reschedule_confirmation(self, appointment: Appointment, old_date: str, old_time: str) -> bool:
        """Send reschedule confirmation SMS"""
        if not appointment or not appointment.patient or not appointment.doctor:
            return False
        
        patient = appointment.patient
        doctor = appointment.doctor
        
        message = f"""📅 Apollo Hospitals - Appointment Rescheduled

Dear {patient.name},
Your appointment has been rescheduled:

👨‍⚕️ Doctor: {doctor.name}
📅 New Date: {appointment.appointment_date.strftime('%B %d, %Y')}
⏰ New Time: {appointment.start_time.strftime('%I:%M %p')}

Previous appointment: {old_date} at {old_time}

Please arrive 15 minutes early.
Apollo Hospitals"""
        
        return self.send_sms(patient.phone, message)
    
    def send_cancellation_confirmation(self, patient_name: str, patient_phone: str, 
                                     doctor_name: str, appointment_date: str, 
                                     appointment_time: str) -> bool:
        """Send cancellation confirmation SMS"""
        message = f"""❌ Apollo Hospitals - Appointment Cancelled

Dear {patient_name},
Your appointment has been cancelled:

👨‍⚕️ Doctor: {doctor_name}
📅 Date: {appointment_date}
⏰ Time: {appointment_time}

To book a new appointment, call: 1860-500-1066

Thank you,
Apollo Hospitals"""
        
        return self.send_sms(patient_phone, message)

# Global instance
notification_manager = NotificationManager()