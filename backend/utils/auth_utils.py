# Backend/Utils/auth_utils.py
import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", 60))
FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable is required but not set")

try:
    fernet = Fernet(FERNET_KEY)
except Exception as e:
    raise ValueError(f"Invalid FERNET_KEY format: {e}")


def encrypt_key(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt_key(cipher_text: str) -> str:
    return fernet.decrypt(cipher_text.encode()).decode()


def hash_password(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()


def verify_password(plain_password: str, hashed_password_db: bytes) -> bool:
    return hash_password(plain_password) == hashed_password_db


def create_jwt_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def is_admin(source_id: int) -> bool:
    return source_id == 4


def parse_comma_separated(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def validate_date_range(from_date: str, to_date: str, date_format: str = "%Y-%m-%d"):
    try:
        from_dt = datetime.strptime(from_date, date_format)
        to_dt = datetime.strptime(to_date, date_format)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD."
        )

    if from_dt > to_dt:
        raise HTTPException(
            status_code=400, detail="From date cannot be after To date."
        )

def clean_guest_email(upn: str) -> str:
    if "#EXT#" in upn:
        return upn.split("#EXT#")[0].replace("_", "@")
    return upn