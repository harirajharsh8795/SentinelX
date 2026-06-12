from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from utils.config import settings
from sqlalchemy.orm import Session
from database.models import User

import hashlib
import os

def get_password_hash(password: str) -> str:
    # Pure python PBKDF2 with HMAC-SHA256, 100,000 iterations.
    # Extremely secure and free of passlib/bcrypt version compatibility bugs.
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2_sha256$100000${salt.hex()}${hashed.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith("pbkdf2_sha256$"):
            parts = hashed_password.split("$")
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            hashed = bytes.fromhex(parts[3])
            calc = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
            return calc == hashed
    except Exception:
        pass
    return False

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt
