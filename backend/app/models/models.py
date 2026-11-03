import datetime
from datetime import timezone, timedelta
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    Time,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base

# Pakistan Standard Time (PKT, UTC+5)
PKT_ZONE = timezone(timedelta(hours=5))

def get_pk_now():
    return datetime.datetime.now(PKT_ZONE).replace(tzinfo=None)

def get_pk_today():
    return datetime.datetime.now(PKT_ZONE).date()

def get_pk_time():
    return datetime.datetime.now(PKT_ZONE).time()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="receptionist", nullable=False)  # admin, receptionist
    status = Column(String(20), default="active", nullable=False)  # active, inactive
    created_at = Column(DateTime, default=get_pk_now)

class Trainer(Base):
    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    specialization = Column(String(100), default="General Fitness")
    salary = Column(Float, default=0.0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=get_pk_now)

    members = relationship("Member", back_populates="trainer")

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    cnic = Column(String(20), nullable=True)
    role = Column(String(50), nullable=False)  # Owner, Manager, Receptionist, Trainer
    salary = Column(Float, default=0.0)
    joining_date = Column(Date, nullable=False)
    status = Column(String(20), default="Active")
    created_at = Column(DateTime, default=get_pk_now)

class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    duration_days = Column(Integer, nullable=False)  # e.g. 30, 90, 180, 365
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_pk_now)

    members = relationship("Member", back_populates="current_plan")

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=True)
    cnic = Column(String(20), nullable=True, index=True)
    phone = Column(String(20), nullable=False, index=True)
    emergency_contact = Column(String(20), nullable=True)
    gender = Column(String(10), default="Male")  # Male, Female, Other
    dob = Column(Date, nullable=True)
    address = Column(Text, nullable=True)
    join_date = Column(Date, nullable=False, default=get_pk_today)
    photo_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    trainer_id = Column(Integer, ForeignKey("trainers.id", ondelete="SET NULL"), nullable=True)
    current_plan_id = Column(Integer, ForeignKey("membership_plans.id", ondelete="SET NULL"), nullable=True)

    start_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    monthly_fee = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    outstanding_amount = Column(Float, default=0.0)
    status = Column(String(20), default="Active")  # Active, Expiring Soon, Expired, Inactive

    created_at = Column(DateTime, default=get_pk_now)
    updated_at = Column(DateTime, default=get_pk_now, onupdate=get_pk_now)

    trainer = relationship("Trainer", back_populates="members")
    current_plan = relationship("MembershipPlan", back_populates="members")
    memberships = relationship("Membership", back_populates="member", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="member", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="member", cascade="all, delete-orphan")

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("membership_plans.id", ondelete="SET NULL"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    fee = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)
    remaining_balance = Column(Float, default=0.0)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_pk_now)

    member = relationship("Member", back_populates="memberships")
    plan = relationship("MembershipPlan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String(30), unique=True, nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    payment_date = Column(Date, nullable=False, default=get_pk_today, index=True)
    payment_method = Column(String(30), default="Cash")  # Cash, Bank Transfer, Easypaisa, JazzCash, Other
    description = Column(String(255), nullable=True)
    received_by = Column(String(100), default="Reception")
    created_at = Column(DateTime, default=get_pk_now)

    member = relationship("Member", back_populates="payments")

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, default=get_pk_today, index=True)
    check_in_time = Column(Time, nullable=False, default=get_pk_time)
    check_out_time = Column(Time, nullable=True)
    status = Column(String(20), default="Checked In")  # Checked In, Checked Out
    created_at = Column(DateTime, default=get_pk_now)

    member = relationship("Member", back_populates="attendances")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)  # Electricity, Rent, Equipment, Cleaning, Staff Salary, Maintenance, Water, Generator, Other
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, default=get_pk_today)
    description = Column(Text, nullable=True)
    paid_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=get_pk_now)

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    performed_by = Column(String(100), default="System")
    timestamp = Column(DateTime, default=get_pk_now)

class GymSetting(Base):
    __tablename__ = "gym_settings"

    id = Column(Integer, primary_key=True, index=True)
    key_name = Column(String(50), unique=True, nullable=False)
    key_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=get_pk_now, onupdate=get_pk_now)
