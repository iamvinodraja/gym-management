import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models.models import Expense, GymSetting
from app.schemas.schemas import ExpenseCreate
from app.services.gym_service import format_date_pk, format_currency_pk, log_activity, parse_date_pk

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

@router.get("")
def list_expenses(
    category: Optional[str] = None,
    month: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Expense)

    if category and category != "All":
        query = query.filter(Expense.category == category)

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    expenses = query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    results = []
    for exp in expenses:
        results.append({
            "id": exp.id,
            "category": exp.category,
            "amount": exp.amount,
            "amount_formatted": format_currency_pk(exp.amount, curr_sym),
            "date": format_date_pk(exp.date),
            "description": exp.description or "",
            "paid_by": exp.paid_by or "Admin"
        })
    return results

@router.get("/summary")
def get_expense_summary(db: Session = Depends(get_db)):
    today = datetime.date.today()
    first_of_month = datetime.date(today.year, today.month, 1)

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    today_sum = db.query(func.sum(Expense.amount)).filter(Expense.date == today).scalar() or 0.0
    month_sum = db.query(func.sum(Expense.amount)).filter(Expense.date >= first_of_month).scalar() or 0.0
    total_sum = db.query(func.sum(Expense.amount)).scalar() or 0.0

    # Category breakdown for this month
    cat_breakdown = (
        db.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.date >= first_of_month)
        .group_by(Expense.category)
        .all()
    )
    categories = [
        {"category": c[0], "total": c[1], "total_formatted": format_currency_pk(c[1], curr_sym)}
        for c in cat_breakdown
    ]

    return {
        "today_expenses": today_sum,
        "today_expenses_formatted": format_currency_pk(today_sum, curr_sym),
        "month_expenses": month_sum,
        "month_expenses_formatted": format_currency_pk(month_sum, curr_sym),
        "total_expenses": total_sum,
        "total_expenses_formatted": format_currency_pk(total_sum, curr_sym),
        "categories": categories
    }

@router.post("")
def add_expense(data: ExpenseCreate, db: Session = Depends(get_db)):
    exp_date = data.date or datetime.date.today()
    expense = Expense(
        category=data.category.strip(),
        amount=data.amount,
        date=exp_date,
        description=data.description.strip() if data.description else None,
        paid_by=data.paid_by or "Admin"
    )
    db.add(expense)

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    log_activity(db, "Expense Added", f"Expense of {format_currency_pk(expense.amount, curr_sym)} recorded for {expense.category} ({expense.description or ''})")
    db.commit()

    return {"success": True, "message": "Expense added successfully", "id": expense.id}
