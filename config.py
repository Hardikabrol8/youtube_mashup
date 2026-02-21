import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-12345")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "hardikabrol8@gmail.com")
    SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "")
    
    # Check if app password is set
    @classmethod
    def validate_config(cls):
        errors = []
        if not cls.SENDER_EMAIL:
            errors.append("SENDER_EMAIL is not set in environment.")
        if not cls.SENDER_APP_PASSWORD:
            errors.append("SENDER_APP_PASSWORD is not set in environment.")
        return errors
