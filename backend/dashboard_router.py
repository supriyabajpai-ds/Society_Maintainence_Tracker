from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import create_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        name=data.name.strip(),
        flat_no=data.flat_no.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role="resident",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
