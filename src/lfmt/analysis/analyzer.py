"""
Intelligent Thermographic Defect Analyzer Master Pipeline.

Executes autonomous end-to-end scientific analysis on arbitrary thermal data:
Input Inspection -> Physical Validation -> Method Selection -> Preprocessing ->
Scientific Processing -> Feature Extraction -> AI Multi-Task Inference ->
Uncertainty & OOD Estimation -> Consensus Fusion -> Structured Diagnostic Report.
"""

from __future__ import annotations
import uuid
import time
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import numpy as np

# IO & Inspection
from lfmt.io.input_analyzer import UniversalInputAnalyzer, InputInspectionResult, InputType, QualityStatus, DataRepresentation

# Analysis & Applicability
from lfmt.analysis.method_selector import MethodApplicabilityEngine, ApplicabilityMatrix, MethodStatus
from lfmt.analysis.preprocessing import UniversalPreprocessor, PreprocessingManifest
from lfmt.analysis.physics_features import PhysicsFeatureEngine, PhysicsFeatures, SpatioTemporalFeatures
from lfmt.analysis.single_frame import SingleFrameSpatialAnalyzer, SingleFrameSpatialResult

from lfmt.excitation import LFMTExcitation
from lfmt.contrast import RawThermalContrast, RawContrastResult
from lfmt.pulse_compression import LFMTMatchedFilter, PulseCompressionResult
from lfmt.pct import PrincipalComponentThermography, PCTResult
from lfmt.spct import SparsePrincipalComponentThermography, SPCTResult
from lfmt.rpt import RandomProjectionTechnique, RPTResult
from lfmt.detection import MultiDefectDetector, MultiDetectionResult, DefectCandidate

# Machine Learning & AI
from ml.models.classical import ClassicalMLDefectEngine, MLPredictionResult
from ml.models.multitask import MultiTaskInferenceEngine, MultiTaskPrediction
from ml.uncertainty.dropout import MCDropoutUncertaintyEstimator, UncertaintyEstimate
from ml.ood.detector import OODDetector, OODResult
from ml.fusion.consensus import MultiMethodConsensusEngine, ConsensusVerdict


@dataclass
class DefectInstance:
    """Individual isolated defect characterized by the analyzer."""
    defect_id: str
    defect_type: str
    confidence_score: float
    centroid_px: Tuple[float, float]
    centroid_mm: Optional[Tuple[float, float]]
    bounding_box_px: Tuple[int, int, int, int]
    area_px: int
    area_mm2: Optional[float]
    equivalent_diameter_mm: Optional[float]
    depth_estimate_mm: Optional[float]
    uncertainty_depth_range_mm: Optional[Tuple[float, float]]
    evidence_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "defect_id": self.defect_id,
            "defect_type": self.defect_type,
            "confidence_score": round(self.confidence_score, 4),
            "centroid_px": [round(self.centroid_px[0], 2), round(self.centroid_px[1], 2)],
            "centroid_mm": [round(self.centroid_mm[0], 2), round(self.centroid_mm[1], 2)] if self.centroid_mm else None,
            "bounding_box_px": list(self.bounding_box_px),
            "area_px": self.area_px,
            "area_mm2": round(self.area_mm2, 2) if self.area_mm2 is not None else None,
            "equivalent_diameter_mm": round(self.equivalent_diameter_mm, 2) if self.equivalent_diameter_mm is not None else None,
            "depth_estimate_mm": round(self.depth_estimate_mm, 2) if self.depth_estimate_mm is not None else None,
            "uncertainty_depth_range_mm": (
                [round(self.uncertainty_depth_range_mm[0], 2), round(self.uncertainty_depth_range_mm[1], 2)]
                if self.uncertainty_depth_range_mm else None
            ),
            "evidence_notes": self.evidence_notes
        }


@dataclass
class AnalysisResult:
    """Master output contract of the Intelligent Thermographic Defect Analyzer."""
    analysis_id: str
    timestamp_utc: str
    input_summary: Dict[str, Any]
    quality_status: str
    warnings: List[str]
    applicability_matrix: Dict[str, Any]
    preprocessing_manifest: Dict[str, Any]
    physics_summary: Dict[str, Any]
    processing_results_summary: Dict[str, Any]
    ai_prediction_summary: Dict[str, Any]
    uncertainty_summary: Dict[str, Any]
    ood_summary: Dict[str, Any]
    consensus_verdict: Dict[str, Any]
    defects: List[Dict[str, Any]]
    total_defects_found: int
    primary_map_type: str
    primary_feature_map: Optional[np.ndarray] = None
    segmentation_mask: Optional[np.ndarray] = None
    runtime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "timestamp_utc": self.timestamp_utc,
            "input_summary": self.input_summary,
            "quality_status": self.quality_status,
            "warnings": self.warnings,
            "applicability_matrix": self.applicability_matrix,
            "preprocessing_manifest": self.preprocessing_manifest,
            "physics_summary": self.physics_summary,
            "processing_results_summary": self.processing_results_summary,
            "ai_prediction_summary": self.ai_prediction_summary,
            "uncertainty_summary": self.uncertainty_summary,
            "ood_summary": self.ood_summary,
            "consensus_verdict": self.consensus_verdict,
            "defects": self.defects,
            "total_defects_found": self.total_defects_found,
            "primary_map_type": self.primary_map_type,
            "runtime_seconds": round(self.runtime_seconds, 4)
        }


class AutoDefectAnalyzer:
    """End-to-End Autonomous Thermographic Defect Analysis Pipeline."""

    def __init__(self):
        self.ml_engine = ClassicalMLDefectEngine(random_state=42)
        self.multitask_engine = MultiTaskInferenceEngine(in_channels=1)
        self.uncertainty_engine = MCDropoutUncertaintyEstimator(n_passes=10)

    def analyze(
        self,
        source: Union[str, Path, np.ndarray, Dict[str, Any]],
        metadata_override: Optional[Dict[str, Any]] = None,
        apply_baseline: bool = True,
        smooth_sigma_px: float = 0.0
    ) -> AnalysisResult:
        """
        Execute full autonomous scientific analysis pipeline.
        """
        t_start = time.perf_counter()
        analysis_id = str(uuid.uuid4())[:12]
        utc_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 1. Input Inspection
        inspection = UniversalInputAnalyzer.inspect(source, metadata_override=metadata_override)

        # 2. Method Applicability
        applicability = MethodApplicabilityEngine.evaluate(inspection)

        # 3. Preprocessing
        cube_raw = inspection.loaded_cube_k
        t_vec_raw = inspection.time_vector

        cube_proc, t_vec_proc, prep_manifest = UniversalPreprocessor.preprocess(
            cube_raw,
            time_vector=t_vec_raw,
            apply_baseline_subtraction=apply_baseline,
            smooth_sigma_px=smooth_sigma_px
        )

        N_frames, H, W = cube_proc.shape
        fov = inspection.fov_mm or (100.0, 70.0)

        # 4. Execute Applicable Signal Processing Algorithms
        processing_outputs: Dict[str, Any] = {}
        primary_map = np.zeros((H, W), dtype=float)
        primary_map_name = "none"

        # A. Raw Contrast
        max_contrast_k = 0.0
        if applicability.is_method_enabled("raw_contrast"):
            try:
                raw_eng = RawThermalContrast(mode="blind")
                raw_res = raw_eng.process(cube_proc, t_vec_proc)
                max_contrast_k = float(raw_res.max_contrast_val)
                is_raw_det = bool(max_contrast_k >= 0.15)
                processing_outputs["raw_contrast"] = {
                    "is_detected": is_raw_det,
                    "max_contrast_val": round(max_contrast_k, 4),
                    "t_max_contrast_s": round(float(raw_res.t_max_contrast_s), 3),
                    "frame_max_contrast": int(raw_res.frame_max_contrast),
                    "runtime_s": round(raw_res.runtime_seconds, 4)
                }
                primary_map = raw_res.contrast_map
                primary_map_name = "Raw Contrast"
            except Exception as e:
                processing_outputs["raw_contrast"] = {"error": str(e)}

        # B. Matched Filter (LFMT Only)
        if applicability.is_method_enabled("lfmt_matched_filter"):
            try:
                exc_meta = inspection.excitation_metadata
                f0 = float(exc_meta.get("f0_hz", 0.05))
                f1 = float(exc_meta.get("f1_hz", 0.50))
                dur = float(exc_meta.get("duration_s", t_vec_proc[-1] - t_vec_proc[0]))
                fps = float(inspection.frame_rate_hz or (len(t_vec_proc) / max(0.1, dur)))
                fps = max(fps, f1 * 2.5)

                lfmt_cfg = LFMTExcitation(f0_hz=f0, f1_hz=f1, duration_s=dur, sampling_rate_hz=fps)
                mf_eng = LFMTMatchedFilter(excitation=lfmt_cfg)
                mf_res = mf_eng.process(cube_proc, t_vec_proc)
                
                peak_amp = float(np.max(mf_res.peak_correlation_map))
                bg_amp = float(np.median(mf_res.peak_correlation_map))
                mf_z = (peak_amp - bg_amp) / (float(np.std(mf_res.peak_correlation_map)) + 1e-6)
                # Anomaly requires both significant amplitude and spatial prominence above noise floor
                is_mf_det = bool(peak_amp >= 0.25 and mf_z >= 2.5)

                processing_outputs["lfmt_matched_filter"] = {
                    "is_detected": is_mf_det,
                    "snr_db": round(float(mf_z), 2),
                    "peak_amplitude": round(peak_amp, 4),
                    "runtime_s": round(mf_res.runtime_seconds, 4)
                }
                primary_map = mf_res.peak_correlation_map
                primary_map_name = "LFMT Matched Filter"
            except Exception as e:
                processing_outputs["lfmt_matched_filter"] = {"error": str(e)}

        # C. PCT
        if applicability.is_method_enabled("pct"):
            try:
                pct_eng = PrincipalComponentThermography(n_components=min(6, N_frames), selection_criterion="blind_kurtosis", mode="blind")
                pct_res = pct_eng.process(cube_proc)
                eof_map = pct_res.selected_eof_image
                eof_z = float(np.max(np.abs(eof_map - np.median(eof_map)))) / (float(np.std(eof_map)) + 1e-6)
                is_pct_det = bool(eof_z >= 5.0 or (max_contrast_k >= 0.15 and eof_z >= 2.5))
                processing_outputs["pct"] = {
                    "is_detected": is_pct_det,
                    "selected_component_idx": int(pct_res.selected_component_idx),
                    "selection_method": pct_res.selection_method,
                    "kurtosis_score": round(eof_z, 2),
                    "explained_variance_ratio": [round(float(v), 4) for v in pct_res.explained_variance_ratio],
                    "runtime_s": round(pct_res.runtime_seconds, 4)
                }
                primary_map = pct_res.selected_eof_image
                primary_map_name = "PCT (Optimal EOF)"
            except Exception as e:
                processing_outputs["pct"] = {"error": str(e)}

        # D. SPCT
        if applicability.is_method_enabled("spct"):
            try:
                # Use downsampled grid for fast L1 solver
                sub_stride = 2 if H >= 120 else 1
                cube_spct = cube_proc[:, ::sub_stride, ::sub_stride] if sub_stride > 1 else cube_proc
                spct_eng = SparsePrincipalComponentThermography(n_components=min(4, N_frames), alpha=0.05, max_iter=20, mode="blind", use_minibatch=True)
                spct_res = spct_eng.process(cube_spct)
                seof = spct_res.selected_sparse_image
                seof_z = float(np.max(np.abs(seof - np.median(seof)))) / (float(np.std(seof)) + 1e-6)
                is_spct_det = bool(seof_z >= 5.0 or (max_contrast_k >= 0.15 and seof_z >= 2.5))
                processing_outputs["spct"] = {
                    "is_detected": is_spct_det,
                    "selected_component_idx": int(spct_res.selected_component_idx),
                    "non_zero_ratios": [round(float(v), 3) for v in spct_res.non_zero_ratios],
                    "runtime_s": round(spct_res.runtime_seconds, 4)
                }
            except Exception as e:
                processing_outputs["spct"] = {"error": str(e)}

        # E. RPT
        if applicability.is_method_enabled("rpt"):
            try:
                rpt_eng = RandomProjectionTechnique(n_components=min(4, N_frames), matrix_type="gaussian", mode="blind", random_state=42)
                rpt_res = rpt_eng.process(cube_proc)
                proj = rpt_res.selected_rpt_image
                proj_z = float(np.max(np.abs(proj - np.median(proj)))) / (float(np.std(proj)) + 1e-6)
                is_rpt_det = bool(proj_z >= 5.0 or (max_contrast_k >= 0.15 and proj_z >= 2.5))
                processing_outputs["rpt"] = {
                    "is_detected": is_rpt_det,
                    "selected_component_idx": int(rpt_res.selected_component_idx),
                    "compression_ratio": round(float(rpt_res.compression_ratio), 2),
                    "runtime_s": round(rpt_res.runtime_seconds, 4)
                }
            except Exception as e:
                processing_outputs["rpt"] = {"error": str(e)}

        # F. Single Frame Spatial (if 1 frame)
        if applicability.is_method_enabled("single_frame_spatial"):
            try:
                sf_eng = SingleFrameSpatialAnalyzer()
                sf_res = sf_eng.process(cube_proc[0], fov_mm=fov)
                processing_outputs["single_frame_spatial"] = {
                    "is_detected": sf_res.detection_result.is_detected,
                    "n_candidates": sf_res.detection_result.n_candidates,
                    "peak_anomaly_contrast": sf_res.peak_anomaly_contrast,
                    "runtime_s": sf_res.runtime_seconds
                }
                primary_map = sf_res.spatial_contrast_map
                primary_map_name = "Spatial Contrast"
            except Exception as e:
                processing_outputs["single_frame_spatial"] = {"error": str(e)}

        # 5. Physics & Spatio-Temporal Features
        physics_ctx = PhysicsFeatureEngine.compute_physics_context(
            material_name=inspection.raw_metadata.get("material", "mild_steel"),
            f0_hz=inspection.excitation_metadata.get("f0_hz", 0.05),
            f1_hz=inspection.excitation_metadata.get("f1_hz", 0.50)
        )
        st_features = PhysicsFeatureEngine.extract_spatiotemporal_features(cube_proc, t_vec_proc)

        # 6. AI Inference
        ml_pred: Optional[MLPredictionResult] = None
        multitask_pred: Optional[MultiTaskPrediction] = None

        if applicability.is_method_enabled("ai_multitask"):
            # A. Classical ML Tabular prediction
            ml_pred = self.ml_engine.predict(st_features.raw_feature_vector)

            # B. Deep Multi-Task Network prediction
            phys_vec = np.array([
                physics_ctx.thermal_diffusivity_m2_s * 1e5,
                physics_ctx.thermal_effusivity_w_s12_m2k / 10000.0,
                physics_ctx.f0_hz or 0.05,
                physics_ctx.f1_hz or 0.50,
                float(inspection.frame_rate_hz or 10.0),
                float(N_frames),
                st_features.peak_delta_t_k,
                st_features.time_to_peak_s
            ], dtype=float)

            multitask_pred = self.multitask_engine.predict(primary_map, physics_vec=phys_vec)

        # 7. Uncertainty & OOD Estimation
        ood_res = OODDetector.evaluate(
            inspection.__dict__,
            latent_embedding=multitask_pred.latent_embedding if multitask_pred else None
        )

        unc_res: Optional[UncertaintyEstimate] = None
        if multitask_pred is not None:
            unc_res = self.uncertainty_engine.estimate(
                self.multitask_engine.model,
                primary_map,
                physics_vec=phys_vec
            )

        # 8. Multi-Method Consensus Fusion
        consensus = MultiMethodConsensusEngine.fuse(
            method_results=processing_outputs,
            ml_prediction=ml_pred,
            multitask_prediction=multitask_pred,
            ood_status=ood_res.status.value
        )

        # 9. Defect Sizing & Characterization
        detector = MultiDefectDetector(threshold_method="adaptive_otsu", morphology_kernel_size=1, min_area_px=3, min_confidence=0.04)
        det_all = detector.detect_all(primary_map, fov_mm=fov)

        defect_instances: List[DefectInstance] = []
        if consensus.is_anomaly_detected:
            for i, cand in enumerate(det_all.candidates):
                d_id = f"DEFECT-{i+1:02d}"
                d_type = consensus.likely_defect_type
            
            # Sizing & Depth estimation
            diam_mm = cand.equivalent_diameter_mm if inspection.fov_mm else None
            area_mm2 = cand.area_mm2 if inspection.fov_mm else None
            
            depth_est = None
            unc_range = None
            if consensus.is_anomaly_detected and multitask_pred and multitask_pred.estimated_depth_mm:
                depth_est = multitask_pred.estimated_depth_mm
                unc_range = (max(0.1, depth_est - 0.25), depth_est + 0.35)

            notes = f"Centroid at px ({cand.centroid_px[0]:.1f}, {cand.centroid_px[1]:.1f}), area {cand.area_px} px."
            defect_instances.append(DefectInstance(
                defect_id=d_id,
                defect_type=d_type,
                confidence_score=cand.confidence_score,
                centroid_px=cand.centroid_px,
                centroid_mm=cand.centroid_mm if inspection.fov_mm else None,
                bounding_box_px=cand.bounding_box_px,
                area_px=cand.area_px,
                area_mm2=area_mm2,
                equivalent_diameter_mm=diam_mm,
                depth_estimate_mm=depth_est,
                uncertainty_depth_range_mm=unc_range,
                evidence_notes=notes
            ))

        elapsed_total = time.perf_counter() - t_start

        return AnalysisResult(
            analysis_id=analysis_id,
            timestamp_utc=utc_str,
            input_summary={
                "input_type": inspection.input_type.value,
                "data_representation": inspection.data_representation.value,
                "shape": list(inspection.shape),
                "n_frames": inspection.n_frames,
                "height_px": inspection.height,
                "width_px": inspection.width,
                "frame_rate_hz": inspection.frame_rate_hz,
                "duration_s": inspection.duration_s,
                "temperature_units": inspection.temperature_units,
                "is_radiometric": inspection.is_radiometric,
                "excitation_type": inspection.excitation_type,
                "fov_mm": list(inspection.fov_mm) if inspection.fov_mm else None
            },
            quality_status=inspection.quality_status.value,
            warnings=inspection.warnings,
            applicability_matrix=applicability.to_dict(),
            preprocessing_manifest=prep_manifest.to_dict(),
            physics_summary=physics_ctx.to_dict(),
            processing_results_summary=processing_outputs,
            ai_prediction_summary=(
                multitask_pred.to_dict() if multitask_pred else (ml_pred.to_dict() if ml_pred else {})
            ),
            uncertainty_summary=unc_res.to_dict() if unc_res else {},
            ood_summary=ood_res.to_dict(),
            consensus_verdict=consensus.to_dict(),
            defects=[d.to_dict() for d in defect_instances],
            total_defects_found=len(defect_instances),
            primary_map_type=primary_map_name,
            primary_feature_map=primary_map,
            segmentation_mask=det_all.combined_mask,
            runtime_seconds=round(elapsed_total, 4)
        )
