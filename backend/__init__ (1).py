import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form,
                     HTTPException, UploadFile)
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user, require_admin
from ..database import get_db
from ..emailer import notify_status_change
from ..models import Complaint, Setting, StatusHistory, User
from ..schemas import (ComplaintOut, HistoryOut, OverdueFlagIn,
                       PriorityUpdateIn, StatusUpdateIn)

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB

CATEGORIES = ["Plumbing", "Electrical", "Elevator", "Cleaning", "Security", "Parking", "Other"]
STATUSES = ["Open", "In Progress", "Resolved"]
PRIORITIES = ["Low", "Medium", "High"]
PRIORITY_WEIGHT = {"High": 0, "Medium": 1, "Low": 2}


def get_overdue_days(db: Session) -> int:
    row = db.query(Setting).get("overdue_days")
    if row:
        return int(row.value)
    return int(os.getenv("OVERDUE_DAYS", "7"))


def is_overdue(c: Complaint, threshold_days: int) -> bool:
    if c.status == "Resolved":
        return False
    auto = (datetime.utcnow() - c.created_at) >= timedelta(days=threshold_days)
    return auto or c.flagged_overdue


def to_out(c: Complaint, threshold_days: int) -> ComplaintOut:
    end = c.resolved_at or datetime.utcnow()
    return ComplaintOut(
        id=c.id,
        category=c.category,
        title=c.title,
        description=c.description,
        photo_url=f"/uploads/{c.photo_path}" if c.photo_path else None,
        priority=c.priority,
        status=c.status,
        is_overdue=is_overdue(c, threshold_days),
        days_open=(end - c.created_at).days,
        created_at=c.created_at,
        resolved_at=c.resolved_at,
        resident_name=c.owner.name,
        resident_flat=c.owner.flat_no,
        history=[
            HistoryOut(status=h.status, note=h.note,
                       actor_name=h.actor.name, created_at=h.created_at)
            for h in c.history
        ],
    )


@router.get("/categories")
def categories():
    return {"categories": CATEGORIES, "statuses": STATUSES, "priorities": PRIORITIES}


@router.post("", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    category: str = Form(...),
    title: str = Form(..., min_length=3, max_length=150),
    description: str = Form(..., min_length=5),
    photo: Optional[UploadFile] = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Category must be one of: {', '.join(CATEGORIES)}")

    photo_name = None
    if photo and photo.filename:
        ext = os.path.splitext(photo.filename)[1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=422, detail="Photo must be a JPG, PNG or WEBP image")
        content = await photo.read()
        if len(content) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=422, detail="Photo must be under 5 MB")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        photo_name = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(UPLOAD_DIR, photo_name), "wb") as f:
            f.write(content)

    complaint = Complaint(
        user_id=user.id,
        category=category,
        title=title.strip(),
        description=description.strip(),
        photo_path=photo_name,
    )
    db.add(complaint)
    db.flush()
    # every complaint starts its history at "Open"
    db.add(StatusHistory(complaint_id=complaint.id, status="Open",
                         note="Complaint raised", actor_id=user.id))
    db.commit()
    db.refresh(complaint)
    return to_out(complaint, get_overdue_days(db))


@router.get("/mine", response_model=list[ComplaintOut])
def my_complaints(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    threshold = get_overdue_days(db)
    complaints = (
        db.query(Complaint)
        .options(joinedload(Complaint.history).joinedload(StatusHistory.actor),
                 joinedload(Complaint.owner))
        .filter(Complaint.user_id == user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return [to_out(c, threshold) for c in complaints]


@router.get("", response_model=list[ComplaintOut])
def all_complaints(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,  # YYYY-MM-DD
    date_to: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Complaint).options(
        joinedload(Complaint.history).joinedload(StatusHistory.actor),
        joinedload(Complaint.owner),
    )
    if category:
        q = q.filter(Complaint.category == category)
    if status:
        q = q.filter(Complaint.status == status)
    if date_from:
        q = q.filter(Complaint.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(Complaint.created_at < datetime.fromisoformat(date_to) + timedelta(days=1))

    threshold = get_overdue_days(db)
    complaints = q.all()
    # overdue first, then by priority (High > Medium > Low), then newest
    complaints.sort(key=lambda c: (
        not is_overdue(c, threshold),
        PRIORITY_WEIGHT.get(c.priority, 1),
        -c.created_at.timestamp(),
    ))
    return [to_out(c, threshold) for c in complaints]


def _get_or_404(db: Session, complaint_id: int) -> Complaint:
    c = (
        db.query(Complaint)
        .options(joinedload(Complaint.history).joinedload(StatusHistory.actor),
                 joinedload(Complaint.owner))
        .get(complaint_id)
    )
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return c


@router.post("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(
    complaint_id: int,
    data: StatusUpdateIn,
    background: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if data.status not in STATUSES:
        raise HTTPException(status_code=422, detail=f"Status must be one of: {', '.join(STATUSES)}")

    c = _get_or_404(db, complaint_id)
    if c.status == "Resolved":
        raise HTTPException(status_code=409, detail="This complaint is resolved and closed")
    if data.status == c.status:
        raise HTTPException(status_code=409, detail=f"Complaint is already {c.status}")

    c.status = data.status
    if data.status == "Resolved":
        c.resolved_at = datetime.utcnow()
        c.flagged_overdue = False
    db.add(StatusHistory(complaint_id=c.id, status=data.status,
                         note=data.note, actor_id=admin.id))
    db.commit()
    db.refresh(c)

    background.add_task(notify_status_change, c.owner.email, c.owner.name,
                        c.title, data.status, data.note)
    return to_out(c, get_overdue_days(db))


@router.patch("/{complaint_id}/priority", response_model=ComplaintOut)
def update_priority(
    complaint_id: int,
    data: PriorityUpdateIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if data.priority not in PRIORITIES:
        raise HTTPException(status_code=422, detail="Priority must be Low, Medium or High")
    c = _get_or_404(db, complaint_id)
    c.priority = data.priority
    db.commit()
    db.refresh(c)
    return to_out(c, get_overdue_days(db))


@router.patch("/{complaint_id}/overdue", response_model=ComplaintOut)
def flag_overdue(
    complaint_id: int,
    data: OverdueFlagIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    c = _get_or_404(db, complaint_id)
    if c.status == "Resolved":
        raise HTTPException(status_code=409, detail="Resolved complaints cannot be flagged overdue")
    c.flagged_overdue = data.flagged
    db.commit()
    db.refresh(c)
    return to_out(c, get_overdue_days(db))
