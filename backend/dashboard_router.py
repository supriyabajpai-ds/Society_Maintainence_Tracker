from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Complaint, Setting
from ..auth import require_admin
from ..schemas import DashboardOut, OverdueDaysUpdate
from .complaints_router import get_overdue_days, CATEGORIES, STATUSES

router = APIRouter()


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    overdue_days = get_overdue_days(db)
    complaints = db.query(Complaint).all()

    by_status = {s: 0 for s in STATUSES}
    by_category = {c: 0 for c in CATEGORIES}
    overdue_count = 0

    for c in complaints:
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_category[c.category] = by_category.get(c.category, 0) + 1

        if c.status != "Resolved":
            reference_end = datetime.utcnow()
            days_open = (reference_end - c.created_at).days
            if c.flagged_overdue or days_open > overdue_days:
                overdue_count += 1

    return DashboardOut(
        total=len(complaints),
        by_status=by_status,
        by_category=by_category,
        overdue_count=overdue_count,
        overdue_threshold_days=overdue_days,
    )


@router.put("/settings/overdue-days")
def update_overdue_days(
    payload: OverdueDaysUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    setting = db.query(Setting).filter(Setting.key == "overdue_days").first()
    if setting:
        setting.value = str(payload.days)
    else:
        db.add(Setting(key="overdue_days", value=str(payload.days)))
    db.commit()
    return {"overdue_threshold_days": payload.days}
