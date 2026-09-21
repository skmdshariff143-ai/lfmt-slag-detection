"""
FastAPI Routes for Intelligent Thermographic Defect Analyzer.
"""

from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse

from lfmt.analysis.analyzer import AutoDefectAnalyzer, AnalysisResult
from lfmt.reporting.report_generator import DefectReportGenerator
from api.schemas.analysis import AnalysisResponseSchema, AnalysisRequestMetadata

router = APIRouter(prefix="/analyze", tags=["Intelligent Defect Analyzer"])

# In-memory storage for analysis results & artifact paths
ANALYSIS_CACHE: Dict[str, AnalysisResult] = {}
ARTIFACTS_CACHE: Dict[str, Dict[str, str]] = {}
ANALYZER_INSTANCE = AutoDefectAnalyzer()


@router.post("/upload", response_model=AnalysisResponseSchema)
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    temp_units: Optional[str] = Form(None),
    frame_rate_hz: Optional[float] = Form(None),
    fov_length_mm: Optional[float] = Form(None),
    fov_width_mm: Optional[float] = Form(None),
    material: Optional[str] = Form("mild_steel"),
    excitation_type: Optional[str] = Form(None),
    f0_hz: Optional[float] = Form(None),
    f1_hz: Optional[float] = Form(None),
    apply_baseline: bool = Form(True),
    smooth_sigma_px: float = Form(0.0)
):
    """
    Upload and analyze an arbitrary thermographic file (ZIP, NPZ, NPY, MAT, CSV, PNG, JPG, TIFF).
    """
    suffix = Path(file.filename or "upload.bin").suffix.lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_f:
        shutil.copyfileobj(file.file, tmp_f)
        tmp_path = Path(tmp_f.name)

    try:
        fov_mm = (fov_length_mm, fov_width_mm) if (fov_length_mm and fov_width_mm) else None
        meta_override = {
            "temp_units": temp_units,
            "frame_rate_hz": frame_rate_hz,
            "fov_mm": fov_mm,
            "material": material,
            "excitation_type": excitation_type,
            "excitation": {"f0_hz": f0_hz, "f1_hz": f1_hz, "type": excitation_type} if (f0_hz or excitation_type) else {}
        }
        # Filter None values
        meta_override = {k: v for k, v in meta_override.items() if v is not None}

        result = ANALYZER_INSTANCE.analyze(
            source=tmp_path,
            metadata_override=meta_override,
            apply_baseline=apply_baseline,
            smooth_sigma_px=smooth_sigma_px
        )

        ANALYSIS_CACHE[result.analysis_id] = result
        
        # Generate export package in temp results dir
        export_dir = Path(tempfile.gettempdir()) / "lfmt_analysis_reports"
        artifacts = DefectReportGenerator.export_report_package(result, output_dir=export_dir)
        ARTIFACTS_CACHE[result.analysis_id] = artifacts

        res_dict = result.to_dict()
        res_dict["report_download_url"] = f"/api/v1/analyze/{result.analysis_id}/report"
        return JSONResponse(content=res_dict)

    finally:
        if tmp_path.exists():
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@router.post("/preset/{preset_id}", response_model=AnalysisResponseSchema)
async def analyze_preset_sample(
    preset_id: str,
    apply_baseline: bool = Query(True),
    smooth_sigma_px: float = Query(0.0)
):
    """
    Run analyzer on verified benchmark demonstration cases via ExampleRegistry.
    """
    from lfmt.examples.registry import ExampleRegistry
    registry = ExampleRegistry()
    
    # Map legacy preset IDs to canonical example IDs
    preset_map = {
        "synthetic_lfmt_slag": "slag_shallow",
        "slag_shallow": "slag_shallow",
        "slag_deep": "slag_deep",
        "multi_slag": "multi_slag",
        "healthy_plate": "healthy_lfmt",
        "healthy_lfmt": "healthy_lfmt",
        "single_thermal_frame": "single_thermal_frame",
        "polyu_pulsed_fbh": "measured_polyu_preview",
        "measured_polyu_preview": "measured_polyu_preview"
    }
    
    target_id = preset_map.get(preset_id)
    if not target_id:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preset ID '{preset_id}'. Valid options: {list(preset_map.keys())}"
        )

    try:
        loaded = registry.load(target_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Integrity error: {e}")

    if not loaded.is_installed:
        raise HTTPException(
            status_code=404,
            detail=f"External dataset for '{preset_id}' is not installed locally. Run 'python scripts/prepare_external_polyu_dataset.py'."
        )

    result = ANALYZER_INSTANCE.analyze(
        source=loaded.data,
        metadata_override=loaded.metadata,
        apply_baseline=apply_baseline,
        smooth_sigma_px=smooth_sigma_px
    )

    ANALYSIS_CACHE[result.analysis_id] = result
    export_dir = Path(tempfile.gettempdir()) / "lfmt_analysis_reports"
    artifacts = DefectReportGenerator.export_report_package(result, output_dir=export_dir)
    ARTIFACTS_CACHE[result.analysis_id] = artifacts

    res_dict = result.to_dict()
    res_dict["report_download_url"] = f"/api/v1/analyze/{result.analysis_id}/report"
    return JSONResponse(content=res_dict)


@router.get("/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Retrieve full analysis result by analysis_id."""
    if analysis_id not in ANALYSIS_CACHE:
        raise HTTPException(status_code=404, detail=f"Analysis ID '{analysis_id}' not found.")
    return JSONResponse(content=ANALYSIS_CACHE[analysis_id].to_dict())


@router.get("/{analysis_id}/report")
async def download_analysis_report(analysis_id: str):
    """Download full JSON report artifact for analysis_id."""
    if analysis_id not in ARTIFACTS_CACHE or "json_report" not in ARTIFACTS_CACHE[analysis_id]:
        raise HTTPException(status_code=404, detail="Report artifact not generated for this analysis ID.")
    json_path = ARTIFACTS_CACHE[analysis_id]["json_report"]
    return FileResponse(json_path, filename=f"lfmt_report_{analysis_id}.json", media_type="application/json")


@router.get("/{analysis_id}/figure")
async def download_analysis_figure(analysis_id: str):
    """Download diagnostic panel figure for analysis_id."""
    if analysis_id not in ARTIFACTS_CACHE or "diagnostic_figure" not in ARTIFACTS_CACHE[analysis_id]:
        raise HTTPException(status_code=404, detail="Diagnostic figure not found.")
    fig_path = ARTIFACTS_CACHE[analysis_id]["diagnostic_figure"]
    return FileResponse(fig_path, filename=f"lfmt_diagnostic_{analysis_id}.png", media_type="image/png")
