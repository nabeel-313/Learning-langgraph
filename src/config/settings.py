import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nabeel:momin.123@localhost:5432/travel_db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    SECRET_KEY = os.getenv("SECRET_KEY", "qMUcjKV5NCbJGZz3QSS_renNtHua7FDuXOZDiZLcL-g")


settings = Settings()

# REMOVE THIS - Database should NOT be in settings
# from src.database.database import Database
# database = Database()
