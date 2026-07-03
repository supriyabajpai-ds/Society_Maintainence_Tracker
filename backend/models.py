from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    flat_no = Column(String(30), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="resident", nullable=False)  # resident | admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaints = relationship("Complaint", back_populates="owner")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    photo_path = Column(String(255), nullable=True)
    priority = Column(String(10), default="Medium", nullable=False)  # Low | Medium | High
    status = Column(String(20), default="Open", nullable=False, index=True)  # Open | In Progress | Resolved
    flagged_overdue = Column(Boolean, default=False, nullable=False)  # manual admin flag
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="complaints")
    history = relationship(
        "StatusHistory",
        back_populates="complaint",
        order_by="StatusHistory.created_at",
        cascade="all, delete-orphan",
    )


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    status = Column(String(20), nullable=False)
    note = Column(Text, nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="history")
    actor = relationship("User")


class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    is_important = Column(Boolean, default=False, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    author = relationship("User")


class Setting(Base):
    """Simple key-value store for admin-configurable settings (e.g. overdue threshold)."""

    __tablename__ = "settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=False)
