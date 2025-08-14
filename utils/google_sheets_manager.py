# utils/google_sheets_manager.py

import json
import os
import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import gspread
from google.oauth2.service_account import Credentials
from utils.logger import logger
from config import settings

@dataclass
class Patient:
    patient_id: Optional[int] = None
    name: str = ""
    phone: str = ""
    age: Optional[int] = None
    location: Optional[str] = None
    first_visit: bool = True
    visit_type: Optional[str] = None
    preferred_language: str = 'en'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True

@dataclass
class Doctor:
    doctor_id: Optional[int] = None
    name: str = ""
    qualification: str = ""
    specializations: List[str] = None
    working_start: str = "10:00"
    working_end: str = "21:00"
    working_days: List[str] = None
    is_active: bool = True
    consultation_fee: int = 500
    experience_years: int = 0
    
    def __post_init__(self):
        if self.specializations is None:
            self.specializations = []
        if self.working_days is None:
            self.working_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

@dataclass
class Appointment:
    appointment_id: Optional[int] = None
    patient_id: int = 0
    doctor_id: int = 0
    patient_name: str = ""
    doctor_name: str = ""
    appointment_date: str = ""
    start_time: str = ""
    end_time: str = ""
    status: str = 'scheduled'
    booking_source: str = 'phone'
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class GoogleSheetsManager:
    def __init__(self):
        self.gc = None
        self.patients_sheet = None
        self.doctors_sheet = None
        self.appointments_sheet = None
        self.specializations_sheet = None
        
        # Sheet configurations
        self.sheets_config = {
            'patients': {
                'headers': ['patient_id', 'name', 'phone', 'age', 'location', 'first_visit', 
                           'visit_type', 'preferred_language', 'created_at', 'updated_at', 'is_active']
            },
            'doctors': {
                'headers': ['doctor_id', 'name', 'qualification', 'specializations', 'working_start',
                           'working_end', 'working_days', 'is_active', 'consultation_fee', 'experience_years']
            },
            'appointments': {
                'headers': ['appointment_id', 'patient_id', 'doctor_id', 'patient_name', 'doctor_name',
                           'appointment_date', 'start_time', 'end_time', 'status', 'booking_source', 
                           'notes', 'created_at', 'updated_at']
            },
            'specializations': {
                'headers': ['specialization_id', 'name', 'description', 'is_active']
            }
        }
        
        self.initialize_connection()
    
    def initialize_connection(self):
        """Initialize Google Sheets connection"""
        try:
            # Load credentials from service account file
            credentials_path = settings.GOOGLE_SHEETS_CREDENTIALS_FILE
            
            if not os.path.exists(credentials_path):
                logger.error(f"Google Sheets credentials file not found: {credentials_path}")
                logger.error("Please download the service account JSON file from Google Cloud Console")
                return False
            
            # Define the scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
            self.gc = gspread.authorize(credentials)
            
            # Open or create the spreadsheet
            try:
                spreadsheet = self.gc.open(settings.GOOGLE_SHEETS_SPREADSHEET_NAME)
                logger.info(f"Connected to existing spreadsheet: {settings.GOOGLE_SHEETS_SPREADSHEET_NAME}")
            except gspread.SpreadsheetNotFound:
                logger.info(f"Creating new spreadsheet: {settings.GOOGLE_SHEETS_SPREADSHEET_NAME}")
                spreadsheet = self.gc.create(settings.GOOGLE_SHEETS_SPREADSHEET_NAME)
                
                # Share with your email (optional)
                if hasattr(settings, 'GOOGLE_SHEETS_SHARE_EMAIL') and settings.GOOGLE_SHEETS_SHARE_EMAIL:
                    spreadsheet.share(settings.GOOGLE_SHEETS_SHARE_EMAIL, perm_type='user', role='editor')
            
            # Initialize worksheets
            self._initialize_worksheets(spreadsheet)
            
            logger.info("Google Sheets connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets connection: {e}")
            return False
    
    # def _initialize_worksheets(self, spreadsheet):
    #     """Initialize all required worksheets"""
    #     for sheet_name, config in self.sheets_config.items():
    #         try:
    #             worksheet = spreadsheet.worksheet(sheet_name)
    #             logger.info(f"Connected to existing worksheet: {sheet_name}")
    #         except gspread.WorksheetNotFound:
    #             logger.info(f"Creating new worksheet: {sheet_name}")
    #             worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(config['headers']))
                
    #             # Add headers
    #             worksheet.insert_row(config['headers'], 1)
    #             logger.info(f"Added headers to {sheet_name}: {config['headers']}")
            
    #         # Store worksheet references
    #         setattr(self, f"{sheet_name}_sheet", worksheet)
        
    #     # Seed initial data if sheets are empty
    #     self._seed_initial_data()
    # In utils/google_sheets_manager.py

    # def _initialize_worksheets(self, spreadsheet):
    #     """Initialize all required worksheets in a more robust way."""
    #     try:
    #         # Get a list of all worksheet titles that already exist
    #         existing_worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
    #     except Exception as e:
    #         logger.error(f"Could not list existing worksheets: {e}")
    #         existing_worksheet_titles = []

    #     for sheet_name, config in self.sheets_config.items():
    #         worksheet = None
    #         if sheet_name in existing_worksheet_titles:
    #             try:
    #                 worksheet = spreadsheet.worksheet(sheet_name)
    #                 logger.info(f"Connected to existing worksheet: {sheet_name}")
    #             except Exception as e:
    #                 logger.error(f"Failed to connect to existing worksheet '{sheet_name}': {e}")
    #         else:
    #             try:
    #                 logger.info(f"Creating new worksheet: {sheet_name}")
    #                 worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(config['headers']))
    #                 # Add headers to the new sheet
    #                 worksheet.insert_row(config['headers'], 1)
    #                 logger.info(f"Added headers to {sheet_name}: {config['headers']}")
    #             except Exception as e:
    #                 logger.error(f"Failed to create new worksheet '{sheet_name}': {e}")
            
    #         # Store worksheet references only if it was successfully created/connected
    #         if worksheet:
    #             setattr(self, f"{sheet_name}_sheet", worksheet)
    #         else:
    #             # Ensure the attribute is None if the worksheet could not be set up
    #             setattr(self, f"{sheet_name}_sheet", None)
    #             logger.error(f"Could not initialize the '{sheet_name}' worksheet. It will be unavailable.")
        
    #     # Seed initial data if sheets are empty
    #     self._seed_initial_data()
# In utils/google_sheets_manager.py, replace the entire _initialize_worksheets function

    def _initialize_worksheets(self, spreadsheet):
        """Initialize all required worksheets with robust error handling."""
        for sheet_name, config in self.sheets_config.items():
            worksheet = None
            try:
                # First, try to get the worksheet.
                worksheet = spreadsheet.worksheet(sheet_name)
                logger.info(f"Connected to existing worksheet: {sheet_name}")

            except gspread.WorksheetNotFound:
                # If it's not found, try to create it.
                logger.info(f"Worksheet '{sheet_name}' not found, attempting to create.")
                try:
                    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(config['headers']))
                    worksheet.insert_row(config['headers'], 1)
                    logger.info(f"Successfully created and added headers to '{sheet_name}'.")
                except gspread.exceptions.APIError as e:
                    # If creating it fails because it *already exists*, it means our initial
                    # check was wrong due to an API lag. We log this and just re-fetch it.
                    if 'already exists' in str(e):
                        logger.warning(f"Worksheet '{sheet_name}' already existed despite not being found. Re-fetching.")
                        worksheet = spreadsheet.worksheet(sheet_name) # This should now succeed.
                    else:
                        # If it's a different API error, we can't recover.
                        logger.error(f"A non-recoverable API error occurred while creating '{sheet_name}': {e}")
            
            except Exception as e:
                logger.error(f"An unexpected error occurred while initializing '{sheet_name}': {e}")

            # Store the worksheet reference. It will be None if any of the steps above failed.
            setattr(self, f"{sheet_name}_sheet", worksheet)

        # Seed initial data if sheets are empty
        self._seed_initial_data()


    def _seed_initial_data(self):
        """Seed initial doctors and specializations data"""
        try:
            # Check if doctors sheet has data (beyond headers)
            doctors_data = self.doctors_sheet.get_all_records()
            
            if not doctors_data:
                logger.info("Seeding initial doctors data...")
                
                # Sample specializations
                specializations_data = [
                    [1, "Cardiology", "Heart and cardiovascular system", True],
                    [2, "Orthopedics", "Bones, joints, ligaments, tendons, and muscles", True],
                    [3, "General Medicine", "General health and medical care", True],
                    [4, "Pediatrics", "Medical care of infants, children, and adolescents", True],
                    [5, "Gynecology", "Women's health and reproductive system", True],
                    [6, "Dermatology", "Skin, hair, and nails", True],
                    [7, "Neurology", "Nervous system disorders", True],
                    [8, "ENT", "Ear, nose, and throat", True],
                    [9, "Ophthalmology", "Eye and vision care", True],
                    [10, "Psychiatry", "Mental health and behavioral disorders", True]
                ]
                
                # Add specializations
                for spec_data in specializations_data:
                    self.specializations_sheet.append_row(spec_data)
                
                # Sample doctors
                sample_doctors = [
                    [1, "Dr. Rajesh Kumar", "MBBS, MD Cardiology", "Cardiology", "09:00", "17:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 1200, 15],
                    [2, "Dr. Priya Sharma", "MBBS, MS Orthopedics", "Orthopedics", "10:00", "18:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 1000, 12],
                    [3, "Dr. Amit Verma", "MBBS, MD Internal Medicine", "General Medicine", "08:00", "16:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 800, 10],
                    [4, "Dr. Sunita Gupta", "MBBS, MD Pediatrics", "Pediatrics", "09:00", "17:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 900, 8],
                    [5, "Dr. Meera Iyer", "MBBS, MD Dermatology", "Dermatology", "10:00", "18:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 800, 7],
                    [6, "Dr. Vikram Singh", "MBBS, DM Neurology", "Neurology", "09:00", "17:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 1500, 20],
                    [7, "Dr. Kavitha Nair", "MBBS, MS Gynecology", "Gynecology", "10:00", "19:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 1100, 11],
                    [8, "Dr. Arjun Reddy", "MBBS, MS ENT", "ENT", "09:00", "17:00", 
                     "Mon,Tue,Wed,Thu,Fri,Sat", True, 850, 9]
                ]
                
                # Add doctors
                for doctor_data in sample_doctors:
                    self.doctors_sheet.append_row(doctor_data)
                
                logger.info("Initial data seeded successfully")
                
        except Exception as e:
            logger.error(f"Failed to seed initial data: {e}")
    
    def _get_next_id(self, sheet, id_column: str) -> int:
        """Get the next available ID for a sheet"""
        try:
            records = sheet.get_all_records()
            if not records:
                return 1
            
            existing_ids = [record.get(id_column, 0) for record in records if record.get(id_column)]
            return max(existing_ids) + 1 if existing_ids else 1
            
        except Exception as e:
            logger.error(f"Failed to get next ID: {e}")
            return 1
    
    # Patient operations
    def create_patient(self, patient_data: Dict) -> Optional[Patient]:
        """Create a new patient record"""
        try:
            patient_id = self._get_next_id(self.patients_sheet, 'patient_id')
            timestamp = datetime.datetime.now().isoformat()
            
            row_data = [
                patient_id,
                patient_data.get('name', ''),
                patient_data.get('phone', ''),
                patient_data.get('age', ''),
                patient_data.get('location', ''),
                patient_data.get('first_visit', True),
                patient_data.get('visit_type', ''),
                patient_data.get('preferred_language', 'en'),
                timestamp,
                timestamp,
                True
            ]
            
            self.patients_sheet.append_row(row_data)
            
            logger.info(f"Created patient: {patient_data.get('name')} (ID: {patient_id})")
            
            return Patient(
                patient_id=patient_id,
                name=patient_data.get('name', ''),
                phone=patient_data.get('phone', ''),
                age=patient_data.get('age'),
                location=patient_data.get('location'),
                first_visit=patient_data.get('first_visit', True),
                preferred_language=patient_data.get('preferred_language', 'en'),
                created_at=timestamp,
                updated_at=timestamp
            )
            
        except Exception as e:
            logger.error(f"Failed to create patient: {e}")
            return None
    
    def find_patient_by_phone(self, phone: str) -> Optional[Patient]:
        """Find patient by phone number"""
        try:
            records = self.patients_sheet.get_all_records()
            
            for record in records:
                if record.get('phone') == phone and record.get('is_active'):
                    return Patient(
                        patient_id=record.get('patient_id'),
                        name=record.get('name', ''),
                        phone=record.get('phone', ''),
                        age=record.get('age'),
                        location=record.get('location'),
                        first_visit=record.get('first_visit', True),
                        preferred_language=record.get('preferred_language', 'en')
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find patient by phone: {e}")
            return None
    
    def search_patients(self, query: str) -> List[Patient]:
        """Search patients by name or phone"""
        try:
            records = self.patients_sheet.get_all_records()
            results = []
            
            query_lower = query.lower()
            
            for record in records:
                if not record.get('is_active'):
                    continue
                    
                name = str(record.get('name', '')).lower()
                phone = str(record.get('phone', ''))
                
                if query_lower in name or query in phone:
                    results.append(Patient(
                        patient_id=record.get('patient_id'),
                        name=record.get('name', ''),
                        phone=record.get('phone', ''),
                        age=record.get('age'),
                        location=record.get('location'),
                        preferred_language=record.get('preferred_language', 'en')
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search patients: {e}")
            return []
    
    def update_patient(self, patient_id: int, update_data: Dict) -> bool:
        """Update patient record"""
        try:
            records = self.patients_sheet.get_all_records()
            
            for i, record in enumerate(records, start=2):  # Start from row 2 (after headers)
                if record.get('patient_id') == patient_id:
                    # Update the specific cells
                    if 'name' in update_data:
                        self.patients_sheet.update_cell(i, 2, update_data['name'])
                    if 'age' in update_data:
                        self.patients_sheet.update_cell(i, 4, update_data['age'])
                    if 'location' in update_data:
                        self.patients_sheet.update_cell(i, 5, update_data['location'])
                    if 'preferred_language' in update_data:
                        self.patients_sheet.update_cell(i, 8, update_data['preferred_language'])
                    
                    # Update timestamp
                    self.patients_sheet.update_cell(i, 10, datetime.datetime.now().isoformat())
                    
                    logger.info(f"Updated patient ID: {patient_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update patient: {e}")
            return False
    
    # Doctor operations
    def get_doctors_by_specialization(self, specialization: str) -> List[Doctor]:
        """Get doctors by specialization"""
        try:
            records = self.doctors_sheet.get_all_records()
            results = []
            
            for record in records:
                if not record.get('is_active'):
                    continue
                
                doctor_specializations = str(record.get('specializations', '')).split(',')
                doctor_specializations = [s.strip() for s in doctor_specializations]
                
                if specialization in doctor_specializations:
                    working_days = str(record.get('working_days', 'Mon,Tue,Wed,Thu,Fri,Sat')).split(',')
                    working_days = [day.strip() for day in working_days]
                    
                    results.append(Doctor(
                        doctor_id=record.get('doctor_id'),
                        name=record.get('name', ''),
                        qualification=record.get('qualification', ''),
                        specializations=doctor_specializations,
                        working_start=record.get('working_start', '10:00'),
                        working_end=record.get('working_end', '18:00'),
                        working_days=working_days,
                        consultation_fee=record.get('consultation_fee', 500),
                        experience_years=record.get('experience_years', 0)
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get doctors by specialization: {e}")
            return []
    
    def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """Get doctor by ID"""
        try:
            records = self.doctors_sheet.get_all_records()
            
            for record in records:
                if record.get('doctor_id') == doctor_id and record.get('is_active'):
                    working_days = str(record.get('working_days', 'Mon,Tue,Wed,Thu,Fri,Sat')).split(',')
                    working_days = [day.strip() for day in working_days]
                    
                    specializations = str(record.get('specializations', '')).split(',')
                    specializations = [s.strip() for s in specializations]
                    
                    return Doctor(
                        doctor_id=record.get('doctor_id'),
                        name=record.get('name', ''),
                        qualification=record.get('qualification', ''),
                        specializations=specializations,
                        working_start=record.get('working_start', '10:00'),
                        working_end=record.get('working_end', '18:00'),
                        working_days=working_days,
                        consultation_fee=record.get('consultation_fee', 500),
                        experience_years=record.get('experience_years', 0)
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get doctor by ID: {e}")
            return None
    
    def get_all_specializations(self) -> List[str]:
        """Get all available specializations"""
        try:
            records = self.specializations_sheet.get_all_records()
            return [record.get('name', '') for record in records if record.get('is_active')]
        except Exception as e:
            logger.error(f"Failed to get specializations: {e}")
            return []
    
    # Appointment operations
    def create_appointment(self, appointment_data: Dict) -> Optional[Appointment]:
        """Create a new appointment"""
        try:
            appointment_id = self._get_next_id(self.appointments_sheet, 'appointment_id')
            timestamp = datetime.datetime.now().isoformat()
            
            # Get patient and doctor names
            patient = self.get_patient_by_id(appointment_data.get('patient_id'))
            doctor = self.get_doctor_by_id(appointment_data.get('doctor_id'))
            
            row_data = [
                appointment_id,
                appointment_data.get('patient_id', ''),
                appointment_data.get('doctor_id', ''),
                patient.name if patient else '',
                doctor.name if doctor else '',
                appointment_data.get('appointment_date', ''),
                appointment_data.get('start_time', ''),
                appointment_data.get('end_time', ''),
                appointment_data.get('status', 'scheduled'),
                appointment_data.get('booking_source', 'phone'),
                appointment_data.get('notes', ''),
                timestamp,
                timestamp
            ]
            
            self.appointments_sheet.append_row(row_data)
            
            logger.info(f"Created appointment ID: {appointment_id}")
            
            return Appointment(
                appointment_id=appointment_id,
                patient_id=appointment_data.get('patient_id'),
                doctor_id=appointment_data.get('doctor_id'),
                patient_name=patient.name if patient else '',
                doctor_name=doctor.name if doctor else '',
                appointment_date=appointment_data.get('appointment_date', ''),
                start_time=appointment_data.get('start_time', ''),
                end_time=appointment_data.get('end_time', ''),
                status=appointment_data.get('status', 'scheduled'),
                created_at=timestamp
            )
            
        except Exception as e:
            logger.error(f"Failed to create appointment: {e}")
            return None
    
    def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        """Get patient by ID"""
        try:
            records = self.patients_sheet.get_all_records()
            
            for record in records:
                if record.get('patient_id') == patient_id and record.get('is_active'):
                    return Patient(
                        patient_id=record.get('patient_id'),
                        name=record.get('name', ''),
                        phone=record.get('phone', ''),
                        age=record.get('age'),
                        location=record.get('location'),
                        preferred_language=record.get('preferred_language', 'en')
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get patient by ID: {e}")
            return None
    
    def get_appointments_by_doctor_date(self, doctor_id: int, appointment_date: str) -> List[Appointment]:
        """Get appointments for a doctor on a specific date"""
        try:
            records = self.appointments_sheet.get_all_records()
            results = []
            
            for record in records:
                if (record.get('doctor_id') == doctor_id and 
                    record.get('appointment_date') == appointment_date and
                    record.get('status') in ['scheduled', 'confirmed']):
                    
                    results.append(Appointment(
                        appointment_id=record.get('appointment_id'),
                        patient_id=record.get('patient_id'),
                        doctor_id=record.get('doctor_id'),
                        patient_name=record.get('patient_name', ''),
                        doctor_name=record.get('doctor_name', ''),
                        appointment_date=record.get('appointment_date', ''),
                        start_time=record.get('start_time', ''),
                        end_time=record.get('end_time', ''),
                        status=record.get('status', ''),
                        notes=record.get('notes', '')
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get appointments: {e}")
            return []
    
    def update_appointment(self, appointment_id: int, update_data: Dict) -> bool:
        """Update appointment record"""
        try:
            records = self.appointments_sheet.get_all_records()
            
            for i, record in enumerate(records, start=2):  # Start from row 2 (after headers)
                if record.get('appointment_id') == appointment_id:
                    # Update the specific cells based on column positions
                    if 'appointment_date' in update_data:
                        self.appointments_sheet.update_cell(i, 6, update_data['appointment_date'])
                    if 'start_time' in update_data:
                        self.appointments_sheet.update_cell(i, 7, update_data['start_time'])
                    if 'end_time' in update_data:
                        self.appointments_sheet.update_cell(i, 8, update_data['end_time'])
                    if 'status' in update_data:
                        self.appointments_sheet.update_cell(i, 9, update_data['status'])
                    if 'notes' in update_data:
                        self.appointments_sheet.update_cell(i, 11, update_data['notes'])
                    
                    # Update timestamp
                    self.appointments_sheet.update_cell(i, 13, datetime.datetime.now().isoformat())
                    
                    logger.info(f"Updated appointment ID: {appointment_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update appointment: {e}")
            return False
    
    def get_appointment_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID"""
        try:
            records = self.appointments_sheet.get_all_records()
            
            for record in records:
                if record.get('appointment_id') == appointment_id:
                    return Appointment(
                        appointment_id=record.get('appointment_id'),
                        patient_id=record.get('patient_id'),
                        doctor_id=record.get('doctor_id'),
                        patient_name=record.get('patient_name', ''),
                        doctor_name=record.get('doctor_name', ''),
                        appointment_date=record.get('appointment_date', ''),
                        start_time=record.get('start_time', ''),
                        end_time=record.get('end_time', ''),
                        status=record.get('status', ''),
                        notes=record.get('notes', ''),
                        created_at=record.get('created_at', '')
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get appointment by ID: {e}")
            return None
    
    def get_booking_analytics(self, days: int = 30) -> Dict:
        """Get basic booking analytics"""
        try:
            records = self.appointments_sheet.get_all_records()
            
            # Calculate date range
            end_date = datetime.datetime.now().date()
            start_date = end_date - datetime.timedelta(days=days)
            
            total_bookings = 0
            cancelled_bookings = 0
            specialization_stats = {}
            doctor_stats = {}
            
            for record in records:
                appointment_date_str = record.get('appointment_date', '')
                if not appointment_date_str:
                    continue
                
                try:
                    appointment_date = datetime.datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                    if start_date <= appointment_date <= end_date:
                        status = record.get('status', '')
                        
                        if status in ['scheduled', 'confirmed', 'completed']:
                            total_bookings += 1
                            
                            # Doctor stats
                            doctor_name = record.get('doctor_name', '')
                            if doctor_name:
                                doctor_stats[doctor_name] = doctor_stats.get(doctor_name, 0) + 1
                        
                        elif status == 'cancelled':
                            cancelled_bookings += 1
                
                except ValueError:
                    continue
            
            cancellation_rate = (cancelled_bookings / (total_bookings + cancelled_bookings) * 100) if (total_bookings + cancelled_bookings) > 0 else 0
            
            return {
                "total_bookings": total_bookings,
                "specialization_stats": specialization_stats,
                "top_doctors": dict(sorted(doctor_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                "cancellation_rate": round(cancellation_rate, 2),
                "total_cancelled": cancelled_bookings,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {
                "total_bookings": 0,
                "specialization_stats": {},
                "top_doctors": {},
                "cancellation_rate": 0,
                "total_cancelled": 0,
                "period_days": days
            }
    def create_doctor(self, doctor_data: Dict) -> Optional[Doctor]:
        """Create a new doctor record in the Google Sheet."""
        try:
            # Check if doctor already exists to avoid duplicates
            existing_doctors = self.doctors_sheet.findall(doctor_data.get('name', ''))
            if existing_doctors:
                logger.warning(f"Doctor '{doctor_data.get('name')}' already exists. Skipping.")
                return None

            doctor_id = self._get_next_id(self.doctors_sheet, 'doctor_id')
            
            # Default values similar to your sample data
            row_data = [
                doctor_id,
                doctor_data.get('name', ''),
                doctor_data.get('qualification', ''),
                doctor_data.get('specializations', ''), # Should be a comma-separated string
                doctor_data.get('working_start', '09:00'),
                doctor_data.get('working_end', '18:00'),
                doctor_data.get('working_days', 'Mon,Tue,Wed,Thu,Fri,Sat'),
                doctor_data.get('is_active', True),
                doctor_data.get('consultation_fee', 500),
                doctor_data.get('experience_years', 5) # Default experience
            ]
            
            self.doctors_sheet.append_row(row_data)
            logger.info(f"Successfully seeded doctor: {doctor_data.get('name')} (ID: {doctor_id})")
            
            # Return a Doctor object
            return Doctor(
                doctor_id=doctor_id,
                name=doctor_data.get('name', ''),
                qualification=doctor_data.get('qualification', ''),
                specializations=doctor_data.get('specializations', '').split(','),
            )

        except Exception as e:
            logger.error(f"Failed to create doctor record for '{doctor_data.get('name')}': {e}")
            return None


# Create global instance
sheets_manager = GoogleSheetsManager()