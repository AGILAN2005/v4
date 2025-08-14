#ORM.py

# =========================
# ORM Models (Enhanced)
# =========================

from datetime import datetime, time
from sqlalchemy import (
    Column, Integer, String, Time, ARRAY, Text, Boolean, ForeignKey, 
    TIMESTAMP, UniqueConstraint, Date, Table, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Association table for the many-to-many relationship between doctors and specializations
doctor_specializations_table = Table(
    'doctor_specializations', Base.metadata,
    Column('doctor_id', Integer, ForeignKey('doctors.doctor_id', ondelete="CASCADE"), primary_key=True),
    Column('specialization_id', Integer, ForeignKey('specializations.specialization_id', ondelete="CASCADE"), primary_key=True)
)

class Specialization(Base):
    __tablename__ = 'specializations'
    specialization_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    qualification = Column(String(100))
    working_start = Column(Time, default=time(10, 0))
    working_end = Column(Time, default=time(21, 0))
    working_days = Column(ARRAY(Text), default=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
    is_active = Column(Boolean, default=True)
    consultation_fee = Column(Integer, default=500)  # Fee in INR
    experience_years = Column(Integer, default=0)
    
    # Many-to-many relationship to Specialization via the association table
    specializations = relationship("Specialization", secondary=doctor_specializations_table, backref="doctors")
    appointments = relationship("Appointment", back_populates="doctor")

    # Ensure a doctor is not added twice based on name and qualification
    __table_args__ = (
        UniqueConstraint('name', 'qualification', name='_name_qualification_uc'),
        Index('idx_doctor_active', 'is_active'),
    )

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False, unique=True, index=True)
    phone_hash = Column(String(64), index=True)  # For secure searching
    age = Column(Integer)
    location = Column(String(150))
    first_visit = Column(Boolean, default=True)
    visit_type = Column(String(20))  # consultation / follow_up
    preferred_language = Column(String(5), default='en')
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    appointments = relationship("Appointment", back_populates="patient")
    
    __table_args__ = (
        Index('idx_patient_phone_hash', 'phone_hash'),
        Index('idx_patient_active', 'is_active'),
    )

class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"))
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id", ondelete="CASCADE"))
    appointment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), default='scheduled')  # scheduled, confirmed, cancelled, completed
    booking_source = Column(String(20), default='phone')  # phone, web, mobile_app
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("doctor_id", "appointment_date", "start_time", name="unique_slot"),
        Index('idx_appointment_date_status', 'appointment_date', 'status'),
        Index('idx_appointment_patient_date', 'patient_id', 'appointment_date'),
    )

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(Integer, primary_key=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    user_session = Column(String(100))  # Agent session ID
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    old_values = Column(Text)  # JSON string of old values
    new_values = Column(Text)  # JSON string of new values
    ip_address = Column(String(45))
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_table_record', 'table_name', 'record_id'),
    )

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    setting_id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)