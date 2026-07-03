from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class RegisterRequest(BaseModel):
    name: str
    flat_no: str
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    flat_no: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    token: str
    user: UserOut


# ---------- Complaints ----------

class HistoryItemOut(BaseModel):
    status: str
    note: Optional[str] = None
    actor_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ComplaintOut(BaseModel):
    id: int
    category: str
    title: str
    description: str
    photo_url: Optional[str] = None
    priority: str
    status: str
    is_overdue: bool
    days_open: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resident_name: str
    resident_flat: str
    history: List[HistoryItemOut] = []


class CategoriesOut(BaseModel):
    categories: List[str]
    statuses: List[str]
    priorities: List[str]


class StatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = None


class PriorityUpdateRequest(BaseModel):
    priority: str


class OverdueUpdateRequest(BaseModel):
    flagged: bool


# ---------- Notices ----------

class NoticeCreate(BaseModel):
    title: str
    body: str
    is_important: bool = False


class NoticeOut(BaseModel):
    id: int
    title: str
    body: str
    is_important: bool
    created_at: datetime
    author_name: str

    class Config:
        from_attributes = True


# ---------- Dashboard & settings ----------

class DashboardOut(BaseModel):
    total: int
    by_status: dict
    by_category: dict
    overdue_count: int
    overdue_threshold_days: int


class OverdueDaysUpdate(BaseModel):
    days: int = Field(ge=1, le=90)
