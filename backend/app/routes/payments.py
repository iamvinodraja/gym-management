import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from app.database import get_db
from app.models.models import (
    Payment,
    Member,
    MembershipPlan,
    Membership,
    GymSetting,
)
from app.schemas.schemas import PaymentCreate, RenewalCreate
from app.services.gym_service import (
    generate_payment_id,
    format_date_pk,
    format_currency_pk,
    calculate_member_status,
    log_activity,
    get_gym_setting,
    parse_date_pk,
    get_pakistan_date,
    get_pakistan_now,
    format_time_pk,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.get("")
def list_payments(
    member_id: Optional[int] = None,
    method: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Payment)

    if member_id:
        query = query.filter(Payment.member_id == member_id)

    if method and method != "All":
        query = query.filter(Payment.payment_method == method)

    if start_date:
        parsed_s = parse_date_pk(start_date)
        if parsed_s:
            query = query.filter(Payment.payment_date >= parsed_s)

    if end_date:
        parsed_e = parse_date_pk(end_date)
        if parsed_e:
            query = query.filter(Payment.payment_date <= parsed_e)

    if q:
        pat = f"%{q.strip()}%"
        query = query.join(Member).filter(
            or_(
                Member.full_name.ilike(pat),
                Member.phone.ilike(pat),
                Member.member_id.ilike(pat),
                Payment.payment_id.ilike(pat)
            )
        )

    payments = query.order_by(Payment.payment_date.desc(), Payment.id.desc()).limit(limit).all()

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    results = []
    for p in payments:
        m = p.member
        results.append({
            "id": p.id,
            "payment_id": p.payment_id,
            "member_id": m.id if m else 0,
            "member_code": m.member_id if m else "N/A",
            "member_name": m.full_name if m else "Unknown",
            "phone": m.phone if m else "",
            "amount": p.amount,
            "amount_formatted": format_currency_pk(p.amount, curr_sym),
            "discount": p.discount,
            "payment_date": format_date_pk(p.payment_date),
            "payment_method": p.payment_method,
            "description": p.description or "",
            "received_by": p.received_by
        })
    return results

@router.get("/summary")
def get_payment_summary(db: Session = Depends(get_db)):
    today = get_pakistan_date()
    first_of_month = datetime.date(today.year, today.month, 1)

    today_sum = db.query(func.sum(Payment.amount)).filter(Payment.payment_date == today).scalar() or 0.0
    month_sum = db.query(func.sum(Payment.amount)).filter(Payment.payment_date >= first_of_month).scalar() or 0.0
    total_dues = db.query(func.sum(Member.outstanding_amount)).scalar() or 0.0

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    return {
        "today_collected": today_sum,
        "today_collected_formatted": format_currency_pk(today_sum, curr_sym),
        "month_collected": month_sum,
        "month_collected_formatted": format_currency_pk(month_sum, curr_sym),
        "total_dues": total_dues,
        "total_dues_formatted": format_currency_pk(total_dues, curr_sym)
    }

@router.post("")
def record_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == data.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    pay_id = generate_payment_id(db)
    pay_date = data.payment_date or datetime.date.today()

    payment = Payment(
        payment_id=pay_id,
        member_id=member.id,
        amount=data.amount,
        discount=data.discount or 0.0,
        payment_date=pay_date,
        payment_method=data.payment_method or "Cash",
        description=data.description or "Fee Payment",
        received_by=data.received_by or "Reception"
    )
    db.add(payment)

    # Update member's outstanding balance
    # Outstanding reduces by (amount + discount)
    net_cleared = data.amount + (data.discount or 0.0)
    member.outstanding_amount = max(0.0, (member.outstanding_amount or 0.0) - net_cleared)

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    log_activity(db, "Fee Received", f"Payment of {format_currency_pk(data.amount, curr_sym)} received for {member.full_name} ({member.member_id}) via {payment.payment_method}")
    db.commit()

    return {
        "success": True,
        "message": f"Payment recorded successfully. Receipt No: {pay_id}",
        "payment_id": payment.id,
        "receipt_code": pay_id,
        "remaining_dues": member.outstanding_amount,
        "remaining_dues_formatted": format_currency_pk(member.outstanding_amount, curr_sym)
    }

@router.post("/renew")
def renew_membership(data: RenewalCreate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == data.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    plan = db.query(MembershipPlan).filter(MembershipPlan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    pk_today = get_pakistan_date()
    pk_now = get_pakistan_now()

    # Determine start and new expiry date
    # If member is currently active and expiry_date > today, start from current expiry
    if data.start_from_expiry and member.expiry_date and member.expiry_date >= pk_today:
        new_start_date = member.expiry_date
    else:
        new_start_date = pk_today

    new_expiry_date = new_start_date + datetime.timedelta(days=plan.duration_days)

    fee = data.fee if data.fee > 0 else plan.price
    discount = data.discount or 0.0
    payable = max(0.0, fee - discount)
    amount_paid = data.amount_paid or 0.0
    new_unpaid = max(0.0, payable - amount_paid)

    # Add to existing outstanding amount
    member.outstanding_amount = (member.outstanding_amount or 0.0) + new_unpaid

    # Update member current plan & expiry
    member.current_plan_id = plan.id
    member.start_date = new_start_date
    member.expiry_date = new_expiry_date
    member.monthly_fee = fee

    warning_days_setting = db.query(GymSetting).filter(GymSetting.key_name == "warning_days").first()
    warning_days = int(warning_days_setting.key_value) if warning_days_setting else 7
    status, _ = calculate_member_status(new_expiry_date, warning_days)
    member.status = status

    # Create historical record in memberships table
    history = Membership(
        member_id=member.id,
        plan_id=plan.id,
        start_date=new_start_date,
        end_date=new_expiry_date,
        fee=fee,
        discount=discount,
        amount_paid=amount_paid,
        remaining_balance=new_unpaid,
        notes=data.notes or f"Renewed for {plan.name}",
        created_at=pk_now
    )
    db.add(history)

    # Create payment record if any amount paid - uses LIVE Pakistan date/time
    receipt_code = None
    payment_id_val = None
    if amount_paid > 0:
        receipt_code = generate_payment_id(db)
        payment_entry = Payment(
            payment_id=receipt_code,
            member_id=member.id,
            amount=amount_paid,
            discount=discount,
            payment_date=pk_today,
            payment_method=data.payment_method or "Cash",
            description=f"Renewal fee for {plan.name}",
            received_by="Reception",
            created_at=pk_now
        )
        db.add(payment_entry)
        db.flush()
        payment_id_val = payment_entry.id

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    log_activity(db, "Membership Renewed", f"Membership renewed for {member.full_name} ({member.member_id}) - Plan: {plan.name}, New Expiry: {format_date_pk(new_expiry_date)}")
    db.commit()

    return {
        "success": True,
        "message": f"Membership renewed successfully until {format_date_pk(new_expiry_date)}",
        "new_expiry_date": format_date_pk(new_expiry_date),
        "receipt_id": payment_id_val,
        "receipt_code": receipt_code,
        "remaining_dues": member.outstanding_amount,
        "remaining_dues_formatted": format_currency_pk(member.outstanding_amount, curr_sym)
    }

@router.get("/{payment_id}/receipt")
def get_receipt_data(payment_id: int, db: Session = Depends(get_db)):
    """Returns complete printable receipt data in Pakistani Rupee format"""
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment record not found")

    m = p.member
    gym_name = get_gym_setting(db, "gym_name", "Power Fitness Gym")
    gym_address = get_gym_setting(db, "gym_address", "Karachi, Pakistan")
    gym_phone = get_gym_setting(db, "gym_phone", "0300-1234567")
    curr_sym = get_gym_setting(db, "currency_symbol", "Rs.")
    footer = get_gym_setting(db, "receipt_footer", "Thank you for training with us! Fees once paid are non-refundable.")

    plan_name = m.current_plan.name if m and m.current_plan else "General Membership"

    return {
        "gym": {
            "name": gym_name,
            "address": gym_address,
            "phone": gym_phone,
            "footer": footer
        },
        "receipt": {
            "receipt_no": p.payment_id,
            "date": format_date_pk(p.payment_date),
            "created_time": format_time_pk(p.created_at) if p.created_at else "",
            "payment_method": p.payment_method,
            "received_by": p.received_by,
            "description": p.description or f"Gym Fee - {plan_name}"
        },
        "member": {
            "id": m.id if m else 0,
            "member_id": m.member_id if m else "N/A",
            "name": m.full_name if m else "Unknown",
            "phone": m.phone if m else "",
            "plan_name": plan_name,
            "expiry_date": format_date_pk(m.expiry_date) if m else "",
            "remaining_balance": m.outstanding_amount if m else 0.0,
            "remaining_balance_formatted": format_currency_pk(m.outstanding_amount if m else 0.0, curr_sym)
        },
        "amount": {
            "paid": p.amount,
            "paid_formatted": format_currency_pk(p.amount, curr_sym),
            "discount": p.discount,
            "discount_formatted": format_currency_pk(p.discount, curr_sym)
        }
    }
