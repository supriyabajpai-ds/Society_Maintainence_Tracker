import os
import uuid
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Complaint, StatusHistory, Setting
from ..auth import get_current_user, require_admin
from ..emailer import notify_status_change
from ..schemas import ComplaintOut, CategoriesOut, HistoryItemOut, StatusUpdateRequest, PriorityUpdateRequest, OverdueUpdateRequest

router = APIRouter()

CATEGORIES = ["Plumbing", "Electrical", "Cleaning", "Security", "Lift", "Parking", "Other"]
STATUSES = ["Open", "In Progress", "Resolved"]
PRIORITIES = ["Low", "Medium", "High"]
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

DEFAULT_OVERDUE_DAYS = 7


def get_overdue_days(db: Session) -> int:
    setting = db.query(Setting).filter(Setting.key == "overdue_days").first()
    if setting:
        try:
            return int(setting.value)
        except ValueError:
            pass
    return DEFAULT_OVERDUE_DAYS


def serialize(c: Complaint, overdue_days: int) -> ComplaintOut:
    now = datetime.utcnow()
    reference_end = c.resolved_at or now
    days_open = (reference_end - c.created_at).days

    if c.status == "Resolved":
        is_overdue = False
    else:
        is_overdue = c.flagged_overdue or days_open > overdue_days

    return ComplaintOut(
        id=c.id,
        category=c.category,
        title=c.title,
        description=c.description,
        photo_url=(f"/uploads/{c.photo_path}" if c.photo_path else None),
        priority=c.priority,
        status=c.status,
        is_overdue=is_overdue,
        days_open=days_open,
        created_at=c.created_at,
        resolved_at=c.resolved_at,
        resident_name=c.owner.name,
        resident_flat=c.owner.flat_no,
        history=[
            HistoryItemOut(
                status=h.status,
                note=h.note,
                actor_name=h.actor.name,
                created_at=h.created_at,
            )
            for h in c.history
        ],
    )


@router.get("/categories", response_model=CategoriesOut)
def categories():
    return CategoriesOut(categories=CATEGORIES, statuses=STATUSES, priorities=PRIORITIES)


@router.post("", response_model=ComplaintOut)
def raise_complaint(
    category: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo_path = None
    if photo is not None and photo.filename:
        if photo.content_type not in ALLOWED_PHOTO_TYPES:
            raise HTTPException(status_code=400, detail="Photo must be JPG, PNG, or WEBP")

        contents = photo.file.read()
        if len(contents) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=400, detail="Photo must be 5MB or smaller")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(photo.filename)[1] or ".jpg"
        photo_path = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(UPLOAD_DIR, photo_path), "wb") as f:
            f.write(contents)

    complaint = Complaint(
        user_id=current_user.id,
        category=category,
        title=title,
        description=description,
        photo_path=photo_path,
        status="Open",
        priority="Medium",
    )
    db.add(complaint)
    db.flush()

    db.add(StatusHistory(
        complaint_id=complaint.id,
        status="Open",
        note="Complaint raised",
        actor_id=current_user.id,
    ))
    db.commit()
    db.refresh(complaint)

    return serialize(complaint, get_overdue_days(db))


@router.get("/mine", response_model=list[ComplaintOut])
def my_complaints(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    overdue_days = get_overdue_days(db)
    complaints = (
        db.query(Complaint)
        .filter(Complaint.user_id == current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return [serialize(c, overdue_days) for c in complaints]


@router.get("", response_model=list[ComplaintOut])
def all_complaints(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)
    if category:
        query = query.filter(Complaint.category == category)
    if status:
        query = query.filter(Complaint.status == status)
    if date_from:
        query = query.filter(Complaint.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Complaint.created_at <= datetime.combine(date_to, datetime.max.time()))

    overdue_days = get_overdue_days(db)
    complaints = query.all()
    serialized = [serialize(c, overdue_days) for c in complaints]

    serialized.sort(
        key=lambda c: (
            not c.is_overdue,                       # overdue first
            PRIORITY_ORDER.get(c.priority, 3),       # then priority High->Low
            -c.created_at.timestamp(),               # then newest first
        )
    )
    return serialized


@router.post("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(
    complaint_id: int,
    payload: StatusUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.status == "Resolved":
        raise HTTPException(status_code=400, detail="Complaint is resolved and closed")
    if payload.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    complaint.status = payload.status
    if payload.status == "Resolved":
        complaint.resolved_at = datetime.utcnow()
        complaint.flagged_overdue = False

    db.add(StatusHistory(
        complaint_id=complaint.id,
        status=payload.status,
        note=payload.note,
        actor_id=admin.id,
    ))
    db.commit()
    db.refresh(complaint)

    notify_status_change(
        to=complaint.owner.email,
        resident_name=complaint.owner.name,
        complaint_title=complaint.title,
        new_status=complaint.status,
        note=payload.note,
    )

    return serialize(complaint, get_overdue_days(db))


@router.patch("/{complaint_id}/priority", response_model=ComplaintOut)
def update_priority(
    complaint_id: int,
    payload: PriorityUpdateRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.priority not in PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid priority")

    complaint = db.query(Complaint).get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.priority = payload.priority
    db.commit()
    db.refresh(complaint)
    return serialize(complaint, get_overdue_days(db))


@router.patch("/{complaint_id}/overdue", response_model=ComplaintOut)
def update_overdue_flag(
    complaint_id: int,
    payload: OverdueUpdateRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.flagged_overdue = payload.flagged
    db.commit()
    db.refresh(complaint)
    return serialize(complaint, get_overdue_days(db))
