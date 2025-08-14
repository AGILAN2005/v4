#utils/exceptions.py

class ApolloAssistError(Exception):
    """Base exception for Apollo Assist"""
    pass

class PatientNotFoundError(ApolloAssistError):
    """Patient not found in database"""
    pass

class DoctorNotFoundError(ApolloAssistError):
    """Doctor not found or not available"""
    pass

class SlotUnavailableError(ApolloAssistError):
    """Requested appointment slot is not available"""
    pass

class InvalidDateError(ApolloAssistError):
    """Invalid date provided for appointment"""
    pass

class RateLimitExceededError(ApolloAssistError):
    """Rate limit exceeded for user requests"""
    pass

class BookingConflictError(ApolloAssistError):
    """Appointment booking conflict detected"""
    pass