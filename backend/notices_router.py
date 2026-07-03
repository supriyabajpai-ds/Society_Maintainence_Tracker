from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..models import Complaint, Setting, User
from ..routers.complaints_router import get_overdue_days, is_overdue
from ..schemas import DashboardOut, OverdueThresholdIn

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()
    threshold = get_overdue_days(db)

    by_status: dict[str, int] = {"Open": 0, "In Progress": 0, "Resolved": 0}
    by_category: dict[str, int] = {}
    overdue = 0
    for c in complaints:
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_category[c.category] = by_category.get(c.category, 0) + 1
        if is_overdue(c, threshold):
            overdue += 1

    return DashboardOut(
        total=len(complaints),
        by_status=by_status,
        by_category=by_category,
        overdue_count=overdue,
        overdue_threshold_days=threshold,
    )


@router.put("/settings/overdue-days")
def set_overdue_days(
    data: OverdueThresholdIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = db.query(Setting).get("overdue_days")
    if row:
        row.value = str(data.days)
    else:
        db.add(Setting(key="overdue_days", value=str(data.days)))
    db.commit()
    return {"overdue_days": data.days}
