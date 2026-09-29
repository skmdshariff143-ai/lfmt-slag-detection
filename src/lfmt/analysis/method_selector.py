"""
Scientific Method Applicability & Compatibility Engine.

Determines which thermographic signal processing, spatial, temporal, and AI algorithms
are scientifically valid for a given input, preventing unphysical or uncalibrated execution.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List
from lfmt.io.input_analyzer import InputInspectionResult, InputType, DataRepresentation


class MethodStatus(str, Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INSUFFICIENT_METADATA = "INSUFFICIENT_METADATA"


@dataclass
class MethodEligibility:
    """Scientific compatibility assessment for an individual algorithm."""
    method_id: str
    display_name: str
    status: MethodStatus
    is_applicable: bool
    reason: str
    required_inputs: List[str]
    scientific_principle: str
    expected_output: str


@dataclass
class ApplicabilityMatrix:
    """Complete collection of method eligibility assessments for a sample."""
    methods: Dict[str, MethodEligibility] = field(default_factory=dict)
    applicable_count: int = 0
    total_count: int = 0
    primary_workflow: str = "thermal_sequence"

    def is_method_enabled(self, method_id: str) -> bool:
        return self.methods.get(method_id, None) is not None and self.methods[method_id].is_applicable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applicable_count": self.applicable_count,
            "total_count": self.total_count,
            "primary_workflow": self.primary_workflow,
            "methods": {
                k: {
                    "method_id": v.method_id,
                    "display_name": v.display_name,
                    "status": v.status.value,
                    "is_applicable": v.is_applicable,
                    "reason": v.reason,
                    "required_inputs": v.required_inputs,
                    "scientific_principle": v.scientific_principle,
                    "expected_output": v.expected_output
                }
                for k, v in self.methods.items()
            }
        }


class MethodApplicabilityEngine:
    """Evaluates input characteristics against strict scientific constraints."""

    @staticmethod
    def evaluate(inspection: InputInspectionResult) -> ApplicabilityMatrix:
        matrix: Dict[str, MethodEligibility] = {}
        n_frames = inspection.n_frames
        is_seq = n_frames >= 2
        _is_rich_seq = n_frames >= 5
        is_visible = (inspection.input_type == InputType.VISIBLE_IMAGE or inspection.data_representation == DataRepresentation.VISIBLE_RGB)
        exc_type = inspection.excitation_type.lower()
        has_lfmt_meta = (exc_type == "lfmt" or "f0_hz" in inspection.excitation_metadata or "f0" in inspection.raw_metadata)
        is_radiometric = inspection.is_radiometric

        # 1. Raw Contrast
        if is_visible:
            matrix["raw_contrast"] = MethodEligibility(
                method_id="raw_contrast",
                display_name="Raw Thermal Contrast",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Input is a visual RGB image. Differential thermal contrast requires infrared radiometric thermograms.",
                required_inputs=["infrared_thermogram_sequence"],
                scientific_principle="Evaluates differential temperature ΔT(t) = T_defect(t) - T_sound(t) across temporal heating/cooling.",
                expected_output="Peak contrast spatial map and temporal ΔT(t) curve."
            )
        elif not is_seq:
            matrix["raw_contrast"] = MethodEligibility(
                method_id="raw_contrast",
                display_name="Raw Thermal Contrast",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Single frame detected. Temporal differential contrast ΔT(t) requires at least 2 frames across time.",
                required_inputs=["temporal_frames >= 2"],
                scientific_principle="Evaluates differential temperature ΔT(t) = T_defect(t) - T_sound(t) across temporal heating/cooling.",
                expected_output="Peak contrast spatial map and temporal ΔT(t) curve."
            )
        else:
            matrix["raw_contrast"] = MethodEligibility(
                method_id="raw_contrast",
                display_name="Raw Thermal Contrast",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Multi-frame thermal sequence available.",
                required_inputs=["temporal_frames >= 2"],
                scientific_principle="Evaluates differential temperature ΔT(t) = T_defect(t) - T_sound(t) across temporal heating/cooling.",
                expected_output="Peak contrast spatial map and temporal ΔT(t) curve."
            )

        # 2. Matched Filter (LFMT Pulse Compression) - STRICT GUARD
        if is_visible or not is_seq:
            matrix["lfmt_matched_filter"] = MethodEligibility(
                method_id="lfmt_matched_filter",
                display_name="LFMT Matched Filter / Pulse Compression",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Requires an LFMT frequency-modulated chirp sequence with time progression.",
                required_inputs=["lfmt_chirp_sequence", "reference_chirp_waveform"],
                scientific_principle="Cross-correlates thermal response against reference chirp to maximize SNR and compress energy into low-sidelobe peak.",
                expected_output="Pulse-compression correlation map and temporal phase-delay profile."
            )
        elif not has_lfmt_meta:
            matrix["lfmt_matched_filter"] = MethodEligibility(
                method_id="lfmt_matched_filter",
                display_name="LFMT Matched Filter / Pulse Compression",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Excitation is not LFMT chirp (or chirp parameters f0/f1/T are absent). Matched filtering is strictly disabled on pulsed/unmodulated thermography.",
                required_inputs=["lfmt_excitation_metadata"],
                scientific_principle="Cross-correlates thermal response against reference chirp to maximize SNR and compress energy into low-sidelobe peak.",
                expected_output="Pulse-compression correlation map and temporal phase-delay profile."
            )
        else:
            matrix["lfmt_matched_filter"] = MethodEligibility(
                method_id="lfmt_matched_filter",
                display_name="LFMT Matched Filter / Pulse Compression",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Verified LFMT chirp excitation with active frequency sweep metadata.",
                required_inputs=["lfmt_chirp_sequence", "reference_chirp_waveform"],
                scientific_principle="Cross-correlates thermal response against reference chirp to maximize SNR and compress energy into low-sidelobe peak.",
                expected_output="Pulse-compression correlation map and temporal phase-delay profile."
            )

        # 3. Principal Component Thermography (PCT)
        if is_visible:
            matrix["pct"] = MethodEligibility(
                method_id="pct",
                display_name="Principal Component Thermography (PCT)",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="PCT requires an infrared temporal sequence to decompose thermal diffusion modes.",
                required_inputs=["thermal_sequence >= 3 frames"],
                scientific_principle="Singular Value Decomposition (SVD) on mean-centered temporal data to isolate spatial Empirical Orthogonal Functions (EOFs).",
                expected_output="Spatial EOF mode images and explained variance scree distribution."
            )
        elif n_frames < 3:
            matrix["pct"] = MethodEligibility(
                method_id="pct",
                display_name="Principal Component Thermography (PCT)",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason=f"Sequence has only {n_frames} frame(s). SVD decomposition requires at least 3 frames.",
                required_inputs=["temporal_frames >= 3"],
                scientific_principle="Singular Value Decomposition (SVD) on mean-centered temporal data to isolate spatial Empirical Orthogonal Functions (EOFs).",
                expected_output="Spatial EOF mode images and explained variance scree distribution."
            )
        else:
            matrix["pct"] = MethodEligibility(
                method_id="pct",
                display_name="Principal Component Thermography (PCT)",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Temporal thermogram sequence satisfies SVD rank requirements.",
                required_inputs=["temporal_frames >= 3"],
                scientific_principle="Singular Value Decomposition (SVD) on mean-centered temporal data to isolate spatial Empirical Orthogonal Functions (EOFs).",
                expected_output="Spatial EOF mode images and explained variance scree distribution."
            )

        # 4. Sparse PCT (SPCT)
        if is_visible or n_frames < 3:
            matrix["spct"] = MethodEligibility(
                method_id="spct",
                display_name="Sparse PCT (SPCT)",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Requires a multi-frame thermal sequence for L1-sparse matrix decomposition.",
                required_inputs=["thermal_sequence >= 3 frames"],
                scientific_principle="L1-regularized SparsePCA to enforce compact spatial support and isolate localized anomalies from background drift.",
                expected_output="Sparse defect candidate feature map with non-zero sparsity ratio."
            )
        else:
            matrix["spct"] = MethodEligibility(
                method_id="spct",
                display_name="Sparse PCT (SPCT)",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Temporal thermogram sequence suitable for L1 sparse matrix factorization.",
                required_inputs=["thermal_sequence >= 3 frames"],
                scientific_principle="L1-regularized SparsePCA to enforce compact spatial support and isolate localized anomalies from background drift.",
                expected_output="Sparse defect candidate feature map with non-zero sparsity ratio."
            )

        # 5. Random Projection Technique (RPT)
        if is_visible or n_frames < 3:
            matrix["rpt"] = MethodEligibility(
                method_id="rpt",
                display_name="Random Projection Technique (RPT)",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Requires a multi-frame sequence to project temporal dimensions onto random subspace.",
                required_inputs=["thermal_sequence >= 3 frames"],
                scientific_principle="Johnson-Lindenstrauss random subspace embedding preserving pairwise Euclidean distance geometry.",
                expected_output="Low-dimensional projected thermal anomaly map."
            )
        else:
            matrix["rpt"] = MethodEligibility(
                method_id="rpt",
                display_name="Random Projection Technique (RPT)",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Temporal sequence suitable for Gaussian random projection.",
                required_inputs=["thermal_sequence >= 3 frames"],
                scientific_principle="Johnson-Lindenstrauss random subspace embedding preserving pairwise Euclidean distance geometry.",
                expected_output="Low-dimensional projected thermal anomaly map."
            )

        # 6. Single-Frame Spatial Analysis
        if n_frames == 1:
            matrix["single_frame_spatial"] = MethodEligibility(
                method_id="single_frame_spatial",
                display_name="Spatial Thermal Gradient & Morphology",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Single frame provided. Spatial gradients, Laplacian response, and morphological filtering active.",
                required_inputs=["2D_image"],
                scientific_principle="Evaluates 2D spatial gradients, local entropy, and intensity extrema on single thermal frame.",
                expected_output="Spatial anomaly heatmap and Otsu segmented mask."
            )
        else:
            matrix["single_frame_spatial"] = MethodEligibility(
                method_id="single_frame_spatial",
                display_name="Spatial Thermal Gradient & Morphology",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Sequence detected. Full temporal algorithms (PCT, SPCT, RPT, Raw) supersede static single-frame spatial analysis.",
                required_inputs=["2D_image"],
                scientific_principle="Evaluates 2D spatial gradients, local entropy, and intensity extrema on single thermal frame.",
                expected_output="Spatial anomaly heatmap and Otsu segmented mask."
            )

        # 7. AI Multi-Task Classifier & Segmentation
        if is_visible:
            matrix["ai_multitask"] = MethodEligibility(
                method_id="ai_multitask",
                display_name="Physics-Informed Multi-Task AI",
                status=MethodStatus.NOT_APPLICABLE,
                is_applicable=False,
                reason="Visual RGB input is outside the thermal NDT domain. Thermographic AI models cannot evaluate photographic images.",
                required_inputs=["calibrated_thermal_input"],
                scientific_principle="Multi-task shared convolutional encoder predicting defect probability, segmentation, depth, and diameter.",
                expected_output="Defect classification probabilities, segmentation mask, and dimensional sizing."
            )
        else:
            matrix["ai_multitask"] = MethodEligibility(
                method_id="ai_multitask",
                display_name="Physics-Informed Multi-Task AI",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Valid thermal data available for multi-task neural network inference.",
                required_inputs=["thermal_features_or_maps"],
                scientific_principle="Multi-task shared convolutional encoder predicting defect probability, segmentation, depth, and diameter.",
                expected_output="Defect classification probabilities, segmentation mask, and dimensional sizing."
            )

        # 8. Physics & Diffusion Depth Features
        if is_radiometric:
            matrix["physics_features"] = MethodEligibility(
                method_id="physics_features",
                display_name="Thermal Diffusivity & Diffusion Depth μ(f)",
                status=MethodStatus.APPLICABLE,
                is_applicable=True,
                reason="Calibrated thermodynamic temperatures available.",
                required_inputs=["radiometric_temperatures_in_K"],
                scientific_principle="Derives thermal penetration depth μ = sqrt(α / (π f)) and cooling slope dT/dt.",
                expected_output="Physical diffusivity α, effusivity e, and theoretical penetration depth range."
            )
        else:
            matrix["physics_features"] = MethodEligibility(
                method_id="physics_features",
                display_name="Thermal Diffusivity & Diffusion Depth μ(f)",
                status=MethodStatus.INSUFFICIENT_METADATA,
                is_applicable=False,
                reason="Input data lack thermodynamic Kelvin calibration. Physical diffusion depth cannot be computed without calibrated units.",
                required_inputs=["radiometric_temperatures_in_K"],
                scientific_principle="Derives thermal penetration depth μ = sqrt(α / (π f)) and cooling slope dT/dt.",
                expected_output="Physical diffusivity α, effusivity e, and theoretical penetration depth range."
            )

        # Determine primary workflow
        if is_visible:
            workflow = "visible_image_warning"
        elif n_frames == 1:
            workflow = "single_thermal_image"
        elif has_lfmt_meta:
            workflow = "lfmt_chirp_sequence"
        elif exc_type == "pulsed":
            workflow = "pulsed_thermal_sequence"
        else:
            workflow = "general_thermal_sequence"

        app_count = sum(1 for m in matrix.values() if m.is_applicable)
        return ApplicabilityMatrix(
            methods=matrix,
            applicable_count=app_count,
            total_count=len(matrix),
            primary_workflow=workflow
        )
