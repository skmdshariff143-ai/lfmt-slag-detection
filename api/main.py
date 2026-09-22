"""
FastAPI REST Backend for LFMT Slag Detection & Thermographic Defect Analyzer.
"""

from __future__ import annotations
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure repo root and src are on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

import os
from api.routes import analyze, examples, simulate

app = FastAPI(
    title="LFMT Intelligent Thermographic Defect Analyzer API",
    description=(
        "Autonomous physics-informed NDT diagnosis service supporting multi-format ingestion, "
        "scientific method selection, Raw/PCT/SPCT/RPT/MF processing, AI multi-task characterization, "
        "epistemic uncertainty estimation, and diagnostic report generation."
    ),
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS with explicit allowed origins
raw_origins = os.getenv("LFMT_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000")
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register API routers
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(examples.router, prefix="/api/v1")
app.include_router(simulate.router, prefix="/api/v1")


@app.get("/")
async def root_health():
    """Service health and version telemetry."""
    return {
        "service": "LFMT Intelligent Thermographic Defect Analyzer API",
        "version": "3.0.0",
        "status": "healthy",
        "endpoints": {
            "upload_analysis": "/api/v1/analyze/upload",
            "preset_analysis": "/api/v1/analyze/preset/{preset_id}",
            "docs": "/api/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
