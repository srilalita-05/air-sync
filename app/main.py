"""
AirSync FastAPI Application Entry Point.

Problem Statement: SIH26082 (Air Pollution–Weather Coupled Forecasting System - Delhi-NCR Focus)
Team: Semantic Souls (SIH 2026)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import router as api_router

app = FastAPI(
    title="AirSync Forecasting Backend",
    description="Physics-informed air pollution–weather coupled forecasting platform for Delhi-NCR (SIH 2026)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend web dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routes
app.include_router(api_router)

# Mount frontend directory if it exists
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/dashboard", StaticFiles(directory=frontend_dir, html=True), name="dashboard")


@app.get("/")
def root():
    return {
        "system": "AirSync Air Pollution–Weather Coupled Forecasting Engine",
        "sih_problem_id": "SIH26082",
        "team": "Semantic Souls",
        "status": "running",
        "documentation": "/docs",
        "web_dashboard": "/dashboard/",
    }
