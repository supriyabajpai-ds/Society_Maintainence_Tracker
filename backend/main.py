"""App entry point: creates the FastAPI app, wires up routers,
mounts static files/uploads, and seeds the admin account on startup."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import Base, engine, SessionLocal
from backend import models
from backend.auth import hash_password
from backend.routers import (
    auth_router,
    complaints_router,
    notices_router,
    dashboard_router,
)

app = FastAPI(title="Nivaas — Society Maintenance Tracker")

# Allow the frontend (served separately or from this same origin) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables if they don't exist yet
Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def seed_admin() -> None:
    """Create the default admin account on first start, if it doesn't exist."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@nivaas-society.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == admin_email).first()
        if not existing:
            admin = models.User(
                name="Admin",
                flat_no="—",
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


# API routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(complaints_router.router, prefix="/api/complaints", tags=["complaints"])
app.include_router(notices_router.router, prefix="/api/notices", tags=["notices"])
app.include_router(dashboard_router.router, prefix="/api", tags=["dashboard"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# Serve uploaded complaint photos
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Serve the frontend (index.html, resident.html, admin.html, css/, js/) at the root
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
