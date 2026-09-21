"""
Automated Thermographic Defect Report & Manifest Generator.

Exports analysis results into:
- Structured JSON report
- Tabular CSV defect summaries
- Reproducibility audit manifests
- Multi-panel publication-grade 300 DPI diagnostic figures
"""

from __future__ import annotations
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lfmt.analysis.analyzer import AnalysisResult


class DefectReportGenerator:
    """Generates diagnostic reports, manifests, and visualization figures."""

    @staticmethod
    def export_report_package(
        result: AnalysisResult,
        output_dir: str | Path,
        raw_cube: Optional[np.ndarray] = None
    ) -> Dict[str, str]:
        """
        Generate complete export package for an AnalysisResult.
        """
        out_p = Path(output_dir) / result.analysis_id
        out_p.mkdir(parents=True, exist_ok=True)
        artifacts: Dict[str, str] = {}

        # 1. Save Full JSON Report
        json_path = out_p / "report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
        artifacts["json_report"] = str(json_path)

        # 2. Save Tabular CSV Defect Summary
        csv_path = out_p / "defects_summary.csv"
        headers = ["defect_id", "defect_type", "confidence", "centroid_x_px", "centroid_y_px", "area_px", "diameter_mm", "depth_mm"]
        lines = [",".join(headers)]
        for d in result.defects:
            c_px = d.get("centroid_px", [0, 0])
            row = [
                d.get("defect_id", ""),
                d.get("defect_type", ""),
                str(d.get("confidence_score", 0.0)),
                str(c_px[0]),
                str(c_px[1]),
                str(d.get("area_px", 0)),
                str(d.get("equivalent_diameter_mm", "")),
                str(d.get("depth_estimate_mm", ""))
            ]
            lines.append(",".join(row))
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        artifacts["csv_summary"] = str(csv_path)

        # 3. Save Reproducibility Manifest
        manifest_path = out_p / "analysis_manifest.json"
        manifest_data = {
            "analysis_id": result.analysis_id,
            "timestamp_utc": result.timestamp_utc,
            "runtime_seconds": result.runtime_seconds,
            "software_version": "research-v3.0",
            "quality_status": result.quality_status,
            "warnings_count": len(result.warnings),
            "total_defects_found": result.total_defects_found,
            "likely_defect_type": result.consensus_verdict.get("likely_defect_type", "UNKNOWN"),
            "consensus_confidence": result.consensus_verdict.get("consensus_confidence", 0.0),
            "ood_status": result.ood_summary.get("status", "UNKNOWN")
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        artifacts["manifest"] = str(manifest_path)

        # 4. Generate Multi-Panel Diagnostic Figure
        fig_path = out_p / "diagnostic_panel.png"
        fig, axs = plt.subplots(1, 3, figsize=(15, 4.5), dpi=200)

        # Panel 1: Primary Feature Map
        feat_map = result.primary_feature_map if result.primary_feature_map is not None else np.zeros((64, 64))
        im0 = axs[0].imshow(feat_map, cmap="inferno")
        axs[0].set_title(f"Primary Map: {result.primary_map_type}", fontsize=11, fontweight="bold")
        plt.colorbar(im0, ax=axs[0], fraction=0.046, pad=0.04)

        # Panel 2: Segmentation Mask & Centroid Overlay
        seg_mask = result.segmentation_mask if result.segmentation_mask is not None else np.zeros_like(feat_map)
        im1 = axs[1].imshow(seg_mask, cmap="viridis")
        for d in result.defects:
            c_px = d.get("centroid_px", [0, 0])
            axs[1].plot(c_px[0], c_px[1], "rx", markersize=10, markeredgewidth=2)
            axs[1].text(c_px[0] + 2, c_px[1] + 2, d.get("defect_id", ""), color="yellow", fontsize=9, fontweight="bold")
        axs[1].set_title(f"Segmented Candidates ({result.total_defects_found} isolated)", fontsize=11, fontweight="bold")
        plt.colorbar(im1, ax=axs[1], fraction=0.046, pad=0.04)

        # Panel 3: Consensus & Confidence Telemetry
        axs[2].axis("off")
        cv = result.consensus_verdict
        ood = result.ood_summary
        unc = result.uncertainty_summary

        text_content = (
            f"DIAGNOSTIC REPORT SUMMARY\n"
            f"-----------------------------------------\n"
            f"Verdict: {cv.get('likely_defect_type', 'UNKNOWN')}\n"
            f"Confidence: {cv.get('consensus_confidence', 0.0) * 100:.1f}%\n"
            f"Method Agreement: {cv.get('agreement_level', 'N/A')} ({cv.get('method_agreement_ratio', 0.0) * 100:.0f}%)\n"
            f"OOD Status: {ood.get('status', 'N/A')}\n"
            f"Uncertainty: {unc.get('status_label', 'N/A')} (var={unc.get('predictive_variance', 0.0):.3f})\n\n"
            f"RECOMMENDATION:\n{cv.get('final_recommendation', 'N/A')}\n"
        )
        axs[2].text(0.05, 0.95, text_content, transform=axs[2].transAxes, fontsize=9.5, verticalalignment="top", fontfamily="monospace", bbox=dict(boxstyle="round,pad=0.5", facecolor="#f4f4f5", edgecolor="#d4d4d8"))

        plt.tight_layout()
        fig.savefig(fig_path)
        plt.close(fig)
        artifacts["diagnostic_figure"] = str(fig_path)

        return artifacts
