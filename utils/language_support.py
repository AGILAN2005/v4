#utils/language_support.py

from typing import Dict, Optional

class LanguageManager:
    def __init__(self):
        self.translations = {
            'en': {
                'greeting': 'Namaste! You are speaking with Apollo Assist. How may I help you today?',
                'ask_details': 'To get started, could you please share your full name and registered mobile number?',
                'patient_registered': 'Welcome to Apollo Hospitals! I have registered your details.',
                'patient_found': 'Thank you, I found your details in our system.',
                'booking_success': 'Your appointment has been successfully booked with Dr. {} on {} at {}.',
                'no_slots': 'I am sorry, Dr. {} has no available slots on {}. Let me check alternative dates.',
                'no_doctor': 'I am sorry, no doctors are available for {} on {}.',
                'emergency': 'For medical emergencies, please hang up and dial 1066 immediately.',
                'appointment_confirmed': 'Just to confirm, I am booking an appointment for {} with Dr. {} on {} at {}. Is that correct?',
                'reschedule_success': 'Your appointment has been successfully rescheduled to {} at {}.',
                'cancel_success': 'Your appointment has been cancelled successfully.',
                'technical_error': 'I apologize, there seems to be a technical issue. Please try again or speak to our human operator.',
                'rate_limit': 'Too many requests. Please wait a moment before trying again.',
                'invalid_date': 'Please provide a valid date in DD-MM-YYYY format.',
                'alternative_slots': 'Here are some alternative time slots: {}',
                'alternative_doctors': 'Alternatively, Dr. {} is available at your preferred time.',
            },
            'hi': {
                'greeting': 'नमस्ते! आप अपोलो असिस्ट से बात कर रहे हैं। मैं आपकी कैसे सहायता कर सकता हूं?',
                'ask_details': 'शुरुआत करने के लिए, कृपया अपना पूरा नाम और पंजीकृत मोबाइल नंबर बताएं?',
                'patient_registered': 'अपोलो अस्पताल में आपका स्वागत है! मैंने आपका विवरण पंजीकृत कर दिया है।',
                'patient_found': 'धन्यवाद, मुझे हमारे सिस्टम में आपका विवरण मिल गया है।',
                'booking_success': 'आपकी नियुक्ति सफलतापूर्वक बुक हो गई है डॉ. {} के साथ {} को {} बजे।',
                'no_slots': 'खुशी है, डॉ. {} के पास {} को कोई उपलब्ध स्लॉट नहीं है। मैं वैकल्पिक तारीखें देखता हूं।',
                'no_doctor': 'खुशी है, {} के लिए {} को कोई डॉक्टर उपलब्ध नहीं है।',
                'emergency': 'चिकित्सा आपातकाल के लिए, कृपया फोन काटें और तुरंत 1066 डायल करें।',
                'appointment_confirmed': 'पुष्टि के लिए, मैं {} के लिए डॉ. {} के साथ {} को {} बजे नियुक्ति बुक कर रहा हूं। क्या यह सही है?',
            },
            'ta': {
                'greeting': 'வணக்கம்! நீங்கள் அப்போலோ அசிஸ்ட்டுடன் பேசுகிறீர்கள். நான் உங்களுக்கு எப்படி உதவ முடியும்?',
                'ask_details': 'தொடங்குவதற்கு, உங்கள் முழு பெயரையும் பதிவு செய்யப்பட்ட மொபைல் எண்ணையும் தெரிவிக்க முடியுமா?',
                'patient_registered': 'அப்போலோ மருத்துவமனையில் உங்களை வரவேற்கிறோம்! உங்கள் விவரங்களை பதிவு செய்துவிட்டேன்.',
                'patient_found': 'நன்றி, எங்கள் சிஸ்டத்தில் உங்கள் விவரங்களை கண்டுபிடித்தேன்.',
                'booking_success': 'உங்கள் சந்திப்பு வெற்றிகரமாக பதிவு செய்யப்பட்டுள்ளது டாக்டர் {} உடன் {} அன்று {} மணிக்கு.',
                'emergency': 'மருத்துவ அவசரநிலைக்கு, தயவுசெய்து உடனே 1066 ஐ டயல் செய்யவும்.',
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Simple language detection based on character sets"""
        if not text:
            return 'en'
        
        # Check for Hindi (Devanagari script)
        if any('\u0900' <= char <= '\u097F' for char in text):
            return 'hi'
        
        # Check for Tamil script
        if any('\u0B80' <= char <= '\u0BFF' for char in text):
            return 'ta'
        
        # Default to English
        return 'en'
    
    def get_message(self, key: str, lang: str = 'en', **kwargs) -> str:
        """Get localized message with formatting"""
        message_template = self.translations.get(lang, self.translations['en']).get(key, key)
        
        try:
            return message_template.format(**kwargs) if kwargs else message_template
        except KeyError:
            # Fallback to English if formatting fails
            return self.translations['en'].get(key, key)

# Global instance
language_manager = LanguageManager()