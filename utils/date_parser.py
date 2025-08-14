# from datetime import datetime, date, timedelta
# import holidays
# from typing import Union
# from utils.exceptions import InvalidDateError
# from utils.logger import logger

# class DateParser:
#     def __init__(self):
#         self.indian_holidays = holidays.India()
    
#     def parse_natural_language_date(self, date_input: str, context: str = "booking") -> date:
#         """Parse natural language dates with business rules validation"""
        
#         if not date_input:
#             raise InvalidDateError("Date input cannot be empty")
        
#         date_input = date_input.lower().strip()
#         today = date.today()
        
#         # Natural language parsing
#         if date_input in ["today", "आज", "இன்று"]:
#             target_date = today
#         elif date_input in ["tomorrow", "कल", "நாளை"]:
#             target_date = today + timedelta(days=1)
#         elif date_input in ["day after tomorrow", "परसों", "நாளை மறுநாள்"]:
#             target_date = today + timedelta(days=2)
#         elif "next week" in date_input or "अगले सप्ताह" in date_input:
#             target_date = today + timedelta(days=7)
#         else:
#             # Try parsing various date formats
#             formats = [
#                 "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y",
#                 "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"
#             ]
            
#             target_date = None
#             for fmt in formats:
#                 try:
#                     target_date = datetime.strptime(date_input, fmt).date()
#                     break
#                 except ValueError:
#                     continue
            
#             if not target_date:
#                 raise InvalidDateError(f"Could not parse date: '{date_input}'. Please use format DD-MM-YYYY or DD/MM/YYYY")
        
#         # Business rule validations
#         self._validate_business_rules(target_date, context)
        
#         return target_date
    
#     def _validate_business_rules(self, target_date: date, context: str):
#         """Validate business rules for appointment dates"""
#         today = date.today()
        
#         # Cannot book in the past (except for same day)
#         if target_date < today:
#             raise InvalidDateError("Cannot book appointments for past dates")
        
#         # Cannot book too far in advance
#         max_advance_days = 90
#         if target_date > today + timedelta(days=max_advance_days):
#             raise InvalidDateError(f"Cannot book appointments more than {max_advance_days} days in advance")
        
#         # Check for holidays
#         if target_date in self.indian_holidays:
#             holiday_name = self.indian_holidays[target_date]
#             raise InvalidDateError(f"Hospital is closed on {target_date.strftime('%B %d, %Y')} ({holiday_name}). Please choose another date.")
        
#         # Check if it's a Sunday (most hospitals are closed)
#         if target_date.weekday() == 6:  # Sunday
#             raise InvalidDateError("Hospital is closed on Sundays. Please choose another date.")
        
#         logger.info(f"Date validation passed", date=target_date.isoformat(), context=context)

# # Global instance
# date_parser = DateParser()


# utils/date_parser.py

import datetime
import re
from typing import Optional
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
import calendar

from utils.logger import logger
from utils.exceptions import InvalidDateError

class EnhancedDateParser:
    def __init__(self):
        self.today = datetime.date.today()
        self.now = datetime.datetime.now()
        
        # Common date patterns and their meanings
        self.natural_patterns = {
            r'\b(today|aaj)\b': self._parse_today,
            r'\b(tomorrow|kal)\b': self._parse_tomorrow,
            r'\bday after tomorrow\b': self._parse_day_after_tomorrow,
            r'\byesterday\b': self._parse_yesterday,
            r'\bthis (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b': self._parse_this_weekday,
            r'\bnext (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b': self._parse_next_weekday,
            r'\bthis week\b': self._parse_this_week,
            r'\bnext week\b': self._parse_next_week,
            r'\bthis month\b': self._parse_this_month,
            r'\bnext month\b': self._parse_next_month,
            r'\bin (\d+) days?\b': self._parse_in_n_days,
            r'\bafter (\d+) days?\b': self._parse_in_n_days,
        }
        
        # Weekday mappings
        self.weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
            'fri': 4, 'sat': 5, 'sun': 6
        }
        
        # Month mappings
        self.months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
    
    def get_current_datetime_info(self) -> dict:
        """Get comprehensive current date/time information"""
        now = datetime.datetime.now()
        today = now.date()
        
        return {
            'current_date': today,
            'current_datetime': now,
            'day_of_week': today.strftime('%A'),
            'day_of_week_short': today.strftime('%a'),
            'month': today.strftime('%B'),
            'month_short': today.strftime('%b'),
            'year': today.year,
            'is_weekend': today.weekday() >= 5,
            'week_number': today.isocalendar()[1],
            'formatted_date': today.strftime('%A, %B %d, %Y'),
            'iso_date': today.isoformat(),
            'current_time': now.strftime('%I:%M %p'),
            'hour_24': now.hour,
            'minute': now.minute
        }
    
    def parse_natural_language_date(self, date_string: str, context: str = "general") -> datetime.date:
        """
        Parse natural language date with enhanced current date awareness
        
        Args:
            date_string: The date string to parse
            context: Context for validation (booking, rescheduling, etc.)
        
        Returns:
            datetime.date object
        """
        if not date_string:
            raise InvalidDateError("Date string cannot be empty")
        
        date_string = date_string.lower().strip()
        
        # Update current date reference
        self.today = datetime.date.today()
        self.now = datetime.datetime.now()
        
        logger.debug(f"Parsing date string: '{date_string}' with context: {context}")
        logger.debug(f"Current date reference: {self.today} ({self.today.strftime('%A')})")
        
        try:
            # First, try natural language patterns
            for pattern, parser_func in self.natural_patterns.items():
                match = re.search(pattern, date_string, re.IGNORECASE)
                if match:
                    result_date = parser_func(match)
                    if result_date:
                        self._validate_date_for_context(result_date, context)
                        logger.info(f"Parsed '{date_string}' as {result_date} using pattern: {pattern}")
                        return result_date
            
            # Try specific date formats
            result_date = self._parse_specific_date_formats(date_string)
            if result_date:
                self._validate_date_for_context(result_date, context)
                logger.info(f"Parsed '{date_string}' as {result_date} using specific format")
                return result_date
            
            # Try dateutil parser as fallback
            try:
                parsed_dt = dateutil_parser.parse(date_string, default=self.now)
                result_date = parsed_dt.date()
                self._validate_date_for_context(result_date, context)
                logger.info(f"Parsed '{date_string}' as {result_date} using dateutil parser")
                return result_date
            except (ValueError, TypeError):
                pass
            
            # If all parsing fails
            raise InvalidDateError(f"Unable to understand the date '{date_string}'. Please try formats like 'tomorrow', 'next Monday', '15th December', or 'December 15, 2024'.")
            
        except InvalidDateError:
            raise
        except Exception as e:
            logger.error(f"Error parsing date '{date_string}': {e}")
            raise InvalidDateError(f"Invalid date format: '{date_string}'. Please try 'tomorrow', 'next Monday', or '15th December'.")
    
    # def _parse_specific_date_formats(self, date_string: str) -> Optional[datetime.date]:
    #     """Parse specific date formats"""
        
    #     # Format: 15th December, December 15th, Dec 15th, etc.
    #     ordinal_patterns = [
    #         r'(\d{1,2})(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:\s+(\d{4}))?',
    #         r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(st|nd|rd|th)?(?:\s+(\d{4}))?'
    #     ]
        
    #     for pattern in ordinal_patterns:
    #         match = re.search(pattern, date_string, re.IGNORECASE)
    #         if match:
    #             try:
    #                 groups = match.groups()
    #                 if len(groups) >= 2:
    #                     if groups[0].isdigit():  # Day first format
    #                         day = int(groups[0])
    #                         month_str = groups[2].lower()
    #                         year = int(groups[3]) if len(groups) > 3 and groups[3] else self.today.year
    #                     else:  # Month first format
    #                         month_str = groups[0].lower()
    #                         day = int(groups[1])
    #                         year = int(groups[3]) if len(groups) > 3 and groups[3] else self.today.year
                        
    #                     month = self.months.get(month_str)
    #                     if month:
    #                         result_date = datetime.date(year, month, day)
    #                         # If date is in the past and no year specified, assume next year
    #                         if result_date < self.today and len(groups) <= 3:
    #                             result_date = datetime.date(year + 1, month, day)
    #                         return result_date
    #             except (ValueError, KeyError):
    #                 continue
        
    #     # Format: DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, etc.
    #     date_separator_patterns = [
    #         r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
    #         r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})',  # DD/MM/YY or MM/DD/YY
    #         r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
    #     ]
        
    #     for pattern in date_separator_patterns:
    #         match = re.search(pattern, date_string)
    #         if match:
    #             try:
    #                 parts = [int(part) for part in match.groups()]
                    
    #                 if len(str(parts[2])) == 2:  # Two-digit year
    #                     parts[2] += 2000 if parts[2] < 50 else 1900
                    
    #                 if len(str(parts[0])) == 4:  # YYYY/MM/DD format
    #                     year, month, day = parts
    #                 else:
    #                     # Assume DD/MM/YYYY for Indian context
    #                     day, month, year = parts
    #                     # But also try MM/DD/YYYY if DD/MM doesn't make sense
    #                     try:
    #                         datetime.date(year, month, day)
    #                     except ValueError:
    #                         try:
    #                             month, day, year = parts
    #                             datetime.date(year, month, day)
    #                         except ValueError:
    #                             continue
                    
    #                 return datetime.date(year, month, day)
                    
    #             except (ValueError, IndexError):
    #                 continue
        
    #     return None
    def _parse_specific_date_formats(self, date_string: str) -> Optional[datetime.date]:
        """Parse specific date formats with improved, safer logic."""
        
        # --- Ordinal Patterns (e.g., 15th December) ---
        ordinal_patterns = [
            r'(\d{1,2})(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:\s+(\d{4}))?',
            r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(st|nd|rd|th)?(?:\s+(\d{4}))?'
        ]
        
        for pattern in ordinal_patterns:
            match = re.search(pattern, date_string, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if groups[0].isdigit():  # Day first format (e.g., "15th December")
                        day = int(groups[0])
                        month_str = groups[2].lower()
                        year = int(groups[3]) if len(groups) > 3 and groups[3] else self.today.year
                    else:  # Month first format (e.g., "December 15th")
                        month_str = groups[0].lower()
                        day = int(groups[1])
                        year = int(groups[3]) if len(groups) > 3 and groups[3] else self.today.year
                    
                    month = self.months.get(month_str)
                    if month:
                        result_date = datetime.date(year, month, day)
                        # If the parsed date is in the past and no year was specified, assume it's for the next year
                        if result_date < self.today and len(groups) <= 3:
                            result_date = datetime.date(year + 1, month, day)
                        return result_date
                except (ValueError, KeyError):
                    continue

        # --- Date Separator Patterns (e.g., 2025-08-15) ---
        # This new logic handles each format separately to avoid bugs.

        # Pattern for YYYY-MM-DD
        match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', date_string)
        if match:
            try:
                year, month, day = map(int, match.groups())
                return datetime.date(year, month, day)
            except (ValueError, IndexError):
                pass  # Let it fall through to the next pattern

        # Pattern for DD-MM-YYYY
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_string)
        if match:
            try:
                p1, p2, year = map(int, match.groups())
                # Assume DD/MM/YYYY first for Indian context
                return datetime.date(year, p2, p1)
            except (ValueError, IndexError):
                pass
        
        # Pattern for DD-MM-YY
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})', date_string)
        if match:
            try:
                p1, p2, year_short = map(int, match.groups())
                # Correctly handle 2-digit years
                year = 2000 + year_short if year_short < 50 else 1900 + year_short
                # Assume DD/MM/YY first
                return datetime.date(year, p2, p1)
            except (ValueError, IndexError):
                pass
                
        return None



    def _validate_date_for_context(self, date_obj: datetime.date, context: str):
        """Validate date based on context"""
        if context == "booking":
            # For booking, date cannot be in the past (except today)
            if date_obj < self.today:
                raise InvalidDateError(f"Cannot book appointments for past dates. {date_obj.strftime('%B %d, %Y')} has already passed.")
            
            # Cannot book too far in advance (e.g., more than 90 days)
            max_advance = self.today + datetime.timedelta(days=90)
            if date_obj > max_advance:
                raise InvalidDateError(f"Cannot book appointments more than 90 days in advance. Please choose a date before {max_advance.strftime('%B %d, %Y')}.")
        
        elif context == "rescheduling":
            # Similar rules as booking
            if date_obj < self.today:
                raise InvalidDateError(f"Cannot reschedule to past dates. Please choose today or a future date.")
    
    # Natural language parsing methods
    def _parse_today(self, match) -> datetime.date:
        return self.today
    
    def _parse_tomorrow(self, match) -> datetime.date:
        return self.today + datetime.timedelta(days=1)
    
    def _parse_day_after_tomorrow(self, match) -> datetime.date:
        return self.today + datetime.timedelta(days=2)
    
    def _parse_yesterday(self, match) -> datetime.date:
        return self.today - datetime.timedelta(days=1)
    
    def _parse_this_weekday(self, match) -> datetime.date:
        weekday_str = match.group(1).lower()
        target_weekday = self.weekdays.get(weekday_str)
        if target_weekday is None:
            return None
        
        days_ahead = target_weekday - self.today.weekday()
        if days_ahead <= 0:  # If it's today or past, get next week's day
            days_ahead += 7
        
        return self.today + datetime.timedelta(days=days_ahead)
    
    def _parse_next_weekday(self, match) -> datetime.date:
        weekday_str = match.group(1).lower()
        target_weekday = self.weekdays.get(weekday_str)
        if target_weekday is None:
            return None
        
        # Always next week
        days_ahead = target_weekday - self.today.weekday() + 7
        return self.today + datetime.timedelta(days=days_ahead)
    
    def _parse_this_week(self, match) -> datetime.date:
        # Return the next working day this week (Monday-Saturday)
        for i in range(7):
            check_date = self.today + datetime.timedelta(days=i)
            if check_date.weekday() < 6:  # Monday=0, Saturday=5
                return check_date
        return self.today + datetime.timedelta(days=1)  # Fallback
    
    def _parse_next_week(self, match) -> datetime.date:
        # Return Monday of next week
        days_until_monday = 7 - self.today.weekday()
        return self.today + datetime.timedelta(days=days_until_monday)
    
    def _parse_this_month(self, match) -> datetime.date:
        # Return first available day of current month (today if still in this month)
        return max(self.today, datetime.date(self.today.year, self.today.month, 1))
    
    def _parse_next_month(self, match) -> datetime.date:
        # Return first day of next month
        if self.today.month == 12:
            return datetime.date(self.today.year + 1, 1, 1)
        else:
            return datetime.date(self.today.year, self.today.month + 1, 1)
    
    def _parse_in_n_days(self, match) -> datetime.date:
        try:
            days = int(match.group(1))
            return self.today + datetime.timedelta(days=days)
        except (ValueError, IndexError):
            return None
    
    def get_relative_date_suggestions(self, base_date: datetime.date = None) -> list:
        """Get relative date suggestions for user"""
        if base_date is None:
            base_date = self.today
        
        suggestions = []
        
        # Add basic suggestions
        suggestions.extend([
            ("Today", base_date),
            ("Tomorrow", base_date + datetime.timedelta(days=1)),
            ("Day after tomorrow", base_date + datetime.timedelta(days=2))
        ])
        
        # Add next few weekdays
        for i in range(1, 8):
            check_date = base_date + datetime.timedelta(days=i)
            day_name = check_date.strftime("%A")
            
            if check_date.weekday() < 6:  # Monday to Saturday
                suggestions.append((f"Next {day_name}", check_date))
        
        return suggestions[:7]  # Return first 7 suggestions
    
    def format_date_for_display(self, date_obj: datetime.date, include_day: bool = True) -> str:
        """Format date for user-friendly display"""
        if date_obj == self.today:
            return f"Today ({date_obj.strftime('%B %d, %Y')})"
        elif date_obj == self.today + datetime.timedelta(days=1):
            return f"Tomorrow ({date_obj.strftime('%B %d, %Y')})"
        elif date_obj == self.today + datetime.timedelta(days=2):
            return f"Day after tomorrow ({date_obj.strftime('%B %d, %Y')})"
        else:
            if include_day:
                return date_obj.strftime('%A, %B %d, %Y')
            else:
                return date_obj.strftime('%B %d, %Y')

# Create global instance
date_parser = EnhancedDateParser()

