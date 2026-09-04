from pydantic import BaseModel, Field
from typing import Optional, List, Any
import datetime

# --- Auth Schemas ---
class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    status: str

    class Config:
        from_attributes = True

# --- Plan Schemas ---
class PlanBase(BaseModel):
    name: str
    duration_days: int
    price: float
    description: Optional[str] = None
    is_active: bool = True

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PlanOut(PlanBase):
    id: int
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Trainer Schemas ---
class TrainerBase(BaseModel):
    name: str
    phone: str
    specialization: Optional[str] = "General Fitness"
    salary: Optional[float] = 0.0
    status: Optional[str] = "active"

class TrainerCreate(TrainerBase):
    pass

class TrainerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    salary: Optional[float] = None
    status: Optional[str] = None

class TrainerOut(TrainerBase):
    id: int
    assigned_members_count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Staff Schemas ---
class StaffBase(BaseModel):
    staff_id: str
    name: str
    phone: str
    cnic: Optional[str] = None
    role: str  # Owner, Manager, Receptionist, Trainer
    salary: Optional[float] = 0.0
    joining_date: datetime.date
    status: Optional[str] = "Active"

class StaffCreate(StaffBase):
    pass

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    cnic: Optional[str] = None
    role: Optional[str] = None
    salary: Optional[float] = None
    joining_date: Optional[datetime.date] = None
    status: Optional[str] = None

class StaffOut(StaffBase):
    id: int
    joining_date_formatted: Optional[str] = None

    class Config:
        from_attributes = True

# --- Member Schemas ---
class MemberCreate(BaseModel):
    full_name: str
    father_name: Optional[str] = None
    cnic: Optional[str] = None
    phone: str
    emergency_contact: Optional[str] = None
    gender: Optional[str] = "Male"
    dob: Optional[datetime.date] = None
    address: Optional[str] = None
    join_date: Optional[datetime.date] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    trainer_id: Optional[int] = None
    current_plan_id: Optional[int] = None
    start_date: Optional[datetime.date] = None
    monthly_fee: Optional[float] = 0.0
    discount: Optional[float] = 0.0
    amount_paid: Optional[float] = 0.0  # Initial payment on registration
    payment_method: Optional[str] = "Cash"

class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    father_name: Optional[str] = None
    cnic: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[datetime.date] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    trainer_id: Optional[int] = None
    status: Optional[str] = None

class MemberListItem(BaseModel):
    id: int
    member_id: str
    full_name: str
    phone: str
    cnic: Optional[str] = None
    plan_name: Optional[str] = "None"
    expiry_date: Optional[datetime.date] = None
    expiry_date_formatted: Optional[str] = None
    join_date_formatted: Optional[str] = None
    status: str
    remaining_days: int
    outstanding_amount: float
    trainer_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- Membership History Schema ---
class MembershipHistoryOut(BaseModel):
    id: int
    plan_name: Optional[str] = None
    start_date: datetime.date
    end_date: datetime.date
    start_date_formatted: Optional[str] = None
    end_date_formatted: Optional[str] = None
    fee: float
    discount: float
    amount_paid: float
    remaining_balance: float
    notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Payment Schemas ---
class PaymentCreate(BaseModel):
    member_id: int
    amount: float
    discount: Optional[float] = 0.0
    payment_date: Optional[datetime.date] = None
    payment_method: Optional[str] = "Cash"  # Cash, Bank Transfer, Easypaisa, JazzCash, Other
    description: Optional[str] = None
    received_by: Optional[str] = "Reception"

class PaymentOut(BaseModel):
    id: int
    payment_id: str
    member_id: int
    member_name: Optional[str] = None
    member_code: Optional[str] = None
    amount: float
    discount: float
    payment_date: datetime.date
    payment_date_formatted: Optional[str] = None
    payment_method: str
    description: Optional[str] = None
    received_by: str

    class Config:
        from_attributes = True

# --- Attendance Schemas ---
class AttendanceCheckIn(BaseModel):
    member_id: int
    allow_duplicate: bool = False

class AttendanceCheckOut(BaseModel):
    attendance_id: int

class AttendanceOut(BaseModel):
    id: int
    member_id: int
    member_name: str
    member_code: str
    date: datetime.date
    date_formatted: str
    check_in_time: str
    check_out_time: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

# --- Renewal Schema ---
class RenewalCreate(BaseModel):
    member_id: int
    plan_id: int
    fee: float
    discount: Optional[float] = 0.0
    amount_paid: float
    payment_method: Optional[str] = "Cash"
    start_from_expiry: bool = True  # If True and currently active, start after current expiry
    notes: Optional[str] = None

# --- Expense Schemas ---
class ExpenseCreate(BaseModel):
    category: str
    amount: float
    date: Optional[datetime.date] = None
    description: Optional[str] = None
    paid_by: Optional[str] = None

class ExpenseOut(BaseModel):
    id: int
    category: str
    amount: float
    date: datetime.date
    date_formatted: Optional[str] = None
    description: Optional[str] = None
    paid_by: Optional[str] = None

    class Config:
        from_attributes = True

# --- Settings Schema ---
class GymSettingsUpdate(BaseModel):
    gym_name: Optional[str] = None
    gym_address: Optional[str] = None
    gym_phone: Optional[str] = None
    currency_symbol: Optional[str] = "Rs."
    default_fee: Optional[float] = 2500.0
    warning_days: Optional[int] = 7
    receipt_footer: Optional[str] = None

class GymSettingsOut(BaseModel):
    gym_name: str
    gym_address: str
    gym_phone: str
    currency_symbol: str
    currency_code: str
    default_fee: float
    warning_days: int
    receipt_footer: str

# --- Member Profile Details ---
class MemberProfileOut(BaseModel):
    id: int
    member_id: str
    full_name: str
    father_name: Optional[str] = None
    cnic: Optional[str] = None
    phone: str
    emergency_contact: Optional[str] = None
    gender: str
    dob: Optional[datetime.date] = None
    dob_formatted: Optional[str] = None
    address: Optional[str] = None
    join_date: datetime.date
    join_date_formatted: str
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    status: str
    trainer_id: Optional[int] = None
    trainer_name: Optional[str] = None
    current_plan_id: Optional[int] = None
    plan_name: Optional[str] = None
    start_date: Optional[datetime.date] = None
    start_date_formatted: Optional[str] = None
    expiry_date: Optional[datetime.date] = None
    expiry_date_formatted: Optional[str] = None
    remaining_days: int
    monthly_fee: float
    discount: float
    outstanding_amount: float
    payments: List[PaymentOut] = []
    attendances: List[AttendanceOut] = []
    memberships: List[MembershipHistoryOut] = []
