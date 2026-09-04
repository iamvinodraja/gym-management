import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base, get_active_db_type
from app.models import models
from app.routes import (
    auth,
    dashboard,
    members,
    plans,
    attendance,
    payments,
    expenses,
    staff,
    trainers,
    reports,
    settings,
)

# Auto create tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Pakistani Gym Management System",
    description="Modern, simple, fast, and practical Gym Management System tailored for Pakistani gyms",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(members.router)
app.include_router(plans.router)
app.include_router(attendance.router)
app.include_router(payments.router)
app.include_router(expenses.router)
app.include_router(staff.router)
app.include_router(trainers.router)
app.include_router(reports.router)
app.include_router(settings.router)

# Locate Frontend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Pakistani Gym Management System API is running. Frontend directory not found."}

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "app": "Pakistani Gym Management System",
        "database": get_active_db_type(),
        "currency": "PKR (Rs.)",
        "date_format": "DD-MM-YYYY"
    }
