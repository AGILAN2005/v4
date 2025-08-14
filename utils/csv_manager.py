# utils/csv_manager.py

import pandas as pd
import os
import threading
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

from utils.logger import logger

# --- Data Structures ---
@dataclass
class Patient:
    patient_id: Optional[int] = None
    name: str = ""
    phone: str = ""
    age: Optional[int] = None
    location: Optional[str] = None
    first_visit: bool = True
    preferred_language: str = 'en'

@dataclass
class Doctor:
    doctor_id: Optional[int] = None
    name: str = ""
    qualification: str = ""
    specializations: List[str] = None
    working_start: str = "09:00"
    working_end: str = "18:00"
    working_days: List[str] = None
    consultation_fee: int = 500
    experience_years: int = 5

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
    patient: Optional[Patient] = None
    doctor: Optional[Doctor] = None

# --- CSVManager Class ---
class CSVManager:
    def __init__(self, data_folder='data'):
        self.data_folder = data_folder
        os.makedirs(self.data_folder, exist_ok=True)

        # Define file paths
        self.doctors_file = os.path.join(self.data_folder, 'doctors.csv')
        self.patients_file = os.path.join(self.data_folder, 'patients.csv')
        self.appointments_file = os.path.join(self.data_folder, 'appointments.csv')

        self.lock = threading.Lock()

        # Define columns for each CSV
        self.doctor_cols = ['doctor_id', 'name', 'qualification', 'specializations', 'working_start', 'working_end', 'working_days', 'is_active', 'consultation_fee', 'experience_years']
        self.patient_cols = ['patient_id', 'name', 'phone', 'age', 'location', 'first_visit', 'preferred_language']
        self.appointment_cols = ['appointment_id', 'patient_id', 'doctor_id', 'patient_name', 'doctor_name', 'appointment_date', 'start_time', 'end_time', 'status']

        # Load data into pandas DataFrames
        self.doctors_df = self._load_csv(self.doctors_file, self.doctor_cols)
        self.patients_df = self._load_csv(self.patients_file, self.patient_cols)
        self.appointments_df = self._load_csv(self.appointments_file, self.appointment_cols)

    def _load_csv(self, file_path, columns):
        with self.lock:
            if os.path.exists(file_path):
                logger.info(f"Loading data from {file_path}")
                return pd.read_csv(file_path)
            else:
                logger.info(f"Creating new data file: {file_path}")
                return pd.DataFrame(columns=columns)

    def _save_csv(self, df, file_path):
        with self.lock:
            df.to_csv(file_path, index=False)

    def _get_next_id(self, df, id_column):
        if df.empty or id_column not in df.columns or df[id_column].isnull().all():
            return 1
        return int(df[id_column].max()) + 1

    def _row_to_doctor(self, row) -> Doctor:
        return Doctor(
            doctor_id=row.get('doctor_id'),
            name=row.get('name'),
            qualification=row.get('qualification'),
            specializations=row.get('specializations', '').split(',') if row.get('specializations') else [],
            working_start=row.get('working_start'),
            working_end=row.get('working_end'),
            working_days=row.get('working_days', '').split(',') if row.get('working_days') else [],
            consultation_fee=row.get('consultation_fee'),
            experience_years=row.get('experience_years')
        )

    def _row_to_patient(self, row) -> Patient:
        return Patient(
            patient_id=row.get('patient_id'),
            name=row.get('name'),
            phone=row.get('phone'),
            age=row.get('age'),
            location=row.get('location'),
            first_visit=row.get('first_visit'),
            preferred_language=row.get('preferred_language')
        )

    def _row_to_appointment(self, row) -> Appointment:
        return Appointment(
            appointment_id=row.get('appointment_id'),
            patient_id=row.get('patient_id'),
            doctor_id=row.get('doctor_id'),
            patient_name=row.get('patient_name'),
            doctor_name=row.get('doctor_name'),
            appointment_date=row.get('appointment_date'),
            start_time=row.get('start_time'),
            end_time=row.get('end_time'),
            status=row.get('status')
        )

    # --- Doctor Methods ---
    def create_doctor(self, doctor_data: Dict) -> Optional[Doctor]:
        name = doctor_data.get('name')
        if not self.doctors_df[self.doctors_df['name'] == name].empty:
            logger.warning(f"Doctor '{name}' already exists. Skipping.")
            return None

        doctor_id = self._get_next_id(self.doctors_df, 'doctor_id')
        new_record = {
            'doctor_id': doctor_id, 'name': name,
            'qualification': doctor_data.get('qualification', ''),
            'specializations': doctor_data.get('specializations', ''),
            'working_start': '09:00', 'working_end': '18:00',
            'working_days': 'Mon,Tue,Wed,Thu,Fri,Sat',
            'is_active': True, 'consultation_fee': 500, 'experience_years': 5
        }
        self.doctors_df = pd.concat([self.doctors_df, pd.DataFrame([new_record])], ignore_index=True)
        self._save_csv(self.doctors_df, self.doctors_file)
        logger.info(f"Successfully seeded doctor to CSV: {name} (ID: {doctor_id})")
        return self._row_to_doctor(new_record)

    def get_doctors_by_specialization(self, specialization: str) -> List[Doctor]:
        df = self.doctors_df[self.doctors_df['specializations'].str.contains(specialization, case=False, na=False)]
        return [self._row_to_doctor(row) for _, row in df.iterrows()]
        
    def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
        doctor_series = self.doctors_df[self.doctors_df['doctor_id'] == doctor_id]
        if not doctor_series.empty:
            return self._row_to_doctor(doctor_series.iloc[0])
        return None

    def get_all_specializations(self) -> List[str]:
        all_specs = set()
        for spec_list in self.doctors_df['specializations'].dropna():
            for spec in spec_list.split(','):
                all_specs.add(spec.strip())
        return sorted(list(all_specs))

    # --- Patient Methods ---
    def search_patients(self, query: str) -> List[Patient]:
        query_lower = query.lower()
        # Search by name or phone number
        mask = self.patients_df['name'].str.lower().str.contains(query_lower, na=False) | \
               self.patients_df['phone'].astype(str).str.contains(query, na=False)
        df = self.patients_df[mask]
        return [self._row_to_patient(row) for _, row in df.iterrows()]

    def find_patient_by_phone(self, phone: str) -> Optional[Patient]:
        patient_series = self.patients_df[self.patients_df['phone'] == phone]
        if not patient_series.empty:
            return self._row_to_patient(patient_series.iloc[0])
        return None
    
    def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        patient_series = self.patients_df[self.patients_df['patient_id'] == patient_id]
        if not patient_series.empty:
            return self._row_to_patient(patient_series.iloc[0])
        return None

    def create_patient(self, patient_data: Dict) -> Patient:
        patient_id = self._get_next_id(self.patients_df, 'patient_id')
        new_record = {
            'patient_id': patient_id, 'name': patient_data.get('name'),
            'phone': patient_data.get('phone'), 'age': patient_data.get('age'),
            'location': patient_data.get('location'), 'first_visit': True,
            'preferred_language': patient_data.get('preferred_language', 'en')
        }
        self.patients_df = pd.concat([self.patients_df, pd.DataFrame([new_record])], ignore_index=True)
        self._save_csv(self.patients_df, self.patients_file)
        return self._row_to_patient(new_record)

    def update_patient(self, patient_id: int, update_data: Dict) -> bool:
        idx = self.patients_df.index[self.patients_df['patient_id'] == patient_id].tolist()
        if not idx:
            return False
        for key, value in update_data.items():
            self.patients_df.loc[idx[0], key] = value
        self._save_csv(self.patients_df, self.patients_file)
        return True

    # --- Appointment Methods ---
    def create_appointment(self, appointment_data: Dict) -> Appointment:
        appointment_id = self._get_next_id(self.appointments_df, 'appointment_id')
        
        patient = self.get_patient_by_id(appointment_data['patient_id'])
        doctor = self.get_doctor_by_id(appointment_data['doctor_id'])

        new_record = {
            'appointment_id': appointment_id,
            'patient_id': appointment_data.get('patient_id'),
            'doctor_id': appointment_data.get('doctor_id'),
            'patient_name': patient.name if patient else 'N/A',
            'doctor_name': doctor.name if doctor else 'N/A',
            'appointment_date': appointment_data.get('appointment_date'),
            'start_time': appointment_data.get('start_time'),
            'end_time': appointment_data.get('end_time'),
            'status': 'scheduled'
        }
        self.appointments_df = pd.concat([self.appointments_df, pd.DataFrame([new_record])], ignore_index=True)
        self._save_csv(self.appointments_df, self.appointments_file)
        return self._row_to_appointment(new_record)

    def get_appointments_by_doctor_date(self, doctor_id: int, appointment_date: str) -> List[Appointment]:
        mask = (self.appointments_df['doctor_id'] == doctor_id) & \
               (self.appointments_df['appointment_date'] == appointment_date) & \
               (self.appointments_df['status'].isin(['scheduled', 'confirmed']))
        df = self.appointments_df[mask]
        return [self._row_to_appointment(row) for _, row in df.iterrows()]

    def get_appointment_by_id(self, appointment_id: int) -> Optional[Appointment]:
        appointment_series = self.appointments_df[self.appointments_df['appointment_id'] == appointment_id]
        if not appointment_series.empty:
            return self._row_to_appointment(appointment_series.iloc[0])
        return None

    def update_appointment(self, appointment_id: int, update_data: Dict) -> bool:
        idx = self.appointments_df.index[self.appointments_df['appointment_id'] == appointment_id].tolist()
        if not idx:
            return False
        for key, value in update_data.items():
            self.appointments_df.loc[idx[0], key] = value
        self._save_csv(self.appointments_df, self.appointments_file)
        return True

csv_manager = CSVManager()