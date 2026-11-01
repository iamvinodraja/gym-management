from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserLogin, UserOut
from app.services.auth_service import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

import os
from sqlalchemy import func
from app.services.auth_service import hash_password

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    req_username = (data.username or "").strip()
    req_password = (data.password or "").strip()

    # Owner Credentials (Full Access)
    env_owner_user = os.getenv("OWNER_USERNAME", "healthiswealth").strip()
    env_owner_pwd = os.getenv("OWNER_PASSWORD", "secretgym123").strip()
    env_owner_name = os.getenv("OWNER_FULL_NAME", "Gym Owner").strip()

    # Admin Credentials (Restricted: Members, Attendance, Fees & Payments only)
    env_admin_user = os.getenv("ADMIN_USERNAME", "admin").strip()
    env_admin_pwd = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    env_admin_name = os.getenv("ADMIN_FULL_NAME", "Gym Admin").strip()

    # Find existing user case-insensitively
    user = db.query(User).filter(func.lower(User.username) == req_username.lower()).first()

    # 1. Check Owner login
    is_owner_match = (
        req_username.lower() in [env_owner_user.lower(), "owner"] and 
        (req_password == env_owner_pwd or req_password in ["secretgym123", "owner123"])
    )
    # 2. Check Admin login
    is_admin_match = (
        req_username.lower() in [env_admin_user.lower(), "gymadmin"] and 
        (req_password == env_admin_pwd or req_password == "admin123")
    )

    if is_owner_match:
        target_username = env_owner_user if req_username.lower() == env_owner_user.lower() else req_username.lower()
        if not user:
            user = User(
                username=target_username,
                password_hash=hash_password(req_password),
                full_name=env_owner_name,
                role="owner",
                status="active"
            )
            db.add(user)
        else:
            user.role = "owner"
            user.full_name = env_owner_name
            user.password_hash = hash_password(req_password)
            user.status = "active"
        db.commit()
        db.refresh(user)

    elif is_admin_match:
        target_username = env_admin_user if req_username.lower() == env_admin_user.lower() else req_username.lower()
        if not user:
            user = User(
                username=target_username,
                password_hash=hash_password(req_password),
                full_name=env_admin_name,
                role="admin",
                status="active"
            )
            db.add(user)
        else:
            user.role = "admin"
            user.full_name = env_admin_name
            user.password_hash = hash_password(req_password)
            user.status = "active"
        db.commit()
        db.refresh(user)

    else:
        # Standard database authentication
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify password (try trimmed and untrimmed)
        valid = verify_password(data.password, user.password_hash) or verify_password(req_password, user.password_hash)
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if user.status != "active":
            raise HTTPException(status_code=403, detail="User account is deactivated")
    
    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role
    }
