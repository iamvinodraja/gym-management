from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Trainer, Member, GymSetting
from app.schemas.schemas import TrainerCreate, TrainerUpdate
from app.services.gym_service import format_currency_pk, log_activity

router = APIRouter(prefix="/api/trainers", tags=["trainers"])

@router.get("")
def list_trainers(db: Session = Depends(get_db)):
    trainers = db.query(Trainer).order_by(Trainer.id.asc()).all()
    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    results = []
    for t in trainers:
        assigned_count = db.query(func.count(Member.id)).filter(Member.trainer_id == t.id).scalar() or 0
        results.append({
            "id": t.id,
            "name": t.name,
            "phone": t.phone,
            "specialization": t.specialization or "General Fitness",
            "salary": t.salary,
            "salary_formatted": format_currency_pk(t.salary, curr_sym),
            "status": t.status,
            "assigned_members_count": assigned_count
        })
    return results

@router.post("")
def add_trainer(data: TrainerCreate, db: Session = Depends(get_db)):
    trainer = Trainer(
        name=data.name.strip(),
        phone=data.phone.strip(),
        specialization=data.specialization.strip() if data.specialization else "General Fitness",
        salary=data.salary or 0.0,
        status=data.status or "active"
    )
    db.add(trainer)
    log_activity(db, "Trainer Added", f"New trainer added: {trainer.name} ({trainer.specialization})")
    db.commit()

    return {"success": True, "message": "Trainer added successfully", "id": trainer.id}

@router.put("/{trainer_id}")
def update_trainer(trainer_id: int, data: TrainerUpdate, db: Session = Depends(get_db)):
    t = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trainer not found")

    if data.name is not None:
        t.name = data.name.strip()
    if data.phone is not None:
        t.phone = data.phone.strip()
    if data.specialization is not None:
        t.specialization = data.specialization.strip()
    if data.salary is not None:
        t.salary = data.salary
    if data.status is not None:
        t.status = data.status

    db.commit()
    return {"success": True, "message": "Trainer updated successfully"}
