from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Notice
from ..auth import get_current_user, require_admin
from ..emailer import notify_important_notice
from ..schemas import NoticeCreate, NoticeOut

router = APIRouter()


@router.get("", response_model=list[NoticeOut])
def list_notices(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notices = (
        db.query(Notice)
        .order_by(Notice.is_important.desc(), Notice.created_at.desc())
        .all()
    )
    return [
        NoticeOut(
            id=n.id,
            title=n.title,
            body=n.body,
            is_important=n.is_important,
            created_at=n.created_at,
            author_name=n.author.name,
        )
        for n in notices
    ]


@router.post("", response_model=NoticeOut)
def create_notice(
    payload: NoticeCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    notice = Notice(
        title=payload.title,
        body=payload.body,
        is_important=payload.is_important,
        author_id=admin.id,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)

    if notice.is_important:
        residents = db.query(User).filter(User.role == "resident").all()
        for resident in residents:
            notify_important_notice(
                to=resident.email,
                resident_name=resident.name,
                title=notice.title,
                notice_body=notice.body,
            )

    return NoticeOut(
        id=notice.id,
        title=notice.title,
        body=notice.body,
        is_important=notice.is_important,
        created_at=notice.created_at,
        author_name=notice.author.name,
    )
