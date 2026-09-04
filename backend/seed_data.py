import sys
import os
import datetime
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import engine, SessionLocal, Base
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

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Seeding Gym Settings...")
        default_settings = [
            ("gym_name", "Power Fitness Gym"),
            ("gym_address", "Plot 14-C, Main Boulevard, Gulberg III, Lahore, Pakistan"),
            ("gym_phone", "0300-1234567"),
            ("currency_symbol", "Rs."),
            ("currency_code", "PKR"),
            ("default_fee", "2500"),
            ("warning_days", "7"),
            ("receipt_footer", "Thank you for training with Power Fitness Gym! Fees once paid are non-refundable. Please carry your workout towel and clean shoes.")
        ]
        for k, v in default_settings:
            existing = db.query(GymSetting).filter(GymSetting.key_name == k).first()
            if not existing:
                db.add(GymSetting(key_name=k, key_value=v))

        admin_user = os.getenv("ADMIN_USERNAME", "healthiswealth").strip()
        admin_pwd = os.getenv("ADMIN_PASSWORD", "secretgym123").strip()
        admin_name = os.getenv("ADMIN_FULL_NAME", "Gym Owner").strip()
        print(f"Seeding User ({admin_user})...")

        # Remove previous default test users if they differ
        if admin_user != "admin":
            db.query(User).filter(User.username == "admin").delete()
        db.query(User).filter(User.username == "reception").delete()

        existing_admin = db.query(User).filter(User.username == admin_user).first()
        if not existing_admin:
            db.add(User(
                username=admin_user,
                password_hash=hash_password(admin_pwd),
                full_name=admin_name,
                role="admin",
                status="active"
            ))
        else:
            existing_admin.password_hash = hash_password(admin_pwd)
            existing_admin.full_name = admin_name
            existing_admin.status = "active"

        print("Seeding Membership Plans...")
        plans_data = [
            ("Monthly Regular", 30, 2500.0, "Full cardio & strength gym access for 30 days"),
            ("3 Months Saver", 90, 6500.0, "Quarterly package with Rs. 1,000 discount"),
            ("6 Months Pro", 180, 11000.0, "Half-yearly access with free locker"),
            ("Yearly Elite", 365, 18000.0, "Best value! 12 months full facility access"),
            ("Admission / Registration", 0, 1000.0, "One-time registration fee for new joiners")
        ]
        for name, dur, pr, desc in plans_data:
            if not db.query(MembershipPlan).filter(MembershipPlan.name == name).first():
                db.add(MembershipPlan(name=name, duration_days=dur, price=pr, description=desc, is_active=True))
        db.commit()

        print("Seeding Trainers...")
        trainers_data = [
            ("Ahmed Khan", "0321-4567890", "Bodybuilding & Heavy Lifting", 45000.0),
            ("Zubair Butt", "0333-7654321", "Weight Loss & HIIT Cardio", 40000.0),
            ("Shahid Afridi", "0312-9876543", "Crossfit & Strength Conditioning", 42000.0)
        ]
        for name, ph, spec, sal in trainers_data:
            if not db.query(Trainer).filter(Trainer.name == name).first():
                db.add(Trainer(name=name, phone=ph, specialization=spec, salary=sal, status="active"))
        db.commit()

        print("Seeding Staff...")
        staff_data = [
            ("STF-01", "Malik Tariq", "0300-1112233", "35201-1234567-1", "Owner", 0.0, datetime.date(2023, 1, 1)),
            ("STF-02", "Hamza Qureshi", "0302-2223344", "35201-2345678-3", "Manager", 55000.0, datetime.date(2023, 3, 15)),
            ("STF-03", "Asad Ali", "0304-3334455", "35202-3456789-5", "Receptionist", 30000.0, datetime.date(2024, 1, 10)),
            ("STF-04", "Ahmed Khan", "0321-4567890", "35202-4567890-7", "Trainer", 45000.0, datetime.date(2023, 6, 1))
        ]
        for sid, sname, sph, scnic, srole, ssal, sjdate in staff_data:
            if not db.query(Staff).filter(Staff.staff_id == sid).first():
                db.add(Staff(staff_id=sid, name=sname, phone=sph, cnic=scnic, role=srole, salary=ssal, joining_date=sjdate, status="Active"))
        db.commit()

        # Check if members already exist
        if db.query(Member).count() == 0:
            print("Seeding Sample Pakistani Members...")
            today = datetime.date.today()

            plan_monthly = db.query(MembershipPlan).filter(MembershipPlan.name == "Monthly Regular").first()
            plan_3m = db.query(MembershipPlan).filter(MembershipPlan.name == "3 Months Saver").first()
            plan_yearly = db.query(MembershipPlan).filter(MembershipPlan.name == "Yearly Elite").first()

            t1 = db.query(Trainer).filter(Trainer.name == "Ahmed Khan").first()
            t2 = db.query(Trainer).filter(Trainer.name == "Zubair Butt").first()

            members_data = [
                {
                    "member_id": "PK-1001",
                    "full_name": "Ali Raza Khan",
                    "father_name": "Tariq Khan",
                    "cnic": "35201-1122334-1",
                    "phone": "0300-8451234",
                    "emergency_contact": "0300-1122334",
                    "gender": "Male",
                    "dob": datetime.date(1998, 5, 14),
                    "address": "House 12, Street 4, Cavalry Ground, Lahore",
                    "join_date": today - datetime.timedelta(days=60),
                    "plan": plan_monthly,
                    "start_date": today - datetime.timedelta(days=10),
                    "expiry_date": today + datetime.timedelta(days=20),
                    "monthly_fee": 2500.0,
                    "discount": 0.0,
                    "outstanding_amount": 0.0,
                    "status": "Active",
                    "trainer": t1,
                    "amount_paid": 2500.0,
                    "method": "Cash"
                },
                {
                    "member_id": "PK-1002",
                    "full_name": "Usman Tariq",
                    "father_name": "Muhammad Tariq",
                    "cnic": "35202-2233445-3",
                    "phone": "0321-9876543",
                    "emergency_contact": "0321-7766554",
                    "gender": "Male",
                    "dob": datetime.date(1995, 8, 20),
                    "address": "Flat 3-B, Model Town, Lahore",
                    "join_date": today - datetime.timedelta(days=90),
                    "plan": plan_monthly,
                    "start_date": today - datetime.timedelta(days=28),
                    "expiry_date": today + datetime.timedelta(days=2),  # Expiring Soon!
                    "monthly_fee": 2500.0,
                    "discount": 0.0,
                    "outstanding_amount": 1000.0,  # Has dues!
                    "status": "Expiring Soon",
                    "trainer": t2,
                    "amount_paid": 1500.0,
                    "method": "Easypaisa"
                },
                {
                    "member_id": "PK-1003",
                    "full_name": "Hamza Shah",
                    "father_name": "Syed Shah",
                    "cnic": "35201-9988776-5",
                    "phone": "0333-5566778",
                    "emergency_contact": "0333-9988776",
                    "gender": "Male",
                    "dob": datetime.date(2001, 11, 2),
                    "address": "Sector Y, Phase 3, DHA Lahore",
                    "join_date": today - datetime.timedelta(days=40),
                    "plan": plan_monthly,
                    "start_date": today - datetime.timedelta(days=35),
                    "expiry_date": today - datetime.timedelta(days=5),  # Expired!
                    "monthly_fee": 2500.0,
                    "discount": 0.0,
                    "outstanding_amount": 2500.0,
                    "status": "Expired",
                    "trainer": None,
                    "amount_paid": 0.0,
                    "method": "JazzCash"
                },
                {
                    "member_id": "PK-1004",
                    "full_name": "Bilal Ahmed",
                    "father_name": "Ahmed Din",
                    "cnic": "35202-4455667-7",
                    "phone": "0312-3344556",
                    "emergency_contact": "0312-8877665",
                    "gender": "Male",
                    "dob": datetime.date(1996, 3, 10),
                    "address": "Gulshan-e-Ravi, Lahore",
                    "join_date": today - datetime.timedelta(days=85),
                    "plan": plan_3m,
                    "start_date": today - datetime.timedelta(days=85),
                    "expiry_date": today + datetime.timedelta(days=5),  # Expiring Soon!
                    "monthly_fee": 6500.0,
                    "discount": 500.0,
                    "outstanding_amount": 0.0,
                    "status": "Expiring Soon",
                    "trainer": t1,
                    "amount_paid": 6000.0,
                    "method": "Bank Transfer"
                },
                {
                    "member_id": "PK-1005",
                    "full_name": "Fatima Noor",
                    "father_name": "Noor Alam",
                    "cnic": "35201-7788990-2",
                    "phone": "0301-4455667",
                    "emergency_contact": "0301-9988776",
                    "gender": "Female",
                    "dob": datetime.date(1999, 7, 25),
                    "address": "Johar Town, Block G, Lahore",
                    "join_date": today - datetime.timedelta(days=15),
                    "plan": plan_yearly,
                    "start_date": today - datetime.timedelta(days=15),
                    "expiry_date": today + datetime.timedelta(days=350),
                    "monthly_fee": 18000.0,
                    "discount": 1000.0,
                    "outstanding_amount": 0.0,
                    "status": "Active",
                    "trainer": t2,
                    "amount_paid": 17000.0,
                    "method": "Bank Transfer"
                },
                {
                    "member_id": "PK-1006",
                    "full_name": "Zeeshan Butt",
                    "father_name": "Sohail Butt",
                    "cnic": "35202-3344551-9",
                    "phone": "0302-6677889",
                    "emergency_contact": "0302-5544332",
                    "gender": "Male",
                    "dob": datetime.date(1997, 12, 1),
                    "address": "Wapda Town, Lahore",
                    "join_date": today - datetime.timedelta(days=5),
                    "plan": plan_monthly,
                    "start_date": today - datetime.timedelta(days=5),
                    "expiry_date": today + datetime.timedelta(days=25),
                    "monthly_fee": 2500.0,
                    "discount": 0.0,
                    "outstanding_amount": 1000.0,  # Partial payment!
                    "status": "Active",
                    "trainer": None,
                    "amount_paid": 1500.0,
                    "method": "Cash"
                }
            ]

            created_members = []
            pay_idx = 1
            for item in members_data:
                m = Member(
                    member_id=item["member_id"],
                    full_name=item["full_name"],
                    father_name=item["father_name"],
                    cnic=item["cnic"],
                    phone=item["phone"],
                    emergency_contact=item["emergency_contact"],
                    gender=item["gender"],
                    dob=item["dob"],
                    address=item["address"],
                    join_date=item["join_date"],
                    current_plan_id=item["plan"].id if item["plan"] else None,
                    start_date=item["start_date"],
                    expiry_date=item["expiry_date"],
                    monthly_fee=item["monthly_fee"],
                    discount=item["discount"],
                    outstanding_amount=item["outstanding_amount"],
                    status=item["status"],
                    trainer_id=item["trainer"].id if item["trainer"] else None
                )
                db.add(m)
                db.flush()
                created_members.append((m, item))

                # Membership history
                if item["plan"]:
                    db.add(Membership(
                        member_id=m.id,
                        plan_id=item["plan"].id,
                        start_date=item["start_date"],
                        end_date=item["expiry_date"],
                        fee=item["monthly_fee"],
                        discount=item["discount"],
                        amount_paid=item["amount_paid"],
                        remaining_balance=item["outstanding_amount"],
                        notes="Initial registration plan"
                    ))

                # Payment record
                if item["amount_paid"] > 0:
                    p = Payment(
                        payment_id=f"REC-{today.year}-{pay_idx:04d}",
                        member_id=m.id,
                        amount=item["amount_paid"],
                        discount=item["discount"],
                        payment_date=item["start_date"],
                        payment_method=item["method"],
                        description=f"Fee Payment - {item['plan'].name if item['plan'] else 'Plan'}",
                        received_by="Asad Ali"
                    )
                    db.add(p)
                    pay_idx += 1

            db.commit()

            print("Seeding Today's Attendance...")
            # Check in Ali, Usman, Fatima today
            m1 = db.query(Member).filter(Member.member_id == "PK-1001").first()
            m2 = db.query(Member).filter(Member.member_id == "PK-1002").first()
            m5 = db.query(Member).filter(Member.member_id == "PK-1005").first()
            m6 = db.query(Member).filter(Member.member_id == "PK-1006").first()

            if m1:
                db.add(Attendance(member_id=m1.id, date=today, check_in_time=datetime.time(8, 30), status="Checked In"))
            if m2:
                db.add(Attendance(member_id=m2.id, date=today, check_in_time=datetime.time(9, 15), check_out_time=datetime.time(10, 45), status="Checked Out"))
            if m5:
                db.add(Attendance(member_id=m5.id, date=today, check_in_time=datetime.time(10, 5), status="Checked In"))
            if m6:
                db.add(Attendance(member_id=m6.id, date=today, check_in_time=datetime.time(11, 20), status="Checked In"))

            # Also seed some attendance for past 5 days
            for d_offset in range(1, 6):
                past_d = today - datetime.timedelta(days=d_offset)
                if m1:
                    db.add(Attendance(member_id=m1.id, date=past_d, check_in_time=datetime.time(8, 35), status="Checked In"))
                if m2:
                    db.add(Attendance(member_id=m2.id, date=past_d, check_in_time=datetime.time(9, 20), status="Checked In"))
                if m4 := db.query(Member).filter(Member.member_id == "PK-1004").first():
                    db.add(Attendance(member_id=m4.id, date=past_d, check_in_time=datetime.time(17, 30), status="Checked In"))

            print("Seeding Expenses...")
            expenses_data = [
                ("Electricity", 35000.0, today - datetime.timedelta(days=2), "LESCO commercial electricity bill for current month", "Malik Tariq"),
                ("Generator / Fuel", 8500.0, today - datetime.timedelta(days=1), "Diesel for backup power generator during load-shedding", "Hamza Qureshi"),
                ("Staff Salary", 75000.0, today - datetime.timedelta(days=4), "Salary advance for trainers and cleaner", "Malik Tariq"),
                ("Cleaning", 3500.0, today, "Detergents, floor wash, and disinfectant supplies", "Hamza Qureshi"),
                ("Maintenance", 4200.0, today - datetime.timedelta(days=3), "Cable replacement for lat pull-down machine", "Asad Ali")
            ]
            for cat, amt, edate, edesc, paidby in expenses_data:
                db.add(Expense(category=cat, amount=amt, date=edate, description=edesc, paid_by=paidby))

            print("Seeding Activity Logs...")
            activities = [
                ("Member Registered", "New member registered: Ali Raza Khan (PK-1001)", "Asad Ali"),
                ("Fee Received", "Payment of Rs. 2,500 received for Ali Raza Khan via Cash", "Asad Ali"),
                ("Member Registered", "New member registered: Usman Tariq (PK-1002)", "Asad Ali"),
                ("Fee Received", "Payment of Rs. 1,500 received for Usman Tariq via Easypaisa", "Asad Ali"),
                ("Member Checked In", "Ali Raza Khan (PK-1001) checked in at 08:30 AM", "System"),
                ("Member Checked In", "Usman Tariq (PK-1002) checked in at 09:15 AM", "System")
            ]
            for act, desc, perf in activities:
                db.add(ActivityLog(action=act, description=desc, performed_by=perf))

            db.commit()
            print("Successfully seeded all data!")
        else:
            print("Members already exist, skipping member seeding.")

    except Exception as e:
        db.rollback()
        print("Error during seed:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
