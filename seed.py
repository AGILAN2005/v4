# seed.py

import re
from utils.csv_manager import csv_manager # <-- Use the new CSV Manager
from utils.logger import logger

def split_and_join_specializations(raw: str) -> str:
    if not isinstance(raw, str):
        return ""
    s = re.sub(r'[/;&]| and | & |,|Lingual and contemporary orthodontics', ',', raw, flags=re.IGNORECASE)
    parts = [p.strip() for p in s.split(',') if p.strip()]
    return ','.join(parts)

def seed_doctors_from_data():
    logger.info("Starting to seed doctor data into local CSV files...")

    if not csv_manager:
        logger.error("CSV Manager is not initialized. Aborting seed.")
        return

    doctors_to_seed = [
        # ... (list of doctors from your image remains the same as before) ...
        {"name": "Dr. Ramesh Shanmugam", "qualification": "M.D.S, Clinical Director", "specialization": "Orthodontics & Dentofacial Orthopedics, Periodontal Surgeries, Lingual and contemporary orthodontics, Root canals, Cosmetic dentistry, Dental implants, Oral Implantologist (certified from Manipal)"},
        {"name": "Dr. Ranjana Ramesh", "qualification": "M.D.S, Cosmetic Dentist", "specialization": "Cosmetic dentistry, Biofunctional Prosthetic System (BPS) specialist, Full mouth rehabilitation, Laser dentistry, Implant dentistry"},
        {"name": "Dr. Shalini", "qualification": "Endodontist", "specialization": "Endodontist"},
        {"name": "Dr. Sabitha", "qualification": "General Dentist", "specialization": "General Dentist"},
        {"name": "Dr. Thivya Shankari", "qualification": "Endodontist", "specialization": "Endodontist"},
        {"name": "Dr. Shwetha", "qualification": "General Dentist", "specialization": "General Dentist"},
        {"name": "Dr. Ashwini", "qualification": "Pedodontist", "specialization": "Pedodontist"},
        {"name": "Dr. Angelin", "qualification": "Periodontist", "specialization": "Periodontist"},
        {"name": "Dr. Geetha", "qualification": "General Dentist", "specialization": "General Dentist"},
        {"name": "Dr. Glory", "qualification": "General Dentist", "specialization": "General Dentist"},
        {"name": "Dr. Sharath", "qualification": "Oral Medicine & Radiology", "specialization": "Oral Medicine & Radiology"},
        {"name": "Dr. Sathya", "qualification": "General Dentist", "specialization": "General Dentist"},
        {"name": "Dr. Nakshatra", "qualification": "General Dentist", "specialization": "General Dentist"},
        {"name": "Dr. Gayathri", "qualification": "Pedodontist", "specialization": "Pedodontist"},
        {"name": "Dr. Vishnu Priya", "qualification": "General Dentist", "specialization": "General Dentist"},
        {"name": "Dr. Asha V Shet", "qualification": "Oral & Maxillofacial Surgeon", "specialization": "Oral & Maxillofacial Surgeon"},
    ]

    added_count = 0
    for doc in doctors_to_seed:
        doctor_data = {
            "name": doc["name"],
            "qualification": doc["qualification"],
            "specializations": split_and_join_specializations(doc["specialization"])
        }
        
        # Use the csv_manager's create_doctor method
        if csv_manager.create_doctor(doctor_data):
            added_count += 1

    logger.info(f"Seeding process complete. Added {added_count} new doctors to doctors.csv.")

if __name__ == "__main__":
    seed_doctors_from_data()