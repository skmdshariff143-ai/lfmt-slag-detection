"""
Pydantic Schemas for FastAPI Intelligent Thermographic Defect Analyzer.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class AnalysisRequestMetadata(BaseModel):
    """Optional user-supplied overrides and physical metadata."""
    temp_units: Optional[str] = Field(default=None, description="Explicit temperature units ('K', 'C')")
    frame_rate_hz: Optional[float] = Field(default=None, description="Camera acquisition frame rate in Hz")
    fov_mm: Optional[Tuple[float, float]] = Field(default=None, description="Field of View in millimeters [length, width]")
    material: Optional[str] = Field(default="mild_steel", description="Specimen base material name")
    excitation_type: Optional[str] = Field(default=None, description="Excitation type ('lfmt', 'pulsed', 'none')")
    f0_hz: Optional[float] = Field(default=None, description="LFMT start chirp frequency in Hz")
    f1_hz: Optional[float] = Field(default=None, description="LFMT end chirp frequency in Hz")
    apply_baseline: bool = Field(default=True, description="Subtract ambient pre-heating baseline")
    smooth_sigma_px: float = Field(default=0.0, description="Spatial Gaussian smoothing sigma in pixels")


class DefectItemSchema(BaseModel):
    defect_id: str
    defect_type: str
    confidence_score: float
    centroid_px: Tuple[float, float]
    centroid_mm: Optional[Tuple[float, float]] = None
    bounding_box_px: Tuple[int, int, int, int]
    area_px: int
    area_mm2: Optional[float] = None
    equivalent_diameter_mm: Optional[float] = None
    depth_estimate_mm: Optional[float] = None
    uncertainty_depth_range_mm: Optional[Tuple[float, float]] = None
    evidence_notes: str


class MethodEligibilitySchema(BaseModel):
    method_id: str
    display_name: str
    status: str
    is_applicable: bool
    reason: str
    scientific_principle: str
    expected_output: str


class AnalysisResponseSchema(BaseModel):
    analysis_id: str
    timestamp_utc: str
    quality_status: str
    warnings: List[str]
    input_summary: Dict[str, Any]
    applicability_matrix: Dict[str, Any]
    preprocessing_manifest: Dict[str, Any]
    physics_summary: Dict[str, Any]
    processing_results_summary: Dict[str, Any]
    consensus_verdict: Dict[str, Any]
    defects: List[DefectItemSchema]
    total_defects_found: int
    primary_map_type: str
    runtime_seconds: float
    report_download_url: Optional[str] = None
