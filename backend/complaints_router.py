from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user, require_admin
from ..database import get_db
from ..emailer import notify_important_notice
from ..models import Notice, User
from ..schemas import NoticeIn, NoticeOut

router = APIRouter(prefix="/api/notices", tags=["notices"])


def to_out(n: Notice) -> NoticeOut:
    return NoticeOut(
        id=n.id, title=n.title, body=n.body, is_important=n.is_important,
        author_name=n.author.name, created_at=n.created_at,
    )


@router.get("", response_model=list[NoticeOut])
def list_notices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notices = (
        db.query(Notice)
        .options(joinedload(Notice.author))
        .order_by(Notice.is_important.desc(), Notice.created_at.desc())
        .all()
    )
    return [to_out(n) for n in notices]


@router.post("", response_model=NoticeOut, status_code=201)
def create_notice(
    data: NoticeIn,
    background: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    notice = Notice(
        title=data.title.strip(),
        body=data.body.strip(),
        is_important=data.is_important,
        author_id=admin.id,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)

    if notice.is_important:
        residents = db.query(User).filter(User.role == "resident").all()
        for r in residents:
            background.add_task(notify_important_notice, r.email, r.name,
                                notice.title, notice.body)
    return to_out(notice)
