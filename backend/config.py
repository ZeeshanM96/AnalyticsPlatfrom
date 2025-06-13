# Backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Ideally load environment variables from a .env file
JWT_SECRET = ""  # Replace with a secure key
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60
