"""
Out-Of-Distribution (OOD) Domain Verification Module.

Quantifies whether an uploaded thermogram or feature vector lies inside
the validated training/simulation distribution or represents an out-of-domain sample.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class OODStatus(str, Enum):
    IN_DISTRIBUTION = "IN_DISTRIBUTION"
    CAUTION = "CAUTION"
    OUT_OF_DISTRIBUTION = "OUT_OF_DISTRIBUTION"


@dataclass
class OODResult:
    """Out-of-distribution evaluation result."""
    status: OODStatus
    ood_score: float          # 0.0 (in-distribution) to 1.0 (highly anomalous)
    is_reliable: bool
    reasons: List[str]
    suggested_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "ood_score": round(self.ood_score, 4),
            "is_reliable": self.is_reliable,
            "reasons": self.reasons,
            "suggested_action": self.suggested_action
        }


class OODDetector:
    """Multi-criterion domain validity checker."""

    # Validated simulation domain boundaries
    VALID_BOUNDS = {
        "min_temp_k": (270.0, 320.0),
        "max_temp_k": (290.0, 450.0),
        "min_frames": 1,
        "max_frames": 2000,
        "min_fps": 1.0,
        "max_fps": 200.0,
        "min_duration_s": 0.5,
        "max_duration_s": 60.0
    }

    @staticmethod
    def evaluate(
        inspection_dict: Dict[str, Any],
        latent_embedding: Optional[np.ndarray] = None
    ) -> OODResult:
        """
        Evaluate domain compliance.
        """
        reasons: List[str] = []
        penalties = 0.0

        # 1. Representation & Visual Check
        rep = inspection_dict.get("data_representation", "")
        if "VISIBLE" in rep or "RGB" in rep:
            return OODResult(
                status=OODStatus.OUT_OF_DISTRIBUTION,
                ood_score=0.98,
                is_reliable=False,
                reasons=["Input is a visual photograph, not a calibrated infrared thermogram."],
                suggested_action="Thermographic subsurface characterization is not scientifically valid on visual RGB photos."
            )

        # 2. Temperature range sanity
        min_T = inspection_dict.get("min_val", 293.0)
        max_T = inspection_dict.get("max_val", 300.0)
        is_rad = inspection_dict.get("is_radiometric", True)

        if not is_rad:
            penalties += 0.35
            reasons.append("Input data lack thermodynamic Kelvin calibration.")

        if min_T < OODDetector.VALID_BOUNDS["min_temp_k"][0] or max_T > OODDetector.VALID_BOUNDS["max_temp_k"][1]:
            penalties += 0.40
            reasons.append(f"Temperature bounds [{min_T:.1f}, {max_T:.1f}] K deviate from the validated NDT training domain.")

        # 3. Sequence duration & frame rate
        n_frames = inspection_dict.get("n_frames", 1)
        dur = inspection_dict.get("duration_s", 10.0)
        fps = inspection_dict.get("frame_rate_hz", 10.0)

        if n_frames > 1:
            if dur and (dur < 0.5 or dur > 60.0):
                penalties += 0.25
                reasons.append(f"Sequence duration ({dur:.1f} s) is outside the typical [0.5, 60] s domain.")

        # 4. Latent embedding distance (energy score heuristic)
        if latent_embedding is not None:
            norm = float(np.linalg.norm(latent_embedding))
            if norm > 25.0:
                penalties += 0.30
                reasons.append("Latent neural feature representation exhibits high outlier distance from training centroid.")

        # Final score
        ood_score = float(min(1.0, penalties))

        if ood_score < 0.25:
            status = OODStatus.IN_DISTRIBUTION
            reliable = True
            action = "Input is within the validated domain. Predictions are reliable."
        elif ood_score < 0.60:
            status = OODStatus.CAUTION
            reliable = True
            action = "Input exhibits moderate domain shift. Interpret classifications with caution."
        else:
            status = OODStatus.OUT_OF_DISTRIBUTION
            reliable = False
            action = "Input is outside the validated domain. Defect classification is unreliable."

        if not reasons:
            reasons.append("Input matches the validated mild steel thermographic inspection domain.")

        return OODResult(
            status=status,
            ood_score=round(ood_score, 4),
            is_reliable=reliable,
            reasons=reasons,
            suggested_action=action
        )
