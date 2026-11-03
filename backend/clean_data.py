import sys
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import engine, SessionLocal, Base, get_active_db_type
from app.models.models import (
    User,
    Trainer,
    Staff,
    MembershipPlan,
    Member,
    Membership,
    Payment,
    Attendance,
    Expense,
    ActivityLog,
    GymSetting,
)
from app.services.auth_service import hash_password

def clean_database():
    print("=" * 60)
    print(f"Connecting to database [Type: {get_active_db_type()}]...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("\n1. Deleting demo data in dependency order...")
        
        # Child tables first
        num_att = db.query(Attendance).delete()
        print(f"   - Deleted {num_att} Attendance records")

        num_pay = db.query(Payment).delete()
        print(f"   - Deleted {num_pay} Payment / Receipt records")

        num_mships = db.query(Membership).delete()
        print(f"   - Deleted {num_mships} Membership subscription history records")

        num_members = db.query(Member).delete()
        print(f"   - Deleted {num_members} Members")

        num_exp = db.query(Expense).delete()
        print(f"   - Deleted {num_exp} Expenses")

        num_logs = db.query(ActivityLog).delete()
        print(f"   - Deleted {num_logs} Activity logs")

        num_staff = db.query(Staff).delete()
        print(f"   - Deleted {num_staff} Staff entries")

        num_trainers = db.query(Trainer).delete()
        print(f"   - Deleted {num_trainers} Trainer entries")

        num_plans = db.query(MembershipPlan).delete()
        print(f"   - Deleted {num_plans} Membership plans")

        db.commit()
        print("-> Demo data wipe completed successfully!")

        print("\n2. Ensuring Owner and Admin accounts exist...")
        owner_user = os.getenv("OWNER_USERNAME", "healthiswealth").strip()
        owner_pwd = os.getenv("OWNER_PASSWORD", "secretgym123").strip()
        owner_name = os.getenv("OWNER_FULL_NAME", "Gym Owner").strip()

        admin_user = os.getenv("ADMIN_USERNAME", "admin").strip()
        admin_pwd = os.getenv("ADMIN_PASSWORD", "admin123").strip()
        admin_name = os.getenv("ADMIN_FULL_NAME", "Gym Admin").strip()

        # Delete any extra demo users
        db.query(User).filter(~User.username.in_([owner_user, admin_user])).delete(synchronize_session=False)

        # Upsert Owner
        existing_owner = db.query(User).filter(User.username == owner_user).first()
        if not existing_owner:
            db.add(User(
                username=owner_user,
                password_hash=hash_password(owner_pwd),
                full_name=owner_name,
                role="owner",
                status="active"
            ))
            print(f"   + Created Owner account: '{owner_user}'")
        else:
            existing_owner.role = "owner"
            existing_owner.password_hash = hash_password(owner_pwd)
            existing_owner.full_name = owner_name
            existing_owner.status = "active"
            print(f"   * Updated Owner account: '{owner_user}'")

        # Upsert Admin
        existing_admin = db.query(User).filter(User.username == admin_user).first()
        if not existing_admin:
            db.add(User(
                username=admin_user,
                password_hash=hash_password(admin_pwd),
                full_name=admin_name,
                role="admin",
                status="active"
            ))
            print(f"   + Created Admin account: '{admin_user}'")
        else:
            existing_admin.role = "admin"
            existing_admin.password_hash = hash_password(admin_pwd)
            existing_admin.full_name = admin_name
            existing_admin.status = "active"
            print(f"   * Updated Admin account: '{admin_user}'")

        # 3. Ensure Gym Settings
        default_settings = [
            ("gym_name", os.getenv("GYM_NAME", "Power Fitness Gym")),
            ("gym_address", os.getenv("GYM_ADDRESS", "Plot 14-C, Main Boulevard, Gulberg III, Lahore, Pakistan")),
            ("gym_phone", os.getenv("GYM_PHONE", "0300-1234567")),
            ("currency_symbol", "Rs."),
            ("currency_code", "PKR"),
            ("default_fee", "2500"),
            ("warning_days", "7"),
            ("receipt_footer", "Thank you for training with us! Fees once paid are non-refundable. Please carry your workout towel and clean shoes.")
        ]
        for k, v in default_settings:
            existing = db.query(GymSetting).filter(GymSetting.key_name == k).first()
            if not existing:
                db.add(GymSetting(key_name=k, key_value=v))

        db.commit()
        print("\n-> Database is now completely clean and ready for real data!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Database clean failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    clean_database()
