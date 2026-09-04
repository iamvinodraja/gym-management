import os
import hmac
import hashlib
import base64
import json
import time
from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User

SECRET_KEY = os.getenv("SECRET_KEY", "pakistani_gym_management_super_secret_key_2026")
SALT = "pakistani_gym_salt_val"

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt_bytes = SALT.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000)
    return f"pbkdf2:sha256:100000${SALT}${key.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password or not hashed_password.startswith("pbkdf2:sha256:"):
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        expected_hex = parts[2]
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False

def create_access_token(user: User) -> str:
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "exp": int(time.time()) + (86400 * 30),  # 30 days valid
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    signature = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"

def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Add padding back if necessary
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        payload = json.loads(payload_json)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required")
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    user = db.query(User).filter(User.id == payload["user_id"], User.status == "active").first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin permissions required")
    return current_user
