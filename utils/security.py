#utils/security.py

import hashlib
import os
from cryptography.fernet import Fernet
from typing import Optional
from config import settings
from utils.logger import logger

class SecurityManager:
    def __init__(self):
        # Initialize encryption
        encryption_key = settings.ENCRYPTION_KEY
        if not encryption_key:
            # Generate a key for development (use proper key management in production)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("Using generated encryption key. Set ENCRYPTION_KEY in production!")
        
        try:
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            self.cipher = Fernet(encryption_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.cipher = None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self.cipher or not data:
            return data
        
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self.cipher or not encrypted_data:
            return encrypted_data
        
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data
    
    def hash_phone(self, phone: str) -> str:
        """Hash phone number for secure indexing"""
        if not phone:
            return ""
        return hashlib.sha256(phone.encode()).hexdigest()
    
    def validate_phone_format(self, phone: str) -> bool:
        """Validate Indian phone number format"""
        if not phone:
            return False
        
        # Remove any non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # Indian mobile numbers: 10 digits starting with 6,7,8,9
        # Or with country code: +91 followed by 10 digits
        if len(digits_only) == 10 and digits_only[0] in '6789':
            return True
        elif len(digits_only) == 12 and digits_only.startswith('91') and digits_only[2] in '6789':
            return True
        
        return False
    
    def sanitize_input(self, input_str: str) -> str:
        """Basic input sanitization"""
        if not input_str:
            return ""
        
        # Remove potentially harmful characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}']
        sanitized = input_str
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()

# Global instance
security_manager = SecurityManager()