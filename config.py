#config.py

from pydantic_settings import BaseSettings
from pydantic import Extra
import os

class Settings(BaseSettings):
    HOSP_DB_NAME:str
    HOSP_DB_USER:str
    HOSP_DB_PASSWORD:str
    HOSP_DB_HOST:str
    HOSP_DB_PORT:str
    DATABASE_URL: str
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    GOOGLE_API_KEY: str | None = None

    JWT_SECRET_KEY: str
    JWT_ACCESS_EXPIRES_MIN: int = 15
    JWT_REFRESH_EXPIRES_DAYS: int = 7

    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    RELOAD: bool = False
    TZ: str = "Asia/Kolkata"

    REDIS_URL: str | None = None
    ENCRYPTION_KEY: str | None = None
    GOOGLE_SHEETS_CREDENTIALS_FILE: str = "credentials.json"
    GOOGLE_SHEETS_SPREADSHEET_NAME: str = "Apollo_Assist_DB"
    GOOGLE_SHEETS_SHARE_EMAIL: str | None = None # Optional: 
    # Rate limiting settings
    MAX_BOOKING_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        extra = Extra.allow

settings = Settings()