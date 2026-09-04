import datetime
import re
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Member, Payment, ActivityLog, GymSetting

def format_date_pk(d: Optional[datetime.date]) -> str:
    if not d:
        return ""
    return d.strftime("%d-%m-%Y")

def parse_date_pk(date_str: Optional[str]) -> Optional[datetime.date]:
    if not date_str:
        return None
    date_str = date_str.strip()
    # Try DD-MM-YYYY
    try:
        return datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        pass
    # Try YYYY-MM-DD
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    return None

def format_currency_pk(amount: float, symbol: str = "Rs.") -> str:
    try:
        val = float(amount or 0)
        formatted_num = f"{val:,.0f}" if val.is_integer() else f"{val:,.2f}"
        return f"{symbol} {formatted_num}"
    except Exception:
        return f"{symbol} {amount}"

def generate_member_id(db: Session) -> str:
    """Generates sequential ID like PK-1001, PK-1002"""
    latest = db.query(Member).order_by(Member.id.desc()).first()
    if not latest:
        return "PK-1001"
    
    # Try to extract trailing number
    match = re.search(r"(\d+)$", latest.member_id)
    if match:
        next_num = int(match.group(1)) + 1
        return f"PK-{next_num}"
    else:
        return f"PK-{1000 + latest.id + 1}"

def generate_payment_id(db: Session) -> str:
    """Generates sequential ID like REC-2026-0001"""
    year = datetime.date.today().year
    count = db.query(func.count(Payment.id)).scalar() or 0
    return f"REC-{year}-{count + 1:04d}"

def calculate_member_status(expiry_date: Optional[datetime.date], warning_days: int = 7) -> Tuple[str, int]:
    """
    Returns (status, remaining_days)
    Status: 'Active', 'Expiring Soon', 'Expired', 'No Plan'
    """
    if not expiry_date:
        return ("No Plan", 0)
    
    today = datetime.date.today()
    delta = (expiry_date - today).days

    if delta < 0:
        return ("Expired", delta)
    elif delta <= warning_days:
        return ("Expiring Soon", delta)
    else:
        return ("Active", delta)

def log_activity(db: Session, action: str, description: str, performed_by: str = "System"):
    try:
        log = ActivityLog(
            action=action,
            description=description,
            performed_by=performed_by,
            timestamp=datetime.datetime.now()
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()

def get_gym_setting(db: Session, key: str, default: str = "") -> str:
    setting = db.query(GymSetting).filter(GymSetting.key_name == key).first()
    return setting.key_value if setting else default

def set_gym_setting(db: Session, key: str, value: str):
    setting = db.query(GymSetting).filter(GymSetting.key_name == key).first()
    if setting:
        setting.key_value = str(value)
    else:
        setting = GymSetting(key_name=key, key_value=str(value))
        db.add(setting)
    db.commit()
