# config.py
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env file

class Config:
    # MYSQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True

    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Debugging: Print the values to ensure they are loaded
print(f"MYSQL_HOST={Config.MYSQL_HOST}")
print(f"MYSQL_USER={Config.MYSQL_USER}")
print(f"MYSQL_PASSWORD={Config.MYSQL_PASSWORD}")
print(f"MYSQL_DB={Config.MYSQL_DB}")

def start_redis():
    try:
        subprocess.Popen(['redis-server'])
        print("Redis server started")
    except Exception as e:
        print(f"Failed to start Redis server: {e}")

# Call the function to start Redis when the module is imported
start_redis()