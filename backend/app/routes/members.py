import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from app.database import get_db
from app.models.models import (
    Member,
    MembershipPlan,
    Membership,
    Payment,
    Attendance,
    Trainer,
    GymSetting,
)
from app.schemas.schemas import MemberCreate, MemberUpdate, MemberProfileOut
from app.services.gym_service import (
    generate_member_id,
    generate_payment_id,
    calculate_member_status,
    format_date_pk,
    format_currency_pk,
    log_activity,
    get_pakistan_date,
    get_pakistan_now,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/members", tags=["members"])

@router.get("")
def list_members(
    q: Optional[str] = None,
    status: Optional[str] = None,
    plan_id: Optional[int] = None,
    has_dues: Optional[bool] = None,
    gender: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Member)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Member.full_name.ilike(search_pattern),
                Member.phone.ilike(search_pattern),
                Member.member_id.ilike(search_pattern),
                Member.cnic.ilike(search_pattern)
            )
        )

    if plan_id:
        query = query.filter(Member.current_plan_id == plan_id)

    if gender:
        query = query.filter(Member.gender == gender)

    warning_days_setting = db.query(GymSetting).filter(GymSetting.key_name == "warning_days").first()
    warning_days = int(warning_days_setting.key_value) if warning_days_setting else 7
    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    members = query.order_by(Member.id.desc()).all()
    results = []

    for m in members:
        # Dynamically recalculate status based on current date
        curr_status, days_left = calculate_member_status(m.expiry_date, warning_days)
        if m.status != curr_status and m.status != "Inactive":
            m.status = curr_status

        # Status filter
        if status and status.lower() != "all":
            if status.lower() == "active" and m.status not in ("Active", "Expiring Soon"):
                continue
            elif status.lower() == "expiring soon" and m.status != "Expiring Soon":
                continue
            elif status.lower() == "expired" and m.status != "Expired":
                continue
            elif status.lower() == "inactive" and m.status != "Inactive":
                continue

        # Dues filter
        if has_dues is True and (m.outstanding_amount or 0) <= 0:
            continue

        results.append({
            "id": m.id,
            "member_id": m.member_id,
            "full_name": m.full_name,
            "phone": m.phone,
            "cnic": m.cnic or "",
            "gender": m.gender,
            "plan_name": m.current_plan.name if m.current_plan else "No Plan",
            "current_plan_id": m.current_plan_id,
            "join_date": format_date_pk(m.join_date),
            "expiry_date": format_date_pk(m.expiry_date),
            "status": m.status,
            "remaining_days": days_left,
            "monthly_fee": m.monthly_fee,
            "outstanding_amount": m.outstanding_amount,
            "outstanding_formatted": format_currency_pk(m.outstanding_amount, curr_sym),
            "trainer_name": m.trainer.name if m.trainer else None
        })

    db.commit()
    return results

@router.get("/quick-search")
def quick_search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Fast receptionist search by name, phone, CNIC, or ID"""
    pattern = f"%{q.strip()}%"
    members = (
        db.query(Member)
        .filter(
            or_(
                Member.full_name.ilike(pattern),
                Member.phone.ilike(pattern),
                Member.member_id.ilike(pattern),
                Member.cnic.ilike(pattern)
            )
        )
        .limit(10)
        .all()
    )

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    results = []
    today = get_pakistan_date()
    for m in members:
        # Check if checked in today
        today_checkin = (
            db.query(Attendance)
            .filter(Attendance.member_id == m.id, Attendance.date == today)
            .first()
        )
        results.append({
            "id": m.id,
            "member_id": m.member_id,
            "full_name": m.full_name,
            "phone": m.phone,
            "status": m.status,
            "expiry_date": format_date_pk(m.expiry_date),
            "plan_name": m.current_plan.name if m.current_plan else "No Plan",
            "outstanding_formatted": format_currency_pk(m.outstanding_amount, curr_sym),
            "has_checked_in_today": bool(today_checkin),
            "checked_in_time": today_checkin.check_in_time.strftime("%I:%M %p") if today_checkin else None
        })
    return results

@router.get("/{member_id}")
def get_member_profile(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")

    warning_days_setting = db.query(GymSetting).filter(GymSetting.key_name == "warning_days").first()
    warning_days = int(warning_days_setting.key_value) if warning_days_setting else 7
    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    status, days_left = calculate_member_status(m.expiry_date, warning_days)
    if m.status != status and m.status != "Inactive":
        m.status = status
        db.commit()

    # Payments history
    payments = (
        db.query(Payment)
        .filter(Payment.member_id == m.id)
        .order_by(Payment.id.desc())
        .all()
    )
    payment_list = []
    for p in payments:
        payment_list.append({
            "id": p.id,
            "payment_id": p.payment_id,
            "amount": p.amount,
            "amount_formatted": format_currency_pk(p.amount, curr_sym),
            "discount": p.discount,
            "payment_date": format_date_pk(p.payment_date),
            "payment_method": p.payment_method,
            "description": p.description or "",
            "received_by": p.received_by
        })

    # Attendance history
    attendances = (
        db.query(Attendance)
        .filter(Attendance.member_id == m.id)
        .order_by(Attendance.id.desc())
        .limit(30)
        .all()
    )
    attendance_list = []
    for a in attendances:
        attendance_list.append({
            "id": a.id,
            "date": format_date_pk(a.date),
            "check_in_time": a.check_in_time.strftime("%I:%M %p") if a.check_in_time else "",
            "check_out_time": a.check_out_time.strftime("%I:%M %p") if a.check_out_time else "-",
            "status": a.status
        })

    # Membership history (renewals & plans)
    memberships = (
        db.query(Membership)
        .filter(Membership.member_id == m.id)
        .order_by(Membership.id.desc())
        .all()
    )
    membership_list = []
    for mh in memberships:
        membership_list.append({
            "id": mh.id,
            "plan_name": mh.plan.name if mh.plan else "Custom",
            "start_date": format_date_pk(mh.start_date),
            "end_date": format_date_pk(mh.end_date),
            "fee": mh.fee,
            "fee_formatted": format_currency_pk(mh.fee, curr_sym),
            "discount": mh.discount,
            "amount_paid": mh.amount_paid,
            "remaining_balance": mh.remaining_balance,
            "notes": mh.notes or "",
            "created_at": mh.created_at.strftime("%d-%m-%Y %I:%M %p") if mh.created_at else ""
        })

    return {
        "id": m.id,
        "member_id": m.member_id,
        "full_name": m.full_name,
        "father_name": m.father_name or "",
        "cnic": m.cnic or "",
        "phone": m.phone,
        "emergency_contact": m.emergency_contact or "",
        "gender": m.gender,
        "dob": format_date_pk(m.dob),
        "address": m.address or "",
        "join_date": format_date_pk(m.join_date),
        "photo_url": m.photo_url or "",
        "notes": m.notes or "",
        "status": m.status,
        "trainer_id": m.trainer_id,
        "trainer_name": m.trainer.name if m.trainer else None,
        "current_plan_id": m.current_plan_id,
        "plan_name": m.current_plan.name if m.current_plan else "No Plan",
        "start_date": format_date_pk(m.start_date),
        "expiry_date": format_date_pk(m.expiry_date),
        "remaining_days": days_left,
        "monthly_fee": m.monthly_fee,
        "monthly_fee_formatted": format_currency_pk(m.monthly_fee, curr_sym),
        "discount": m.discount,
        "outstanding_amount": m.outstanding_amount,
        "outstanding_formatted": format_currency_pk(m.outstanding_amount, curr_sym),
        "payments": payment_list,
        "attendances": attendance_list,
        "memberships": membership_list
    }

@router.post("")
def add_member(data: MemberCreate, db: Session = Depends(get_db)):
    try:
        # Auto-generate Member ID (guaranteed collision-free)
        gen_id = generate_member_id(db)

        # Dates setup
        pk_today = get_pakistan_date()
        pk_now = get_pakistan_now()
        join_d = data.join_date or pk_today
        start_d = data.start_date or join_d

        plan = None
        expiry_d = None
        if data.current_plan_id:
            plan = db.query(MembershipPlan).filter(MembershipPlan.id == data.current_plan_id).first()
            if plan:
                expiry_d = start_d + datetime.timedelta(days=plan.duration_days)

        # Financial calculations
        fee = data.monthly_fee if (data.monthly_fee is not None and data.monthly_fee > 0) else (plan.price if plan else 0.0)
        discount = data.discount or 0.0
        payable = max(0.0, fee - discount)
        amount_paid = data.amount_paid or 0.0
        outstanding = max(0.0, payable - amount_paid)

        warning_days_setting = db.query(GymSetting).filter(GymSetting.key_name == "warning_days").first()
        warning_days = int(warning_days_setting.key_value) if warning_days_setting else 7
        status, _ = calculate_member_status(expiry_d, warning_days)

        new_member = Member(
            member_id=gen_id,
            full_name=data.full_name.strip()[:100],
            father_name=data.father_name.strip()[:100] if data.father_name else None,
            cnic=data.cnic.strip()[:20] if data.cnic else None,
            phone=data.phone.strip()[:20],
            emergency_contact=data.emergency_contact.strip()[:20] if data.emergency_contact else None,
            gender=data.gender or "Male",
            dob=data.dob,
            address=data.address.strip() if data.address else None,
            join_date=join_d,
            photo_url=data.photo_url,
            notes=data.notes,
            trainer_id=data.trainer_id,
            current_plan_id=data.current_plan_id,
            start_date=start_d,
            expiry_date=expiry_d,
            monthly_fee=fee,
            discount=discount,
            outstanding_amount=outstanding,
            status=status,
            created_at=pk_now,
            updated_at=pk_now
        )
        db.add(new_member)
        db.flush()

        # Record initial membership period in history
        if plan and expiry_d:
            history_entry = Membership(
                member_id=new_member.id,
                plan_id=plan.id,
                start_date=start_d,
                end_date=expiry_d,
                fee=fee,
                discount=discount,
                amount_paid=amount_paid,
                remaining_balance=outstanding,
                notes="Initial Registration Membership",
                created_at=pk_now
            )
            db.add(history_entry)

        # If initial payment made, create payment record using LIVE Pakistan date and time
        receipt_id = None
        if amount_paid > 0:
            pay_id = generate_payment_id(db)
            payment_record = Payment(
                payment_id=pay_id,
                member_id=new_member.id,
                amount=amount_paid,
                discount=discount,
                payment_date=pk_today,
                payment_method=data.payment_method or "Cash",
                description=f"Registration & Plan fee ({plan.name if plan else 'Custom'})",
                received_by="Reception",
                created_at=pk_now
            )
            db.add(payment_record)
            db.flush()
            receipt_id = payment_record.id

        log_activity(db, "Member Registered", f"New member registered: {new_member.full_name} ({new_member.member_id})")
        db.commit()
        db.refresh(new_member)

        return {
            "success": True,
            "message": f"Member {new_member.full_name} added successfully with ID {new_member.member_id}",
            "member_id": new_member.id,
            "member_code": new_member.member_id,
            "receipt_id": receipt_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to add member: {str(e)}")

@router.put("/{member_id}")
def update_member(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")

    if data.full_name is not None:
        m.full_name = data.full_name.strip()
    if data.father_name is not None:
        m.father_name = data.father_name.strip()
    if data.cnic is not None:
        m.cnic = data.cnic.strip()
    if data.phone is not None:
        m.phone = data.phone.strip()
    if data.emergency_contact is not None:
        m.emergency_contact = data.emergency_contact.strip()
    if data.gender is not None:
        m.gender = data.gender
    if data.dob is not None:
        m.dob = data.dob
    if data.address is not None:
        m.address = data.address.strip()
    if data.photo_url is not None:
        m.photo_url = data.photo_url
    if data.notes is not None:
        m.notes = data.notes
    if data.trainer_id is not None:
        m.trainer_id = data.trainer_id if data.trainer_id > 0 else None
    if data.status is not None:
        m.status = data.status

    log_activity(db, "Member Updated", f"Profile updated for {m.full_name} ({m.member_id})")
    db.commit()
    return {"success": True, "message": "Member updated successfully"}

@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")

    # Rather than hard deleting financial history, we mark as Inactive to preserve accounts & attendance!
    m.status = "Inactive"
    log_activity(db, "Member Deactivated", f"Member {m.full_name} ({m.member_id}) marked as Inactive")
    db.commit()
    return {"success": True, "message": f"Member {m.member_id} deactivated. Financial records preserved."}
