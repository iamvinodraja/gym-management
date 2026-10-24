import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Staff, GymSetting
from app.schemas.schemas import StaffCreate, StaffUpdate
from app.services.gym_service import format_date_pk, format_currency_pk, log_activity

router = APIRouter(prefix="/api/staff", tags=["staff"])

@router.get("")
def list_staff(db: Session = Depends(get_db)):
    staff_members = db.query(Staff).order_by(Staff.id.asc()).all()
    curr_setting = db.query(GymSetting).filter(GymSetting.key_name == "currency_symbol").first()
    curr_sym = curr_setting.key_value if curr_setting else "Rs."

    results = []
    for s in staff_members:
        results.append({
            "id": s.id,
            "staff_id": s.staff_id,
            "name": s.name,
            "phone": s.phone,
            "cnic": s.cnic or "",
            "role": s.role,
            "salary": s.salary,
            "salary_formatted": format_currency_pk(s.salary, curr_sym),
            "joining_date": format_date_pk(s.joining_date),
            "status": s.status
        })
    return results

@router.post("")
def add_staff(data: StaffCreate, db: Session = Depends(get_db)):
    existing = db.query(Staff).filter(Staff.staff_id == data.staff_id.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Staff ID already exists")

    staff = Staff(
        staff_id=data.staff_id.strip(),
        name=data.name.strip(),
        phone=data.phone.strip(),
        cnic=data.cnic.strip() if data.cnic else None,
        role=data.role,
        salary=data.salary or 0.0,
        joining_date=data.joining_date,
        status=data.status or "Active"
    )
    db.add(staff)
    log_activity(db, "Staff Added", f"New staff member added: {staff.name} ({staff.role})")
    db.commit()

    return {"success": True, "message": "Staff member added successfully", "id": staff.id}

@router.put("/{staff_id}")
def update_staff(staff_id: int, data: StaffUpdate, db: Session = Depends(get_db)):
    s = db.query(Staff).filter(Staff.id == staff_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Staff not found")

    if data.name is not None:
        s.name = data.name.strip()
    if data.phone is not None:
        s.phone = data.phone.strip()
    if data.cnic is not None:
        s.cnic = data.cnic.strip()
    if data.role is not None:
        s.role = data.role
    if data.salary is not None:
        s.salary = data.salary
    if data.joining_date is not None:
        s.joining_date = data.joining_date
    if data.status is not None:
        s.status = data.status

    db.commit()
    return {"success": True, "message": "Staff member updated successfully"}

@router.delete("/{staff_id}")
def delete_staff(staff_id: int, db: Session = Depends(get_db)):
    s = db.query(Staff).filter(Staff.id == staff_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Staff not found")
    staff_name = s.name
    db.delete(s)
    log_activity(db, "Staff Deleted", f"Staff member removed: {staff_name}")
    db.commit()
    return {"success": True, "message": "Staff member deleted successfully"}
