#main.py
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError
from datetime import date, timedelta
from ORM import Base, Doctor, Patient, Appointment, Specialization, SystemSettings
from scheduler import AppointmentScheduler
from utils.logger import setup_logging
from config import settings

# Setup logging
logger = setup_logging()

# -------------------------
# Enhanced Database Setup
# -------------------------
def create_database_if_not_exists(db_name, user, password, host="localhost", port=5432):
    """Create database with enhanced error handling"""
    admin_db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/postgres"
    
    try:
        engine = create_engine(admin_db_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as connection:
            check_query = text("SELECT 1 FROM pg_database WHERE datname = :db_name")
            exists = connection.execute(check_query, {"db_name": db_name}).scalar()
            
            if not exists:
                try:
                    connection.execute(text(f'CREATE DATABASE "{db_name}"'))
                    logger.info(f"Database '{db_name}' created successfully")
                except ProgrammingError as e:
                    if "already exists" not in str(e):
                        logger.error(f"Could not create database: {e}")
                        raise
            else:
                logger.info(f"Database '{db_name}' already exists")
                
    except Exception as e:
        logger.error(f"Database setup error: {e}")
        raise

def initialize_system_settings(session):
    """Initialize default system settings"""
    default_settings = [
        ("appointment_slot_duration", "30", "Default appointment slot duration in minutes"),
        ("max_advance_booking_days", "90", "Maximum days in advance for booking appointments"),
        ("hospital_working_days", "Mon,Tue,Wed,Thu,Fri,Sat", "Hospital working days"),
        ("emergency_contact", "1066", "Emergency contact number"),
        ("sms_notifications_enabled", "true", "Enable SMS notifications"),
        ("rate_limit_booking", "5", "Maximum booking attempts per 5 minutes"),
        ("cache_ttl_seconds", "1800", "Cache time-to-live in seconds"),
    ]
    
    for key, value, description in default_settings:
        existing = session.query(SystemSettings).filter_by(key=key).first()
        if not existing:
            setting = SystemSettings(key=key, value=value, description=description)
            session.add(setting)
            logger.debug(f"Added system setting: {key}={value}")
    
    session.commit()

def seed_sample_data(session, scheduler):
    """Seed sample data if tables are empty"""
    if session.query(Doctor).count() == 0:
        logger.info("Seeding sample data...")
        
        # Create specializations
        specializations_data = [
            ("Cardiology", "Heart and cardiovascular system"),
            ("Orthopedics", "Bones, joints, ligaments, tendons, and muscles"),
            ("General Medicine", "General health and medical care"),
            ("Pediatrics", "Medical care of infants, children, and adolescents"),
            ("Gynecology", "Women's health and reproductive system"),
            ("Dermatology", "Skin, hair, and nails"),
            ("Neurology", "Nervous system disorders"),
            ("Psychiatry", "Mental health and behavioral disorders"),
            ("ENT", "Ear, nose, and throat"),
            ("Ophthalmology", "Eye and vision care")
        ]
        
        specializations = {}
        for name, desc in specializations_data:
            spec = Specialization(name=name, description=desc, is_active=True)
            session.add(spec)
            specializations[name] = spec
        
        session.flush()
        
        # Create sample doctors
        doctors_data = [
            ("Dr. Rajesh Kumar", "MBBS, MD", ["Cardiology"], 15, 1000),
            ("Dr. Priya Sharma", "MBBS, MS", ["Orthopedics"], 12, 800),
            ("Dr. Amit Verma", "MBBS, MD", ["General Medicine"], 8, 600),
            ("Dr. Sunita Gupta", "MBBS, MD", ["Pediatrics"], 10, 700),
            ("Dr. Vikram Singh", "MBBS, DM", ["Neurology"], 20, 1500),
            ("Dr. Meera Iyer", "MBBS, MD", ["Dermatology"], 7, 650),
            ("Dr. Arjun Reddy", "MBBS, MS", ["ENT"], 9, 750),
            ("Dr. Kavitha Nair", "MBBS, MS", ["Gynecology"], 11, 800),
        ]
        
        for name, qualification, specs, experience, fee in doctors_data:
            doctor = Doctor(
                name=name,
                qualification=qualification,
                experience_years=experience,
                consultation_fee=fee,
                is_active=True
            )
            
            # Add specializations
            for spec_name in specs:
                if spec_name in specializations:
                    doctor.specializations.append(specializations[spec_name])
            
            session.add(doctor)
        
        session.commit()
        logger.info(f"Seeded {len(doctors_data)} sample doctors and {len(specializations_data)} specializations")

def create_test_patient(scheduler):
    """Create a test patient for verification"""
    try:
        patient = scheduler.register_patient(
            name="Test Patient",
            phone="9999999999",
            age=30,
            location="Chennai",
            language="en"
        )
        logger.info(f"Test patient created/verified: {patient.name} (ID: {patient.patient_id})")
        return patient
    except Exception as e:
        logger.error(f"Failed to create test patient: {e}")
        return None

def run_basic_tests(scheduler, session):
    """Run basic functionality tests"""
    logger.info("Running basic system tests...")
    
    try:
        # Test 1: Doctor recommendation
        doctors = scheduler.get_doctors_by_specialization("Cardiology")
        if doctors:
            logger.info(f"✅ Found {len(doctors)} cardiologists")
        else:
            logger.warning("⚠️ No cardiologists found")
        
        # Test 2: Date parsing
        from utils.date_parser import date_parser
        test_date = date_parser.parse_natural_language_date("tomorrow")
        logger.info(f"✅ Date parsing works: 'tomorrow' = {test_date}")
        
        # Test 3: Patient search
        test_patients = scheduler.enhanced_patient_search("Test")
        logger.info(f"✅ Patient search works: found {len(test_patients)} matches for 'Test'")
        
        # Test 4: Analytics
        analytics = scheduler.get_booking_analytics(7)
        logger.info(f"✅ Analytics works: {analytics['total_bookings']} bookings in last 7 days")
        
        logger.info("✅ All basic tests passed")
        
    except Exception as e:
        logger.error(f"❌ Basic test failed: {e}")
        return False
    
    return True

def main():
    """Enhanced main function with comprehensive setup"""
    logger.info("Starting Apollo Assist Hospital Management System")
    
    try:
        # Parse command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            if command == "test":
                logger.info("Running in test mode")
        
        # Database setup
        db_config = {
            "db_name": settings.HOSP_DB_NAME or "hospital_db",
            "user": settings.HOSP_DB_USER or "postgres", 
            "password": settings.HOSP_DB_PASSWORD or "password",
            "host": settings.HOSP_DB_HOST or "localhost",
            "port": int(settings.HOSP_DB_PORT or 5432)
        }
        
        logger.info(f"Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['db_name']}")
        
        create_database_if_not_exists(**db_config)
        
        # Create engine with connection pooling
        engine = create_engine(
            settings.DATABASE_URL, 
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.drop_all(engine)
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created/verified")
        
        # Initialize session and scheduler
        session = SessionLocal()
        scheduler = AppointmentScheduler(session)
        
        try:
            # Initialize system settings
            initialize_system_settings(session)
            
            # Seed doctors from Excel if file exists
            doctors_xlsx = "doctors.xlsx"
            if os.path.exists(doctors_xlsx):
                logger.info(f"Seeding doctors from {doctors_xlsx}...")
                scheduler.seed_doctors_from_excel(doctors_xlsx)
            else:
                logger.info(f"Excel file {doctors_xlsx} not found, using sample data")
                seed_sample_data(session, scheduler)
            
            # Create test patient
            test_patient = create_test_patient(scheduler)
            
            # Run basic system tests
            if run_basic_tests(scheduler, session):
                logger.info("🎉 Apollo Assist system initialized successfully!")
                logger.info("System is ready to handle appointment bookings.")
                
                # Print system summary
                doctor_count = session.query(Doctor).filter_by(is_active=True).count()
                patient_count = session.query(Patient).filter_by(is_active=True).count()
                appointment_count = session.query(Appointment).count()
                
                logger.info(f"""
System Summary:
- Active Doctors: {doctor_count}
- Registered Patients: {patient_count}
- Total Appointments: {appointment_count}
- Database: {db_config['db_name']}
- Redis Cache: {'Enabled' if settings.REDIS_URL else 'Disabled'}
- SMS Notifications: {'Enabled' if settings.TWILIO_ACCOUNT_SID else 'Disabled'}
                """)
            else:
                logger.error("System tests failed. Please check the configuration.")
                sys.exit(1)
                
        finally:
            session.close()
            
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()