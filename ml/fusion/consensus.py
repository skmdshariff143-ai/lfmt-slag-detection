"""
Multi-Method Consensus & Agreement Fusion Engine for Thermographic NDT.

Fuses evidence across:
1. Signal processing algorithms (Raw Contrast, Matched Filter, PCT, SPCT, RPT)
2. Spatial single-frame analysis
3. Classical Machine Learning
4. Physics-Informed Multi-Task Deep Learning
5. Physics diffusion constraints
to generate a weighted consensus decision, method agreement metrics, and structured explanations.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


@dataclass
class MethodEvidence:
    """Individual algorithm evidence contribution."""
    method_name: str
    detected_anomaly: bool
    confidence_score: float
    candidate_count: int
    peak_contrast_or_kurtosis: float
    weight: float
    notes: str


@dataclass
class ConsensusVerdict:
    """Unified multi-method fused diagnosis."""
    is_anomaly_detected: bool
    likely_defect_type: str
    consensus_confidence: float
    method_agreement_ratio: float  # e.g. 0.80 (4/5 agreed)
    agreement_level: str          # "STRONG_AGREEMENT", "MODERATE_AGREEMENT", "WEAK_AGREEMENT", "CONFLICTING"
    supporting_evidence: List[str]
    counter_evidence: List[str]
    per_method_contributions: Dict[str, Dict[str, Any]]
    final_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_anomaly_detected": self.is_anomaly_detected,
            "likely_defect_type": self.likely_defect_type,
            "consensus_confidence": round(self.consensus_confidence, 4),
            "method_agreement_ratio": round(self.method_agreement_ratio, 3),
            "agreement_level": self.agreement_level,
            "supporting_evidence": self.supporting_evidence,
            "counter_evidence": self.counter_evidence,
            "per_method_contributions": self.per_method_contributions,
            "final_recommendation": self.final_recommendation
        }


class MultiMethodConsensusEngine:
    """Rule + AI Hybrid Multi-Method Agreement and Fusion Processor."""

    DEFAULT_WEIGHTS = {
        "lfmt_matched_filter": 0.30,
        "pct": 0.20,
        "spct": 0.15,
        "rpt": 0.10,
        "raw_contrast": 0.10,
        "ai_multitask": 0.25,
        "classical_ml": 0.15,
        "single_frame_spatial": 0.20
    }

    @staticmethod
    def fuse(
        method_results: Dict[str, Any],
        ml_prediction: Optional[Any] = None,
        multitask_prediction: Optional[Any] = None,
        ood_status: str = "IN_DISTRIBUTION"
    ) -> ConsensusVerdict:
        """
        Synthesize cross-method evidence into a unified verdict.
        """
        evidence_list: List[MethodEvidence] = []
        support: List[str] = []
        counter: List[str] = []
        contributions: Dict[str, Dict[str, Any]] = {}

        # 1. Evaluate Signal Processing & Spatial Methods
        # A. Raw Contrast
        if "raw_contrast" in method_results:
            raw_res = method_results["raw_contrast"]
            det = raw_res.get("is_detected", False)
            conf = float(raw_res.get("max_contrast_val", 0.0) > 0.2) * 0.7 + 0.2
            evidence_list.append(MethodEvidence(
                method_name="Raw Contrast",
                detected_anomaly=det,
                confidence_score=min(1.0, conf),
                candidate_count=1 if det else 0,
                peak_contrast_or_kurtosis=raw_res.get("max_contrast_val", 0.0),
                weight=MultiMethodConsensusEngine.DEFAULT_WEIGHTS["raw_contrast"],
                notes="Peak differential thermal contrast observed."
            ))

        # B. Matched Filter
        if "lfmt_matched_filter" in method_results:
            mf_res = method_results["lfmt_matched_filter"]
            det = mf_res.get("is_detected", False)
            snr = float(mf_res.get("snr_db", 20.0))
            conf = 0.90 if det else 0.20
            evidence_list.append(MethodEvidence(
                method_name="LFMT Matched Filter",
                detected_anomaly=det,
                confidence_score=conf,
                candidate_count=1 if det else 0,
                peak_contrast_or_kurtosis=snr,
                weight=MultiMethodConsensusEngine.DEFAULT_WEIGHTS["lfmt_matched_filter"],
                notes="Phase-delay chirp correlation response."
            ))

        # C. PCT
        if "pct" in method_results:
            pct_res = method_results["pct"]
            det = pct_res.get("is_detected", False)
            kurt = float(pct_res.get("kurtosis_score", 1.5))
            conf = min(1.0, 0.4 + kurt * 0.15) if det else 0.25
            evidence_list.append(MethodEvidence(
                method_name="PCT (Empirical Modes)",
                detected_anomaly=det,
                confidence_score=conf,
                candidate_count=1 if det else 0,
                peak_contrast_or_kurtosis=kurt,
                weight=MultiMethodConsensusEngine.DEFAULT_WEIGHTS["pct"],
                notes=f"Selected EOF mode #{pct_res.get('selected_component_idx', 0)} via excess kurtosis."
            ))

        # D. SPCT
        if "spct" in method_results:
            spct_res = method_results["spct"]
            det = spct_res.get("is_detected", False)
            conf = 0.75 if det else 0.30
            evidence_list.append(MethodEvidence(
                method_name="Sparse PCT",
                detected_anomaly=det,
                confidence_score=conf,
                candidate_count=1 if det else 0,
                peak_contrast_or_kurtosis=spct_res.get("selected_component_idx", 0),
                weight=MultiMethodConsensusEngine.DEFAULT_WEIGHTS["spct"],
                notes="L1 sparse matrix spatial isolation."
            ))

        # E. RPT
        if "rpt" in method_results:
            rpt_res = method_results["rpt"]
            det = rpt_res.get("is_detected", False)
            conf = 0.65 if det else 0.30
            evidence_list.append(MethodEvidence(
                method_name="Random Projection (RPT)",
                detected_anomaly=det,
                confidence_score=conf,
                candidate_count=1 if det else 0,
                peak_contrast_or_kurtosis=0.0,
                weight=MultiMethodConsensusEngine.DEFAULT_WEIGHTS["rpt"],
                notes="Johnson-Lindenstrauss random subspace embedding."
            ))

        # If single frame analysis is active, increase its relative importance
        if "single_frame_spatial" in method_results and len(method_results) == 1:
            MultiMethodConsensusEngine_sf_weight = 0.70
        else:
            MultiMethodConsensusEngine_sf_weight = MultiMethodConsensusEngine.DEFAULT_WEIGHTS["single_frame_spatial"]

        # F. Single Frame Spatial
        if "single_frame_spatial" in method_results:
            sf_res = method_results["single_frame_spatial"]
            det = sf_res.get("is_detected", False)
            conf = 0.85 if det else 0.20
            evidence_list.append(MethodEvidence(
                method_name="Spatial Gradient & Morphology",
                detected_anomaly=det,
                confidence_score=conf,
                candidate_count=sf_res.get("n_candidates", 0),
                peak_contrast_or_kurtosis=sf_res.get("peak_anomaly_contrast", 0.0),
                weight=MultiMethodConsensusEngine_sf_weight,
                notes="2D local contrast and Otsu thresholding."
            ))

        # 2. Integrate AI Models
        ai_defect_type = "UNKNOWN_DEFECT"
        ai_anomaly_prob = 0.0

        if multitask_prediction is not None:
            ai_defect_type = multitask_prediction.defect_type
            ai_anomaly_prob = multitask_prediction.anomaly_probability
            is_ai_det = (ai_defect_type != "HEALTHY" and ai_anomaly_prob >= 0.40)
            evidence_list.append(MethodEvidence(
                method_name="Physics Multi-Task AI",
                detected_anomaly=is_ai_det,
                confidence_score=multitask_prediction.confidence_score,
                candidate_count=1 if is_ai_det else 0,
                peak_contrast_or_kurtosis=ai_anomaly_prob,
                weight=MultiMethodConsensusEngine.DEFAULT_WEIGHTS["ai_multitask"],
                notes=f"Predicted class '{ai_defect_type}' with P = {multitask_prediction.confidence_score:.2f}."
            ))

        if ml_prediction is not None:
            is_ml_det = ml_prediction.is_anomaly
            evidence_list.append(MethodEvidence(
                method_name="Classical ML Baseline",
                detected_anomaly=is_ml_det,
                confidence_score=ml_prediction.confidence_score,
                candidate_count=1 if is_ml_det else 0,
                peak_contrast_or_kurtosis=ml_prediction.anomaly_probability,
                weight=MultiMethodConsensusEngine.DEFAULT_WEIGHTS["classical_ml"],
                notes=f"Tabular ensemble predicted '{ml_prediction.defect_type}'."
            ))

        # 3. Compute Weighted Consensus & Agreement Ratio
        if not evidence_list:
            return ConsensusVerdict(
                is_anomaly_detected=False,
                likely_defect_type="HEALTHY",
                consensus_confidence=0.50,
                method_agreement_ratio=1.0,
                agreement_level="MODERATE_AGREEMENT",
                supporting_evidence=["No active methods found."],
                counter_evidence=[],
                per_method_contributions={},
                final_recommendation="Insufficient processing evidence available."
            )

        total_weight = sum(e.weight for e in evidence_list)
        pos_weight = sum(e.weight * (1.0 if e.detected_anomaly else 0.0) for e in evidence_list)
        fused_score = pos_weight / max(1e-6, total_weight)

        n_agree = sum(1 for e in evidence_list if e.detected_anomaly == (fused_score >= 0.50))
        agreement_ratio = n_agree / float(len(evidence_list))

        for e in evidence_list:
            contributions[e.method_name] = {
                "detected": e.detected_anomaly,
                "confidence": round(e.confidence_score, 3),
                "weight": round(e.weight, 3),
                "notes": e.notes
            }
            if e.detected_anomaly:
                support.append(f"{e.method_name}: {e.notes}")
            else:
                counter.append(f"{e.method_name}: No significant thermal anomaly isolated.")

        # Agreement level
        if agreement_ratio >= 0.80:
            agr_level = "STRONG_AGREEMENT"
        elif agreement_ratio >= 0.60:
            agr_level = "MODERATE_AGREEMENT"
        elif agreement_ratio >= 0.40:
            agr_level = "WEAK_AGREEMENT"
        else:
            agr_level = "CONFLICTING"

        # Final Defect Type Determination (Strict Anomaly vs Specific Classification Separation)
        is_detected = (fused_score >= 0.45)
        if not is_detected:
            final_type = "HEALTHY"
            rec = "Specimen exhibits healthy homogeneous thermal behavior. No defect action required."
        else:
            is_ai_validated = getattr(multitask_prediction, "is_validated", False)
            if ood_status == "OUT_OF_DISTRIBUTION":
                final_type = "GENERIC_SUBSURFACE_THERMAL_ANOMALY"
                rec = "Thermal anomaly detected, but sample lies outside validated AI domain. Classify as Generic Subsurface Thermal Anomaly."
            elif is_ai_validated and ai_defect_type not in ("HEALTHY", "UNKNOWN_DEFECT", "NOT_AVAILABLE"):
                final_type = ai_defect_type
                rec = f"Consensus supports '{final_type}' signature across thermal processing and validated AI."
            else:
                # LFMT Matched Filter establishes an anomaly, NOT metallurgical defect identity without a validated classifier
                final_type = "GENERIC_SUBSURFACE_THERMAL_ANOMALY"
                rec = "Consensus confirms subsurface thermal anomaly detection. Specific defect classification is unavailable without a validated classifier."

        return ConsensusVerdict(
            is_anomaly_detected=is_detected,
            likely_defect_type=final_type,
            consensus_confidence=round(float(fused_score), 4),
            method_agreement_ratio=round(agreement_ratio, 3),
            agreement_level=agr_level,
            supporting_evidence=support,
            counter_evidence=counter,
            per_method_contributions=contributions,
            final_recommendation=rec
        )

