import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models.models import (
    Payment,
    Expense,
    Member,
    Membership,
    Attendance,
    GymSetting,
)
from app.services.gym_service import (
    format_date_pk,
    format_currency_pk,
    calculate_member_status,
    parse_date_pk,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

def get_date_range(timeframe: str, custom_start: Optional[str] = None, custom_end: Optional[str] = None):
    today = datetime.date.today()
    if timeframe == "today":
        return today, today
    elif timeframe == "week":
        start = today - datetime.timedelta(days=today.weekday())
        return start, today
    elif timeframe == "month":
        start = datetime.date(today.year, today.month, 1)
        return start, today
    elif timeframe == "custom" and custom_start and custom_end:
        s = parse_date_pk(custom_start) or today
        e = parse_date_pk(custom_end) or today
        return s, e
    return datetime.date(today.year, today.month, 1), today

@router.get("/financial")
def financial_report(
    timeframe: str = "month",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    s_date, e_date = get_date_range(timeframe, start_date, end_date)

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    # Total Income
    income_sum = (
        db.query(func.sum(Payment.amount))
        .filter(Payment.payment_date >= s_date, Payment.payment_date <= e_date)
        .scalar() or 0.0
    )

    # Income breakdown by method
    method_breakdown = (
        db.query(Payment.payment_method, func.sum(Payment.amount))
        .filter(Payment.payment_date >= s_date, Payment.payment_date <= e_date)
        .group_by(Payment.payment_method)
        .all()
    )
    methods = [
        {"method": m[0], "amount": m[1], "amount_formatted": format_currency_pk(m[1], curr_sym)}
        for m in method_breakdown
    ]

    # Total Expenses
    expense_sum = (
        db.query(func.sum(Expense.amount))
        .filter(Expense.date >= s_date, Expense.date <= e_date)
        .scalar() or 0.0
    )

    # Expense breakdown by category
    category_breakdown = (
        db.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.date >= s_date, Expense.date <= e_date)
        .group_by(Expense.category)
        .all()
    )
    categories = [
        {"category": c[0], "amount": c[1], "amount_formatted": format_currency_pk(c[1], curr_sym)}
        for c in category_breakdown
    ]

    # Outstanding dues
    total_dues = db.query(func.sum(Member.outstanding_amount)).scalar() or 0.0

    net_profit = income_sum - expense_sum

    # Top recent payments in range
    recent_pays = (
        db.query(Payment)
        .filter(Payment.payment_date >= s_date, Payment.payment_date <= e_date)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
        .limit(20)
        .all()
    )
    payments_list = [
        {
            "id": p.id,
            "payment_id": p.payment_id,
            "member_name": p.member.full_name if p.member else "N/A",
            "amount_formatted": format_currency_pk(p.amount, curr_sym),
            "payment_method": p.payment_method,
            "date": format_date_pk(p.payment_date)
        }
        for p in recent_pays
    ]

    return {
        "period": {
            "timeframe": timeframe,
            "start_date": format_date_pk(s_date),
            "end_date": format_date_pk(e_date)
        },
        "summary": {
            "total_income": income_sum,
            "total_income_formatted": format_currency_pk(income_sum, curr_sym),
            "total_expenses": expense_sum,
            "total_expenses_formatted": format_currency_pk(expense_sum, curr_sym),
            "net_profit": net_profit,
            "net_profit_formatted": format_currency_pk(net_profit, curr_sym),
            "outstanding_dues": total_dues,
            "outstanding_dues_formatted": format_currency_pk(total_dues, curr_sym)
        },
        "income_by_method": methods,
        "expenses_by_category": categories,
        "payments": payments_list
    }

@router.get("/membership")
def membership_report(db: Session = Depends(get_db)):
    today = datetime.date.today()
    first_of_month = datetime.date(today.year, today.month, 1)

    warning_days_setting = db.query(GymSetting).filter(GymSetting.key_name == "warning_days").first()
    warning_days = int(warning_days_setting.key_value) if warning_days_setting else 7

    members = db.query(Member).all()
    total = len(members)
    active = 0
    expired = 0
    expiring_soon = 0
    new_this_month = 0

    for m in members:
        status, _ = calculate_member_status(m.expiry_date, warning_days)
        if status == "Active":
            active += 1
        elif status == "Expiring Soon":
            active += 1
            expiring_soon += 1
        elif status == "Expired":
            expired += 1

        if m.join_date >= first_of_month:
            new_this_month += 1

    renewals_this_month = (
        db.query(func.count(Membership.id))
        .filter(Membership.created_at >= datetime.datetime(today.year, today.month, 1))
        .scalar() or 0
    )

    # Popularity by plan
    from app.models.models import MembershipPlan
    plans = db.query(MembershipPlan).all()
    plan_stats = [
        {"name": p.name, "count": len(p.members) if p.members else 0}
        for p in plans
    ]

    return {
        "total_members": total,
        "active_members": active,
        "expired_members": expired,
        "expiring_soon": expiring_soon,
        "new_members_this_month": new_this_month,
        "renewals_this_month": renewals_this_month,
        "plan_popularity": plan_stats
    }

@router.get("/attendance")
def attendance_report(db: Session = Depends(get_db)):
    today = datetime.date.today()
    first_of_month = datetime.date(today.year, today.month, 1)

    # Today check-in count
    today_count = db.query(func.count(Attendance.id)).filter(Attendance.date == today).scalar() or 0
    month_count = db.query(func.count(Attendance.id)).filter(Attendance.date >= first_of_month).scalar() or 0

    # Most active members this month
    top_members_query = (
        db.query(Attendance.member_id, func.count(Attendance.id).label("visit_count"))
        .filter(Attendance.date >= first_of_month)
        .group_by(Attendance.member_id)
        .order_by(desc("visit_count"))
        .limit(10)
        .all()
    )

    leaderboard = []
    for row in top_members_query:
        m = db.query(Member).filter(Member.id == row[0]).first()
        if m:
            leaderboard.append({
                "member_id": m.member_id,
                "name": m.full_name,
                "phone": m.phone,
                "plan": m.current_plan.name if m.current_plan else "N/A",
                "visits": row[1]
            })

    # Daily visits for the last 7 days
    daily_stats = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        cnt = db.query(func.count(Attendance.id)).filter(Attendance.date == d).scalar() or 0
        daily_stats.append({
            "date": format_date_pk(d),
            "day": d.strftime("%A"),
            "count": cnt
        })

    return {
        "today_attendance": today_count,
        "month_attendance": month_count,
        "leaderboard": leaderboard,
        "daily_stats": daily_stats
    }
