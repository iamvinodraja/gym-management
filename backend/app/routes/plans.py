from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import MembershipPlan, GymSetting
from app.schemas.schemas import PlanCreate, PlanUpdate, PlanOut
from app.services.gym_service import format_currency_pk, log_activity

router = APIRouter(prefix="/api/plans", tags=["plans"])

@router.get("")
def list_plans(active_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(MembershipPlan)
    if active_only:
        query = query.filter(MembershipPlan.is_active == True)
    plans = query.order_by(MembershipPlan.duration_days.asc()).all()

    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    result = []
    for p in plans:
        result.append({
            "id": p.id,
            "name": p.name,
            "duration_days": p.duration_days,
            "price": p.price,
            "price_formatted": format_currency_pk(p.price, curr_sym),
            "description": p.description or "",
            "is_active": p.is_active,
            "member_count": len(p.members) if p.members else 0
        })
    return result

@router.post("")
def create_plan(data: PlanCreate, db: Session = Depends(get_db)):
    plan = MembershipPlan(
        name=data.name.strip(),
        duration_days=data.duration_days,
        price=data.price,
        description=data.description.strip() if data.description else None,
        is_active=data.is_active
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    log_activity(db, "Plan Created", f"New membership plan created: {plan.name} (Rs. {plan.price:,.0f})")
    return {"success": True, "message": "Plan created successfully", "id": plan.id}

@router.put("/{plan_id}")
def update_plan(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if data.name is not None:
        plan.name = data.name.strip()
    if data.duration_days is not None:
        plan.duration_days = data.duration_days
    if data.price is not None:
        plan.price = data.price
    if data.description is not None:
        plan.description = data.description.strip()
    if data.is_active is not None:
        plan.is_active = data.is_active

    db.commit()
    log_activity(db, "Plan Updated", f"Plan updated: {plan.name} (Rs. {plan.price:,.0f})")
    return {"success": True, "message": "Plan updated successfully"}
