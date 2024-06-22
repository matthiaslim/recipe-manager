# config.py
import os
from dotenv import load_dotenv

load_dotenv() # load environment variables from .env file

class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True

# Debugging: Print the values to ensure they are loaded
print(f"MYSQL_HOST={Config.MYSQL_HOST}")
print(f"MYSQL_USER={Config.MYSQL_USER}")
print(f"MYSQL_PASSWORD={Config.MYSQL_PASSWORD}")
print(f"MYSQL_DB={Config.MYSQL_DB}")