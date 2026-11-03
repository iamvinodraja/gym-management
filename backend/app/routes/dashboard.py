import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import get_db
from app.models.models import Member, Payment, Attendance, ActivityLog, GymSetting
from app.services.gym_service import format_date_pk, calculate_member_status, format_currency_pk, get_pakistan_date

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def get_dashboard_data(db: Session = Depends(get_db)):
    today = get_pakistan_date()
    first_of_month = datetime.date(today.year, today.month, 1)

    # Fetch gym settings for warning days
    warning_days_setting = db.query(GymSetting).filter(GymSetting.key_name == "warning_days").first()
    warning_days = int(warning_days_setting.key_value) if warning_days_setting else 7
    currency_symbol = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = currency_symbol.key_value if currency_symbol else "Rs."

    # All members query to accurately compute active / expiring / expired status
    members = db.query(Member).all()
    total_members = len(members)
    active_count = 0
    expired_count = 0
    expiring_soon_count = 0
    total_pending_dues = 0.0

    expiring_soon_list = []

    for m in members:
        # Dynamically verify and update status
        status, days_left = calculate_member_status(m.expiry_date, warning_days)
        if m.status != status and m.status != "Inactive":
            m.status = status
        
        if m.status == "Active":
            active_count += 1
        elif m.status == "Expiring Soon":
            active_count += 1
            expiring_soon_count += 1
            expiring_soon_list.append({
                "id": m.id,
                "member_id": m.member_id,
                "name": m.full_name,
                "phone": m.phone,
                "plan": m.current_plan.name if m.current_plan else "Custom",
                "expiry_date": format_date_pk(m.expiry_date),
                "days_left": days_left,
                "outstanding_amount": m.outstanding_amount,
                "outstanding_formatted": format_currency_pk(m.outstanding_amount, curr_sym)
            })
        elif m.status == "Expired":
            expired_count += 1

        total_pending_dues += (m.outstanding_amount or 0.0)

    # Sort expiring soon by days left ascending
    expiring_soon_list.sort(key=lambda x: x["days_left"])

    # Today's attendance
    today_attendances = (
        db.query(Attendance)
        .filter(Attendance.date == today)
        .order_by(Attendance.id.desc())
        .all()
    )
    today_attendance_count = len(today_attendances)
    attendance_list = []
    for att in today_attendances[:10]:
        m = att.member
        attendance_list.append({
            "id": att.id,
            "member_id": m.member_id if m else "N/A",
            "name": m.full_name if m else "Unknown",
            "phone": m.phone if m else "",
            "check_in": att.check_in_time.strftime("%I:%M %p") if att.check_in_time else "",
            "check_out": att.check_out_time.strftime("%I:%M %p") if att.check_out_time else "-",
            "status": att.status
        })

    # Today's collections
    today_collections_sum = (
        db.query(func.sum(Payment.amount))
        .filter(Payment.payment_date == today)
        .scalar() or 0.0
    )

    # Month collections
    month_collections_sum = (
        db.query(func.sum(Payment.amount))
        .filter(Payment.payment_date >= first_of_month)
        .scalar() or 0.0
    )

    # New members this month
    new_members_this_month = (
        db.query(func.count(Member.id))
        .filter(Member.join_date >= first_of_month)
        .scalar() or 0
    )

    # Recent payments
    recent_payments_query = (
        db.query(Payment)
        .order_by(Payment.id.desc())
        .limit(8)
        .all()
    )
    recent_payments = []
    for p in recent_payments_query:
        recent_payments.append({
            "id": p.id,
            "payment_id": p.payment_id,
            "member_name": p.member.full_name if p.member else "N/A",
            "member_code": p.member.member_id if p.member else "N/A",
            "amount": p.amount,
            "amount_formatted": format_currency_pk(p.amount, curr_sym),
            "payment_method": p.payment_method,
            "date": format_date_pk(p.payment_date),
            "received_by": p.received_by
        })

    # Recent activity logs
    recent_activities = (
        db.query(ActivityLog)
        .order_by(ActivityLog.id.desc())
        .limit(10)
        .all()
    )
    activities = []
    for act in recent_activities:
        time_str = act.timestamp.strftime("%d-%m-%Y %I:%M %p") if act.timestamp else ""
        activities.append({
            "id": act.id,
            "action": act.action,
            "description": act.description,
            "performed_by": act.performed_by,
            "time": time_str
        })

    db.commit()

    return {
        "kpis": {
            "total_members": total_members,
            "active_members": active_count,
            "expired_members": expired_count,
            "expiring_soon": expiring_soon_count,
            "today_attendance": today_attendance_count,
            "today_collections": today_collections_sum,
            "today_collections_formatted": format_currency_pk(today_collections_sum, curr_sym),
            "month_collections": month_collections_sum,
            "month_collections_formatted": format_currency_pk(month_collections_sum, curr_sym),
            "pending_payments": total_pending_dues,
            "pending_payments_formatted": format_currency_pk(total_pending_dues, curr_sym),
            "new_members_this_month": new_members_this_month,
        },
        "today_attendance": attendance_list,
        "expiring_soon": expiring_soon_list[:10],
        "recent_payments": recent_payments,
        "recent_activities": activities
    }
