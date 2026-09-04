import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import Attendance, Member
from app.schemas.schemas import AttendanceCheckIn, AttendanceCheckOut
from app.services.gym_service import format_date_pk, log_activity, parse_date_pk

router = APIRouter(prefix="/api/attendance", tags=["attendance"])

@router.get("/today")
def get_today_attendance(db: Session = Depends(get_db)):
    today = datetime.date.today()
    records = (
        db.query(Attendance)
        .filter(Attendance.date == today)
        .order_by(Attendance.id.desc())
        .all()
    )

    results = []
    for r in records:
        m = r.member
        results.append({
            "id": r.id,
            "member_id": m.member_id if m else "N/A",
            "full_name": m.full_name if m else "Unknown",
            "phone": m.phone if m else "",
            "member_db_id": m.id if m else 0,
            "date": format_date_pk(r.date),
            "check_in_time": r.check_in_time.strftime("%I:%M %p") if r.check_in_time else "",
            "check_out_time": r.check_out_time.strftime("%I:%M %p") if r.check_out_time else None,
            "status": r.status
        })
    return results

@router.get("/history")
def get_attendance_history(
    member_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)

    if member_id:
        query = query.filter(Attendance.member_id == member_id)

    if start_date:
        parsed_start = parse_date_pk(start_date)
        if parsed_start:
            query = query.filter(Attendance.date >= parsed_start)

    if end_date:
        parsed_end = parse_date_pk(end_date)
        if parsed_end:
            query = query.filter(Attendance.date <= parsed_end)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.join(Member).filter(
            (Member.full_name.ilike(search_pattern)) |
            (Member.phone.ilike(search_pattern)) |
            (Member.member_id.ilike(search_pattern))
        )

    records = query.order_by(Attendance.date.desc(), Attendance.id.desc()).limit(limit).all()

    results = []
    for r in records:
        m = r.member
        results.append({
            "id": r.id,
            "member_id": m.member_id if m else "N/A",
            "full_name": m.full_name if m else "Unknown",
            "phone": m.phone if m else "",
            "date": format_date_pk(r.date),
            "check_in_time": r.check_in_time.strftime("%I:%M %p") if r.check_in_time else "",
            "check_out_time": r.check_out_time.strftime("%I:%M %p") if r.check_out_time else None,
            "status": r.status
        })
    return results

@router.post("/check-in")
def check_in(data: AttendanceCheckIn, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == data.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    today = datetime.date.today()
    now_time = datetime.datetime.now().time()

    # Duplicate check for today
    existing = (
        db.query(Attendance)
        .filter(Attendance.member_id == member.id, Attendance.date == today)
        .order_by(Attendance.id.desc())
        .first()
    )

    if existing and not data.allow_duplicate:
        return {
            "duplicate": True,
            "message": f"Member {member.full_name} is already checked in today at {existing.check_in_time.strftime('%I:%M %p')}.",
            "existing_id": existing.id
        }

    attendance = Attendance(
        member_id=member.id,
        date=today,
        check_in_time=now_time,
        status="Checked In"
    )
    db.add(attendance)
    log_activity(db, "Member Check-In", f"{member.full_name} ({member.member_id}) checked in at {now_time.strftime('%I:%M %p')}")
    db.commit()
    db.refresh(attendance)

    return {
        "success": True,
        "duplicate": False,
        "message": f"Checked in {member.full_name} successfully at {now_time.strftime('%I:%M %p')}",
        "attendance_id": attendance.id,
        "check_in_time": now_time.strftime("%I:%M %p")
    }

@router.post("/check-out")
def check_out(data: AttendanceCheckOut, db: Session = Depends(get_db)):
    att = db.query(Attendance).filter(Attendance.id == data.attendance_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    now_time = datetime.datetime.now().time()
    att.check_out_time = now_time
    att.status = "Checked Out"

    m = att.member
    log_activity(db, "Member Check-Out", f"{m.full_name if m else 'Member'} checked out at {now_time.strftime('%I:%M %p')}")
    db.commit()

    return {
        "success": True,
        "message": f"Checked out successfully at {now_time.strftime('%I:%M %p')}",
        "check_out_time": now_time.strftime("%I:%M %p")
    }
