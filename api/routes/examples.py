# FastAPI Routes for Discovering and Running Verified Example Thermographic Datasets
from __future__ import annotations
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from lfmt.examples.registry import ExampleRegistry
from api.routes.analyze import ANALYSIS_CACHE, ANALYZER_INSTANCE
from api.schemas.analysis import AnalysisResponseSchema

router = APIRouter(prefix="/examples", tags=["Verified Example Library"])
REGISTRY = ExampleRegistry()


@router.get("", response_model=List[Dict[str, Any]])
async def list_verified_examples():
    """
    List all verified thermographic reference examples in the library.
    """
    examples = REGISTRY.list_examples()
    return examples


@router.get("/{example_id}", response_model=Dict[str, Any])
async def get_example_metadata(example_id: str):
    """
    Get detailed scientific metadata, ground truth, expected results, and integrity for a specific example.
    """
    meta = REGISTRY.get_example_metadata(example_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Example '{example_id}' not found in registry.")

    integrity_info = REGISTRY.verify_example(example_id)
    expected = REGISTRY.get_expected_result(example_id)
    gt = REGISTRY.get_ground_truth(example_id)

    return {
        "id": example_id,
        "example_id": example_id,
        "title": meta.get("title", example_id),
        "category": meta.get("category", "Category A: Numerical 3D FEM"),
        "metadata": meta,
        "expected_result": expected,
        "ground_truth": gt,
        "integrity": integrity_info
    }


@router.post("/{example_id}/analyze", response_model=AnalysisResponseSchema)
async def analyze_verified_example(
    example_id: str,
    apply_baseline: bool = Query(True),
    smooth_sigma_px: float = Query(0.0)
):
    """
    Execute autonomous end-to-end defect analysis on a verified reference sample.
    The example data is cryptographically verified and run through the SAME AutoDefectAnalyzer
    pipeline as uploaded data.
    """
    meta = REGISTRY.get_example_metadata(example_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Example '{example_id}' not found in registry.")

    try:
        loaded = REGISTRY.load(example_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Integrity check failed: {e}")

    # Handle external measured datasets if not downloaded
    if not loaded.is_installed:
        return JSONResponse(
            status_code=200,
            content={
                "status": "EXTERNAL_DATA_NOT_INSTALLED",
                "example_id": example_id,
                "title": loaded.title,
                "category": loaded.category,
                "source": "PolyU Research Data Repository",
                "doi": "10.60933/PRDR/HJYNZB",
                "preparation_command": "python scripts/prepare_external_polyu_dataset.py",
                "message": (
                    "External measured laboratory dataset is not currently downloaded on this server. "
                    "Run 'python scripts/prepare_external_polyu_dataset.py' to ingest the raw thermography sequence."
                ),
                "setup_instructions": "Execute: python scripts/prepare_external_polyu_dataset.py",
                "source_doi": "10.60933/PRDR/HJYNZB"
            }
        )

    # Run through the identical AutoDefectAnalyzer pipeline
    result = ANALYZER_INSTANCE.analyze(
        source=loaded.data,
        metadata_override=loaded.metadata,
        apply_baseline=apply_baseline,
        smooth_sigma_px=smooth_sigma_px
    )

    ANALYSIS_CACHE[result.analysis_id] = result
    res_dict = result.to_dict()
    res_dict["status"] = "SUCCESS"
    res_dict["report_url"] = f"/api/v1/analyze/{result.analysis_id}/report"
    res_dict["diagnostic_figure_url"] = f"/api/v1/analyze/{result.analysis_id}/figure"

    return JSONResponse(content=res_dict)
