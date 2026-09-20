"""
Experiment Orchestration, Parameter Sweeps, and Result Caching Engine.

Executes end-to-end LFMT simulation, noise injection, multi-method processing
(Raw Contrast, Matched Filter, PCT, SPCT, RPT), segmentation, and metric aggregation.
Includes deterministic hash caching to prevent redundant 3D simulation runs.
"""

from __future__ import annotations
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from lfmt.config import LFMTConfig, load_config
from lfmt.materials import get_material
from lfmt.simulation import get_simulation_backend, SimulationResult
from lfmt.camera import VirtualIRCamera, VirtualCameraCapture
from lfmt.noise import apply_noise_pipeline
from lfmt.excitation import LFMTExcitation
from lfmt.pulse_compression import LFMTMatchedFilter, PulseCompressionResult
from lfmt.contrast import RawThermalContrast, RawContrastResult
from lfmt.pct import PrincipalComponentThermography, PCTResult
from lfmt.spct import SparsePrincipalComponentThermography, SPCTResult
from lfmt.rpt import RandomProjectionTechnique, RPTResult
from lfmt.detection import DefectDetector, DetectionResult
from lfmt.metrics import compute_metrics, EvaluationMetrics


@dataclass
class MethodExecutionBundle:
    """Bundle containing processed map, detection result, and metrics for a method."""
    method_name: str
    score_map: np.ndarray
    detection: DetectionResult
    metrics: EvaluationMetrics
    raw_result: Any


@dataclass
class ExperimentCaseResult:
    """
    Complete end-to-end experimental case output.
    """
    config: LFMTConfig
    simulation_result: SimulationResult
    capture_clean: VirtualCameraCapture
    capture_noisy: VirtualCameraCapture
    contrast_bundle: MethodExecutionBundle
    matched_filter_bundle: MethodExecutionBundle
    pct_bundle: MethodExecutionBundle
    spct_bundle: MethodExecutionBundle
    rpt_bundle: MethodExecutionBundle
    metrics_dataframe: pd.DataFrame
    total_pipeline_time_s: float
    cache_hit: bool

    def get_bundle(self, name: str) -> MethodExecutionBundle:
        mapping = {
            "Raw Contrast": self.contrast_bundle,
            "Matched Filter": self.matched_filter_bundle,
            "PCT": self.pct_bundle,
            "SPCT": self.spct_bundle,
            "RPT": self.rpt_bundle,
        }
        key = name.strip()
        for k, v in mapping.items():
            if key.lower() in k.lower():
                return v
        raise KeyError(f"Method '{name}' not found. Available: {list(mapping.keys())}")


class LFMTExperimentPipeline:
    """
    Automated scientific experiment execution pipeline with disk caching.
    """

    def __init__(self, cache_dir: str | Path = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_simulation_hash(self, config: LFMTConfig) -> str:
        """Compute unique deterministic SHA-256 hash for simulation physics."""
        sim_dict = {
            "backend": config.simulation.backend,
            "res": config.simulation.spatial_resolution,
            "dt": config.simulation.timestep_s,
            "t_total": config.simulation.total_time_s,
            "plate": {
                "l": config.geometry.plate.length_mm,
                "w": config.geometry.plate.width_mm,
                "t": config.geometry.plate.thickness_mm,
                "mat": config.geometry.plate.material,
            },
            "inclusion": {
                "x": config.geometry.inclusion.center_x_mm,
                "y": config.geometry.inclusion.center_y_mm,
                "depth": config.geometry.inclusion.depth_mm,
                "diam": config.geometry.inclusion.diameter_mm,
                "thick": config.geometry.inclusion.thickness_mm,
                "mat": config.geometry.inclusion.material,
            },
            "excitation": {
                "f0": config.excitation.f0_hz,
                "f1": config.excitation.f1_hz,
                "dur": config.excitation.duration_s,
                "q0": config.excitation.q0_w_m2,
            }
        }
        encoded = json.dumps(sim_dict, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]

    def run_case(
        self,
        config: LFMTConfig,
        use_cache: bool = True
    ) -> ExperimentCaseResult:
        """
        Execute full case: Simulation -> Camera -> Noise -> 5 Processing Algorithms -> Detection -> Metrics.
        """
        pipeline_start = time.perf_counter()
        sim_hash = self._compute_simulation_hash(config)
        cache_path = self.cache_dir / f"sim_{sim_hash}.npz"
        cache_hit = False

        # 1. Simulation
        if use_cache and cache_path.exists():
            # Load cached simulation
            data = np.load(cache_path, allow_pickle=True)
            surf_temp = data["surface_temperature"]
            t_vec = data["time_vector"]
            x_grid = data["x_grid_mm"]
            y_grid = data["y_grid_mm"]
            z_grid = data["z_grid_mm"]
            gt_dict = json.loads(str(data["ground_truth_json"]))
            meta_dict = json.loads(str(data["metadata_json"]))

            from lfmt.simulation.base import GroundTruth
            gt = GroundTruth(**gt_dict)
            sim_res = SimulationResult(
                surface_temperature=surf_temp,
                time_vector=t_vec,
                x_grid_mm=x_grid,
                y_grid_mm=y_grid,
                z_grid_mm=z_grid,
                ground_truth=gt,
                backend_name=config.simulation.backend,
                metadata=meta_dict
            )
            cache_hit = True
        else:
            backend = get_simulation_backend(config.simulation.backend)
            sim_res = backend.run(config)
            if use_cache:
                np.savez_compressed(
                    cache_path,
                    surface_temperature=sim_res.surface_temperature,
                    time_vector=sim_res.time_vector,
                    x_grid_mm=sim_res.x_grid_mm,
                    y_grid_mm=sim_res.y_grid_mm,
                    z_grid_mm=sim_res.z_grid_mm,
                    ground_truth_json=json.dumps(sim_res.ground_truth.to_dict()),
                    metadata_json=json.dumps(sim_res.metadata)
                )

        # 2. Virtual IR Camera
        camera = VirtualIRCamera(config.camera)
        capture_clean = camera.capture(sim_res)

        # 3. Noise Injection
        noisy_tensor = apply_noise_pipeline(capture_clean.thermograms, config.noise)
        capture_noisy = VirtualCameraCapture(
            thermograms=noisy_tensor,
            time_vector=capture_clean.time_vector,
            ground_truth_mask=capture_clean.ground_truth_mask,
            ground_truth=capture_clean.ground_truth,
            camera_config=capture_clean.camera_config,
            metadata=capture_clean.metadata
        )

        gt_mask = capture_clean.ground_truth_mask
        gt = capture_clean.ground_truth
        fov = (config.geometry.plate.length_mm, config.geometry.plate.width_mm)

        detector = DefectDetector(
            threshold_method=config.processing.detection.threshold_method,
            morphology_kernel_size=config.processing.detection.morphology_kernel_size,
            min_area_px=config.processing.detection.min_area_px
        )

        # 4. Processing Methods (STRICT BLIND MODE - NO GROUND TRUTH LEAKAGE)
        # Method 1: Raw Thermal Contrast
        contrast_engine = RawThermalContrast(mode="blind")
        res_contrast = contrast_engine.process(capture_noisy.thermograms, capture_noisy.time_vector)
        det_contrast = detector.detect(res_contrast.contrast_map, fov_mm=fov)
        met_contrast = compute_metrics("Raw Contrast", det_contrast, gt, gt_mask, res_contrast.contrast_map, res_contrast.runtime_seconds, fov)
        bundle_contrast = MethodExecutionBundle("Raw Contrast", res_contrast.contrast_map, det_contrast, met_contrast, res_contrast)

        # Method 2: Matched Filter / Pulse Compression
        exc = LFMTExcitation(
            f0_hz=config.excitation.f0_hz,
            f1_hz=config.excitation.f1_hz,
            duration_s=config.excitation.duration_s,
            q0_w_m2=config.excitation.q0_w_m2,
            sampling_rate_hz=config.camera.sampling_rate_hz
        )
        mf_engine = LFMTMatchedFilter(excitation=exc)
        res_mf = mf_engine.process(capture_noisy.thermograms, capture_noisy.time_vector)
        det_mf = detector.detect(res_mf.normalized_map, fov_mm=fov)
        met_mf = compute_metrics("Matched Filter", det_mf, gt, gt_mask, res_mf.normalized_map, res_mf.runtime_seconds, fov)
        bundle_mf = MethodExecutionBundle("Matched Filter", res_mf.normalized_map, det_mf, met_mf, res_mf)

        # Method 3: PCT (Blind Excess Kurtosis)
        pct_engine = PrincipalComponentThermography(
            n_components=config.processing.pct.n_components,
            selection_criterion=config.processing.pct.selection_criterion,
            mode="blind"
        )
        res_pct = pct_engine.process(capture_noisy.thermograms)
        det_pct = detector.detect(res_pct.selected_eof_image, fov_mm=fov)
        met_pct = compute_metrics("PCT", det_pct, gt, gt_mask, res_pct.selected_eof_image, res_pct.runtime_seconds, fov)
        bundle_pct = MethodExecutionBundle("PCT", res_pct.selected_eof_image, det_pct, met_pct, res_pct)

        # Method 4: SPCT (Blind Anomaly Ratio)
        spct_engine = SparsePrincipalComponentThermography(
            n_components=config.processing.spct.n_components,
            alpha=config.processing.spct.alpha,
            max_iter=config.processing.spct.max_iter,
            mode="blind"
        )
        res_spct = spct_engine.process(capture_noisy.thermograms)
        det_spct = detector.detect(res_spct.selected_sparse_image, fov_mm=fov)
        met_spct = compute_metrics("SPCT", det_spct, gt, gt_mask, res_spct.selected_sparse_image, res_spct.runtime_seconds, fov)
        bundle_spct = MethodExecutionBundle("SPCT", res_spct.selected_sparse_image, det_spct, met_spct, res_spct)

        # Method 5: RPT (Blind Dynamic Range)
        rpt_engine = RandomProjectionTechnique(
            n_components=config.processing.rpt.n_components,
            matrix_type=config.processing.rpt.matrix_type,
            mode="blind"
        )
        res_rpt = rpt_engine.process(capture_noisy.thermograms)
        det_rpt = detector.detect(res_rpt.selected_rpt_image, fov_mm=fov)
        met_rpt = compute_metrics("RPT", det_rpt, gt, gt_mask, res_rpt.selected_rpt_image, res_rpt.runtime_seconds, fov)
        bundle_rpt = MethodExecutionBundle("RPT", res_rpt.selected_rpt_image, det_rpt, met_rpt, res_rpt)

        # 5. Build summary table DataFrame
        metrics_list = [
            met_contrast.to_dict(),
            met_mf.to_dict(),
            met_pct.to_dict(),
            met_spct.to_dict(),
            met_rpt.to_dict(),
        ]
        df_metrics = pd.DataFrame(metrics_list)

        total_time = time.perf_counter() - pipeline_start

        return ExperimentCaseResult(
            config=config,
            simulation_result=sim_res,
            capture_clean=capture_clean,
            capture_noisy=capture_noisy,
            contrast_bundle=bundle_contrast,
            matched_filter_bundle=bundle_mf,
            pct_bundle=bundle_pct,
            spct_bundle=bundle_spct,
            rpt_bundle=bundle_rpt,
            metrics_dataframe=df_metrics,
            total_pipeline_time_s=total_time,
            cache_hit=cache_hit
        )


def run_parameter_sweep(
    base_config: LFMTConfig,
    diameters_mm: List[float],
    depths_mm: List[float],
    noise_levels_db: List[Optional[float]],
    output_dir: str | Path = "results/sweep",
    progress_callback: Optional[Any] = None
) -> pd.DataFrame:
    """
    Execute systematic parameter sweep over inclusion diameters, depths, and noise levels.
    """
    pipeline = LFMTExperimentPipeline()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    records = []
    total_cases = len(diameters_mm) * len(depths_mm) * len(noise_levels_db)
    current_case = 0

    for diam in diameters_mm:
        for depth in depths_mm:
            for noise_snr in noise_levels_db:
                current_case += 1
                cfg = load_config("configs/default.yaml") if base_config is None else base_config
                cfg.geometry.inclusion.diameter_mm = float(diam)
                cfg.geometry.inclusion.depth_mm = float(depth)
                cfg.noise.snr_db = noise_snr

                try:
                    result = pipeline.run_case(cfg, use_cache=True)
                    for row in result.metrics_dataframe.to_dict(orient="records"):
                        rec = {
                            "diameter_mm": diam,
                            "depth_mm": depth,
                            "aspect_ratio_d_over_z": round(diam / depth, 2) if depth > 0 else 0.0,
                            "noise_snr_db": noise_snr if noise_snr is not None else "Clean (Inf)",
                            **row
                        }
                        records.append(rec)
                except Exception as e:
                    print(f"Error evaluating Case (diam={diam}, depth={depth}, noise={noise_snr}): {e}")

                if progress_callback is not None:
                    progress_callback(current_case, total_cases)

    df_sweep = pd.DataFrame(records)
    df_sweep.to_csv(out_path / "sweep_results.csv", index=False)
    return df_sweep
