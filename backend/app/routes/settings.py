from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import GymSetting
from app.schemas.schemas import GymSettingsUpdate, GymSettingsOut
from app.services.gym_service import get_gym_setting, set_gym_setting, log_activity

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    return {
        "gym_name": get_gym_setting(db, "gym_name", "Power Fitness Gym"),
        "gym_address": get_gym_setting(db, "gym_address", "Plot 14-C, Main Boulevard, Gulberg III, Lahore, Pakistan"),
        "gym_phone": get_gym_setting(db, "gym_phone", "0300-1234567"),
        "currency_symbol": get_gym_setting(db, "currency_symbol", "Rs."),
        "currency_code": get_gym_setting(db, "currency_code", "PKR"),
        "default_fee": float(get_gym_setting(db, "default_fee", "2500")),
        "warning_days": int(get_gym_setting(db, "warning_days", "7")),
        "receipt_footer": get_gym_setting(db, "receipt_footer", "Thank you for training with Power Fitness Gym! Fees once paid are non-refundable.")
    }

@router.put("")
def update_settings(data: GymSettingsUpdate, db: Session = Depends(get_db)):
    if data.gym_name is not None:
        set_gym_setting(db, "gym_name", data.gym_name.strip())
    if data.gym_address is not None:
        set_gym_setting(db, "gym_address", data.gym_address.strip())
    if data.gym_phone is not None:
        set_gym_setting(db, "gym_phone", data.gym_phone.strip())
    if data.currency_symbol is not None:
        set_gym_setting(db, "currency_symbol", data.currency_symbol.strip())
    if data.default_fee is not None:
        set_gym_setting(db, "default_fee", str(data.default_fee))
    if data.warning_days is not None:
        set_gym_setting(db, "warning_days", str(data.warning_days))
    if data.receipt_footer is not None:
        set_gym_setting(db, "receipt_footer", data.receipt_footer.strip())

    log_activity(db, "Settings Updated", "Gym profile and receipt settings updated")
    return {"success": True, "message": "Settings updated successfully"}
