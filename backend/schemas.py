from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

# ---------- Auth ----------

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    flat_no: str = Field(min_length=1, max_length=30)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
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


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Complaints ----------

class HistoryOut(BaseModel):
    status: str
    note: Optional[str]
    actor_name: str
    created_at: datetime


class ComplaintOut(BaseModel):
    id: int
    category: str
    title: str
    description: str
    photo_url: Optional[str]
    priority: str
    status: str
    is_overdue: bool
    days_open: int
    created_at: datetime
    resolved_at: Optional[datetime]
    resident_name: str
    resident_flat: str
    history: List[HistoryOut]


class StatusUpdateIn(BaseModel):
    status: str  # "In Progress" | "Resolved"
    note: Optional[str] = Field(default=None, max_length=500)


class PriorityUpdateIn(BaseModel):
    priority: str  # Low | Medium | High


class OverdueFlagIn(BaseModel):
    flagged: bool


# ---------- Notices ----------

class NoticeIn(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    body: str = Field(min_length=3)
    is_important: bool = False


class NoticeOut(BaseModel):
    id: int
    title: str
    body: str
    is_important: bool
    author_name: str
    created_at: datetime


# ---------- Dashboard / Settings ----------

class DashboardOut(BaseModel):
    total: int
    by_status: dict
    by_category: dict
    overdue_count: int
    overdue_threshold_days: int


class OverdueThresholdIn(BaseModel):
    days: int = Field(ge=1, le=90)
