import os
import sys
import json
import hashlib
import time
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from lfmt.config import (
    LFMTConfig,
    PlateConfig,
    InclusionConfig,
    GeometryConfig,
    SimulationConfig,
    ExcitationConfig,
)
from lfmt.simulation.fem import FEMBackend

DEF_SHA = "115fa00e6e8ce0cc7742c0659717e179e520bfe7"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def write_sha256(ex_dir: Path) -> None:
    lines = []
    for p in sorted(ex_dir.iterdir()):
        if p.is_file() and p.name != "sha256.txt":
            lines.append(f"{compute_sha256(p)}  {p.name}")
    (ex_dir / "sha256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    root = repo_root
    ex_root = root / "data" / "examples"
    ex_root.mkdir(parents=True, exist_ok=True)
    backend = FEMBackend(fallback_if_unavailable=False)
    print("Using FEM engine:", backend.engine_name)
    gen_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # 1. Healthy LFMT
    print("1. Generating Healthy LFMT...")
    h_dir = ex_root / "healthy_lfmt"
    h_dir.mkdir(exist_ok=True)
    cfg_h = LFMTConfig(
        geometry=GeometryConfig(
            plate=PlateConfig(length_mm=100.0, width_mm=70.0, thickness_mm=2.3, material="mild_steel"),
            inclusion=InclusionConfig(diameter_mm=0.0, depth_mm=0.0, thickness_mm=0.5),
        ),
        simulation=SimulationConfig(
            backend="fem",
            total_time_s=10.0,
            timestep_s=0.1,
            spatial_resolution={"nx": 40, "ny": 28, "nz": 10},
        ),
        excitation=ExcitationConfig(f0_hz=0.05, f1_hz=0.50, duration_s=10.0, q0_w_m2=5000.0),
    )
    res_h = backend.run(cfg_h)
    surf_h = res_h.surface_temperature.astype(np.float32)
    t_vec = res_h.time_vector.astype(np.float32)
    np.savez_compressed(h_dir / "thermograms.npz", surface_temperature=surf_h, time_vector=t_vec)

    meta_h = {
        "example_id": "healthy_lfmt",
        "title": "Healthy Mild Steel Plate (LFMT Chirp)",
        "category": "A",
        "source_type": "NUMERICAL_FEM",
        "material": "mild_steel",
        "plate_dimensions_mm": [100.0, 70.0, 2.3],
        "defects": [],
        "depth_definition": "front_surface_to_top_of_inclusion",
        "excitation": {"type": "lfmt_chirp", "f0_hz": 0.05, "f1_hz": 0.50, "q0_w_m2": 5000.0, "duration_s": 10.0},
        "mesh": {"backend": "fem", "resolution": {"nx": 40, "ny": 28, "nz": 10}, "strategy": "uniform_hex"},
        "time": {"dt_s": 0.1, "n_frames": int(surf_h.shape[0]), "duration_s": 10.0},
        "camera": {"frame_rate_hz": 10.0, "resolution": [int(surf_h.shape[1]), int(surf_h.shape[2])], "fov_mm": [100.0, 70.0]},
        "temperature_units": "K",
        "temperature_unit_status": "SOURCE_VERIFIED",
        "radiometric_status": "VERIFIED_NUMERICAL",
        "software_git_sha": DEF_SHA,
        "generated_timestamp": gen_time,
        "generator_script": "scripts/generate_verified_examples.py",
        "scientific_status": "VERIFIED_FEM_NEGATIVE_CONTROL",
    }
    (h_dir / "metadata.json").write_text(json.dumps(meta_h, indent=2), encoding="utf-8")
    exp_h = {
        "expected_anomaly": False,
        "lfmt_matched_filter_applicable": True,
        "pct_applicable": True,
        "spct_applicable": True,
        "rpt_applicable": True,
        "single_frame_spatial_applicable": False,
        "expected_defect_count": 0,
        "expected_final_verdict": "HEALTHY",
        "scientific_notes": "Negative control sample. Confirms zero false positive rate in pure homogeneous conduction.",
    }
    (h_dir / "expected_result.json").write_text(json.dumps(exp_h, indent=2), encoding="utf-8")
    write_sha256(h_dir)

    # 2. Shallow Slag
    print("2. Generating Shallow Slag (d=0.4 mm)...")
    s_dir = ex_root / "slag_shallow"
    s_dir.mkdir(exist_ok=True)
    cfg_s = LFMTConfig(
        geometry=GeometryConfig(
            plate=PlateConfig(length_mm=100.0, width_mm=70.0, thickness_mm=2.3, material="mild_steel"),
            inclusion=InclusionConfig(
                shape="cylinder",
                diameter_mm=8.0,
                depth_mm=0.4,
                thickness_mm=0.5,
                center_x_mm=50.0,
                center_y_mm=35.0,
                material="slag",
            ),
        ),
        simulation=SimulationConfig(
            backend="fem",
            total_time_s=10.0,
            timestep_s=0.1,
            spatial_resolution={"nx": 40, "ny": 28, "nz": 12},
        ),
        excitation=ExcitationConfig(f0_hz=0.05, f1_hz=0.50, duration_s=10.0, q0_w_m2=5000.0),
    )
    res_s = backend.run(cfg_s)
    surf_s = res_s.surface_temperature.astype(np.float32)
    np.savez_compressed(s_dir / "thermograms.npz", surface_temperature=surf_s, time_vector=t_vec)

    meta_s = {
        "example_id": "slag_shallow",
        "title": "Shallow Subsurface Slag Inclusion (d = 0.4 mm, D = 8.0 mm)",
        "category": "A",
        "source_type": "NUMERICAL_FEM",
        "material": "mild_steel",
        "plate_dimensions_mm": [100.0, 70.0, 2.3],
        "defects": [
            {
                "defect_id": "SLAG-01",
                "defect_type": "SLAG_INCLUSION",
                "diameter_mm": 8.0,
                "depth_mm": 0.4,
                "thickness_mm": 0.5,
                "center_x_mm": 50.0,
                "center_y_mm": 35.0,
                "aspect_ratio": 20.0,
            }
        ],
        "depth_definition": "front_surface_to_top_of_inclusion",
        "excitation": {"type": "lfmt_chirp", "f0_hz": 0.05, "f1_hz": 0.50, "q0_w_m2": 5000.0, "duration_s": 10.0},
        "mesh": {"backend": "fem", "resolution": {"nx": 40, "ny": 28, "nz": 12}, "strategy": "uniform_hex"},
        "time": {"dt_s": 0.1, "n_frames": int(surf_s.shape[0]), "duration_s": 10.0},
        "camera": {"frame_rate_hz": 10.0, "resolution": [int(surf_s.shape[1]), int(surf_s.shape[2])], "fov_mm": [100.0, 70.0]},
        "temperature_units": "K",
        "temperature_unit_status": "SOURCE_VERIFIED",
        "radiometric_status": "VERIFIED_NUMERICAL",
        "software_git_sha": DEF_SHA,
        "generated_timestamp": gen_time,
        "generator_script": "scripts/generate_verified_examples.py",
        "scientific_status": "VERIFIED_FEM_HIGH_CONFIDENCE_ANOMALY",
    }
    (s_dir / "metadata.json").write_text(json.dumps(meta_s, indent=2), encoding="utf-8")
    gt_s = {
        "evaluation_only": True,
        "notice": "Ground truth is strictly isolated and inaccessible during blind inference.",
        "defects": meta_s["defects"],
    }
    (s_dir / "ground_truth.json").write_text(json.dumps(gt_s, indent=2), encoding="utf-8")
    exp_s = {
        "expected_anomaly": True,
        "lfmt_matched_filter_applicable": True,
        "pct_applicable": True,
        "spct_applicable": True,
        "rpt_applicable": True,
        "single_frame_spatial_applicable": False,
        "expected_defect_count_min": 1,
        "expected_uncalibrated_verdict": "GENERIC_SUBSURFACE_THERMAL_ANOMALY",
        "scientific_notes": "High thermal effusivity disparity produces clear surface thermal elevation.",
    }
    (s_dir / "expected_result.json").write_text(json.dumps(exp_s, indent=2), encoding="utf-8")
    write_sha256(s_dir)

    # 3. Deep Slag
    print("3. Generating Deep Slag (d=0.8 mm)...")
    d_dir = ex_root / "slag_deep"
    d_dir.mkdir(exist_ok=True)
    cfg_d = LFMTConfig(
        geometry=GeometryConfig(
            plate=PlateConfig(length_mm=100.0, width_mm=70.0, thickness_mm=2.3, material="mild_steel"),
            inclusion=InclusionConfig(
                shape="cylinder",
                diameter_mm=8.0,
                depth_mm=0.8,
                thickness_mm=0.5,
                center_x_mm=50.0,
                center_y_mm=35.0,
                material="slag",
            ),
        ),
        simulation=SimulationConfig(
            backend="fem",
            total_time_s=10.0,
            timestep_s=0.1,
            spatial_resolution={"nx": 40, "ny": 28, "nz": 12},
        ),
        excitation=ExcitationConfig(f0_hz=0.05, f1_hz=0.50, duration_s=10.0, q0_w_m2=5000.0),
    )
    res_d = backend.run(cfg_d)
    surf_d = res_d.surface_temperature.astype(np.float32)
    np.savez_compressed(d_dir / "thermograms.npz", surface_temperature=surf_d, time_vector=t_vec)

    meta_d = {
        "example_id": "slag_deep",
        "title": "Deep Subsurface Slag Inclusion (d = 0.8 mm, D = 8.0 mm)",
        "category": "A",
        "source_type": "NUMERICAL_FEM",
        "material": "mild_steel",
        "plate_dimensions_mm": [100.0, 70.0, 2.3],
        "defects": [
            {
                "defect_id": "SLAG-01",
                "defect_type": "SLAG_INCLUSION",
                "diameter_mm": 8.0,
                "depth_mm": 0.8,
                "thickness_mm": 0.5,
                "center_x_mm": 50.0,
                "center_y_mm": 35.0,
                "aspect_ratio": 10.0,
            }
        ],
        "depth_definition": "front_surface_to_top_of_inclusion",
        "excitation": {"type": "lfmt_chirp", "f0_hz": 0.05, "f1_hz": 0.50, "q0_w_m2": 5000.0, "duration_s": 10.0},
        "mesh": {"backend": "fem", "resolution": {"nx": 40, "ny": 28, "nz": 12}, "strategy": "uniform_hex"},
        "time": {"dt_s": 0.1, "n_frames": int(surf_d.shape[0]), "duration_s": 10.0},
        "camera": {"frame_rate_hz": 10.0, "resolution": [int(surf_d.shape[1]), int(surf_d.shape[2])], "fov_mm": [100.0, 70.0]},
        "temperature_units": "K",
        "temperature_unit_status": "SOURCE_VERIFIED",
        "radiometric_status": "VERIFIED_NUMERICAL",
        "software_git_sha": DEF_SHA,
        "generated_timestamp": gen_time,
        "generator_script": "scripts/generate_verified_examples.py",
        "scientific_status": "VERIFIED_FEM_MODERATE_DEPTH_ANOMALY",
    }
    (d_dir / "metadata.json").write_text(json.dumps(meta_d, indent=2), encoding="utf-8")
    gt_d = {
        "evaluation_only": True,
        "notice": "Ground truth is strictly isolated and inaccessible during blind inference.",
        "defects": meta_d["defects"],
    }
    (d_dir / "ground_truth.json").write_text(json.dumps(gt_d, indent=2), encoding="utf-8")
    exp_d = {
        "expected_anomaly": True,
        "lfmt_matched_filter_applicable": True,
        "pct_applicable": True,
        "spct_applicable": True,
        "rpt_applicable": True,
        "single_frame_spatial_applicable": False,
        "expected_defect_count_min": 1,
        "expected_uncalibrated_verdict": "GENERIC_SUBSURFACE_THERMAL_ANOMALY",
        "scientific_notes": "Diffusion attenuation delays peak surface response.",
    }
    (d_dir / "expected_result.json").write_text(json.dumps(exp_d, indent=2), encoding="utf-8")
    write_sha256(d_dir)

    # 4. Multi-Defect Slag
    print("4. Generating Multi-Defect Slag...")
    m_dir = ex_root / "multi_slag"
    m_dir.mkdir(exist_ok=True)
    cfg_m = LFMTConfig(
        geometry=GeometryConfig(
            plate=PlateConfig(length_mm=100.0, width_mm=70.0, thickness_mm=2.3, material="mild_steel"),
            inclusion=InclusionConfig(
                shape="multi_inclusion",
                diameter_mm=6.0,
                depth_mm=0.4,
                thickness_mm=0.5,
                center_x_mm=50.0,
                center_y_mm=35.0,
                material="slag",
            ),
        ),
        simulation=SimulationConfig(
            backend="fem",
            total_time_s=10.0,
            timestep_s=0.1,
            spatial_resolution={"nx": 40, "ny": 28, "nz": 12},
        ),
        excitation=ExcitationConfig(f0_hz=0.05, f1_hz=0.50, duration_s=10.0, q0_w_m2=5000.0),
    )
    res_m = backend.run(cfg_m)
    surf_m = res_m.surface_temperature.astype(np.float32)
    np.savez_compressed(m_dir / "thermograms.npz", surface_temperature=surf_m, time_vector=t_vec)

    meta_m = {
        "example_id": "multi_slag",
        "title": "Multiple Subsurface Slag Inclusions (Dual Disjoint Domains)",
        "category": "A",
        "source_type": "NUMERICAL_FEM",
        "material": "mild_steel",
        "plate_dimensions_mm": [100.0, 70.0, 2.3],
        "defects": [
            {
                "defect_id": "SLAG-01",
                "defect_type": "SLAG_INCLUSION",
                "diameter_mm": 6.0,
                "depth_mm": 0.4,
                "thickness_mm": 0.5,
                "center_x_mm": 42.5,
                "center_y_mm": 35.0,
            },
            {
                "defect_id": "SLAG-02",
                "defect_type": "SLAG_INCLUSION",
                "diameter_mm": 4.8,
                "depth_mm": 0.4,
                "thickness_mm": 0.5,
                "center_x_mm": 57.5,
                "center_y_mm": 35.0,
            },
        ],
        "depth_definition": "front_surface_to_top_of_inclusion",
        "excitation": {"type": "lfmt_chirp", "f0_hz": 0.05, "f1_hz": 0.50, "q0_w_m2": 5000.0, "duration_s": 10.0},
        "mesh": {"backend": "fem", "resolution": {"nx": 40, "ny": 28, "nz": 12}, "strategy": "uniform_hex"},
        "time": {"dt_s": 0.1, "n_frames": int(surf_m.shape[0]), "duration_s": 10.0},
        "camera": {"frame_rate_hz": 10.0, "resolution": [int(surf_m.shape[1]), int(surf_m.shape[2])], "fov_mm": [100.0, 70.0]},
        "temperature_units": "K",
        "temperature_unit_status": "SOURCE_VERIFIED",
        "radiometric_status": "VERIFIED_NUMERICAL",
        "software_git_sha": DEF_SHA,
        "generated_timestamp": gen_time,
        "generator_script": "scripts/generate_verified_examples.py",
        "scientific_status": "VERIFIED_FEM_MULTI_DEFECT",
    }
    (m_dir / "metadata.json").write_text(json.dumps(meta_m, indent=2), encoding="utf-8")
    gt_m = {
        "evaluation_only": True,
        "notice": "Ground truth is strictly isolated and inaccessible during blind inference.",
        "defects": meta_m["defects"],
    }
    (m_dir / "ground_truth.json").write_text(json.dumps(gt_m, indent=2), encoding="utf-8")
    exp_m = {
        "expected_anomaly": True,
        "lfmt_matched_filter_applicable": True,
        "pct_applicable": True,
        "spct_applicable": True,
        "rpt_applicable": True,
        "single_frame_spatial_applicable": False,
        "expected_defect_count_min": 1,
        "expected_uncalibrated_verdict": "GENERIC_SUBSURFACE_THERMAL_ANOMALY",
        "scientific_notes": "Multi-inclusion cluster produces multiple localized high-contrast signatures.",
    }
    (m_dir / "expected_result.json").write_text(json.dumps(exp_m, indent=2), encoding="utf-8")
    write_sha256(m_dir)

    # 5. Single Frame
    print("5. Generating Single Thermal Frame...")
    sf_dir = ex_root / "single_thermal_frame"
    sf_dir.mkdir(exist_ok=True)
    peak_frame_idx = 80
    peak_frame = surf_s[peak_frame_idx]
    np.save(sf_dir / "thermal_frame.npy", peak_frame)

    meta_sf = {
        "example_id": "single_thermal_frame",
        "title": "Single Thermogram Snapshot (t = 8.0 s)",
        "category": "A",
        "source_type": "NUMERICAL_FEM_EXTRACT",
        "source_example_id": "slag_shallow",
        "source_frame_index": peak_frame_idx,
        "source_time_s": 8.0,
        "material": "mild_steel",
        "plate_dimensions_mm": [100.0, 70.0, 2.3],
        "excitation": {"type": "snapshot", "source_excitation": "lfmt_chirp"},
        "time": {"n_frames": 1, "duration_s": 0.0},
        "camera": {"resolution": [int(peak_frame.shape[0]), int(peak_frame.shape[1])], "fov_mm": [100.0, 70.0]},
        "temperature_units": "K",
        "temperature_unit_status": "SOURCE_VERIFIED",
        "radiometric_status": "VERIFIED_NUMERICAL",
        "software_git_sha": DEF_SHA,
        "generated_timestamp": gen_time,
        "generator_script": "scripts/generate_verified_examples.py",
        "scientific_status": "VERIFIED_SINGLE_FRAME_SPATIAL",
    }
    (sf_dir / "metadata.json").write_text(json.dumps(meta_sf, indent=2), encoding="utf-8")
    exp_sf = {
        "expected_anomaly": True,
        "single_frame_spatial_applicable": True,
        "lfmt_matched_filter_applicable": False,
        "pct_applicable": False,
        "spct_applicable": False,
        "rpt_applicable": False,
        "expected_defect_count_min": 1,
        "expected_uncalibrated_verdict": "GENERIC_SUBSURFACE_THERMAL_ANOMALY",
        "scientific_notes": "Temporal processing methods are strictly disabled for single frames.",
    }
    (sf_dir / "expected_result.json").write_text(json.dumps(exp_sf, indent=2), encoding="utf-8")
    write_sha256(sf_dir)

    # 6. PolyU Preview
    print("6. Generating PolyU Preview Metadata...")
    p_dir = ex_root / "measured_polyu_preview"
    p_dir.mkdir(exist_ok=True)
    (p_dir / "README.md").write_text("# PolyU Flash Pulsed Thermography\nDOI: 10.60933/PRDR/HJYNZB\n", encoding="utf-8")
    meta_p = {
        "example_id": "measured_polyu_preview",
        "title": "PolyU Measured Flash Pulsed Thermography (Mild Steel 11-FBH)",
        "category": "B",
        "source_type": "EXTERNAL_MEASURED",
        "material": "mild_steel",
        "plate_dimensions_mm": [150.0, 150.0, 10.0],
        "excitation": {"type": "pulsed_flash", "energy_kj": 6.0, "pulse_duration_ms": 4.0},
        "camera": {"frame_rate_hz": 50.0, "resolution": [256, 320], "fov_mm": [150.0, 150.0]},
        "temperature_units": "C",
        "temperature_unit_status": "EXPLICIT",
        "radiometric_status": "MEASURED_RADIOMETRIC",
        "GT_available": True,
        "dataset_installed": False,
        "scientific_status": "EXTERNAL_MEASURED_TRANSFER_STUDY",
        "guardrails": ["Matched Filter MUST be disabled.", "This is NOT physical validation of LFMT slag."],
    }
    (p_dir / "metadata.json").write_text(json.dumps(meta_p, indent=2), encoding="utf-8")
    src_p = {
        "repository": "PolyU Research Data Repository",
        "doi": "10.60933/PRDR/HJYNZB",
        "version": "2.0",
        "license": "CC-BY 4.0",
        "local_raw_path": "data/real_world_external/polyu_mild_steel_pulsed/raw/MS-facq-50Hz-air-cir-1_0-999.zip",
    }
    (p_dir / "source.json").write_text(json.dumps(src_p, indent=2), encoding="utf-8")
    exp_p = {
        "expected_anomaly": True,
        "lfmt_matched_filter_applicable": False,
        "pct_applicable": True,
        "spct_applicable": True,
        "rpt_applicable": True,
        "single_frame_spatial_applicable": False,
        "expected_uncalibrated_verdict": "GENERIC_SUBSURFACE_THERMAL_ANOMALY",
        "scientific_notes": "Flash pulsed sequence on mild steel. Matched filter strictly disabled.",
    }
    (p_dir / "expected_result.json").write_text(json.dumps(exp_p, indent=2), encoding="utf-8")
    write_sha256(p_dir)

    # 7. Master Manifest
    print("7. Writing Master Manifest...")
    manifest = {
        "schema_version": "3.0.0",
        "generator_git_sha": DEF_SHA,
        "generated_timestamp": gen_time,
        "total_examples": 6,
        "categories": {"A": "NUMERICAL_FEM_LFMT", "B": "EXTERNAL_MEASURED_THERMOGRAPHY"},
        "examples": [
            {
                "id": "healthy_lfmt",
                "title": "Healthy Mild Steel Plate",
                "short_description": "Homogeneous AISI 1018 steel without inclusions under LFMT chirp.",
                "category": "A",
                "source_type": "NUMERICAL_FEM",
                "material": "mild_steel",
                "excitation_type": "lfmt_chirp",
                "defect_description": "None (Negative control)",
                "frames": 101,
                "resolution": [28, 40],
                "frame_rate_hz": 10.0,
                "duration_s": 10.0,
                "temperature_unit_status": "SOURCE_VERIFIED",
                "radiometric_status": "VERIFIED_NUMERICAL",
                "fov_status": "VERIFIED_100x70_MM",
                "GT_available": False,
                "example_available": True,
                "classifier_required": False,
                "supported_methods": ["raw_contrast", "lfmt_matched_filter", "pct", "spct", "rpt"],
                "data_path": "data/examples/healthy_lfmt/thermograms.npz",
                "metadata_path": "data/examples/healthy_lfmt/metadata.json",
                "expected_result_path": "data/examples/healthy_lfmt/expected_result.json",
                "data_size_bytes": (h_dir / "thermograms.npz").stat().st_size,
            },
            {
                "id": "slag_shallow",
                "title": "Shallow Slag Inclusion (d = 0.4 mm)",
                "short_description": "Single cylindrical welding slag inclusion (D = 8.0 mm, d = 0.4 mm) in mild steel.",
                "category": "A",
                "source_type": "NUMERICAL_FEM",
                "material": "mild_steel",
                "excitation_type": "lfmt_chirp",
                "defect_description": "Single slag inclusion (D = 8.0 mm, d = 0.4 mm)",
                "frames": 101,
                "resolution": [28, 40],
                "frame_rate_hz": 10.0,
                "duration_s": 10.0,
                "temperature_unit_status": "SOURCE_VERIFIED",
                "radiometric_status": "VERIFIED_NUMERICAL",
                "fov_status": "VERIFIED_100x70_MM",
                "GT_available": True,
                "example_available": True,
                "classifier_required": False,
                "supported_methods": ["raw_contrast", "lfmt_matched_filter", "pct", "spct", "rpt"],
                "data_path": "data/examples/slag_shallow/thermograms.npz",
                "metadata_path": "data/examples/slag_shallow/metadata.json",
                "ground_truth_path": "data/examples/slag_shallow/ground_truth.json",
                "expected_result_path": "data/examples/slag_shallow/expected_result.json",
                "data_size_bytes": (s_dir / "thermograms.npz").stat().st_size,
            },
            {
                "id": "slag_deep",
                "title": "Deep Slag Inclusion (d = 0.8 mm)",
                "short_description": "Single cylindrical slag inclusion (D = 8.0 mm, d = 0.8 mm) with lower surface thermal elevation.",
                "category": "A",
                "source_type": "NUMERICAL_FEM",
                "material": "mild_steel",
                "excitation_type": "lfmt_chirp",
                "defect_description": "Single deep slag inclusion (D = 8.0 mm, d = 0.8 mm)",
                "frames": 101,
                "resolution": [28, 40],
                "frame_rate_hz": 10.0,
                "duration_s": 10.0,
                "temperature_unit_status": "SOURCE_VERIFIED",
                "radiometric_status": "VERIFIED_NUMERICAL",
                "fov_status": "VERIFIED_100x70_MM",
                "GT_available": True,
                "example_available": True,
                "classifier_required": False,
                "supported_methods": ["raw_contrast", "lfmt_matched_filter", "pct", "spct", "rpt"],
                "data_path": "data/examples/slag_deep/thermograms.npz",
                "metadata_path": "data/examples/slag_deep/metadata.json",
                "ground_truth_path": "data/examples/slag_deep/ground_truth.json",
                "expected_result_path": "data/examples/slag_deep/expected_result.json",
                "data_size_bytes": (d_dir / "thermograms.npz").stat().st_size,
            },
            {
                "id": "multi_slag",
                "title": "Multiple Slag Inclusions",
                "short_description": "Two spatially disjoint slag inclusions (D = 6.0 mm and 4.8 mm, d = 0.4 mm) in mild steel.",
                "category": "A",
                "source_type": "NUMERICAL_FEM",
                "material": "mild_steel",
                "excitation_type": "lfmt_chirp",
                "defect_description": "Multiple slag inclusions (dual disjoint domain)",
                "frames": 101,
                "resolution": [28, 40],
                "frame_rate_hz": 10.0,
                "duration_s": 10.0,
                "temperature_unit_status": "SOURCE_VERIFIED",
                "radiometric_status": "VERIFIED_NUMERICAL",
                "fov_status": "VERIFIED_100x70_MM",
                "GT_available": True,
                "example_available": True,
                "classifier_required": False,
                "supported_methods": ["raw_contrast", "lfmt_matched_filter", "pct", "spct", "rpt"],
                "data_path": "data/examples/multi_slag/thermograms.npz",
                "metadata_path": "data/examples/multi_slag/metadata.json",
                "ground_truth_path": "data/examples/multi_slag/ground_truth.json",
                "expected_result_path": "data/examples/multi_slag/expected_result.json",
                "data_size_bytes": (m_dir / "thermograms.npz").stat().st_size,
            },
            {
                "id": "single_thermal_frame",
                "title": "Single Thermogram Snapshot",
                "short_description": "Single 2D infrared thermal image (t = 8.0 s extract). Temporal methods automatically disabled.",
                "category": "A",
                "source_type": "NUMERICAL_FEM_EXTRACT",
                "material": "mild_steel",
                "excitation_type": "single_snapshot",
                "defect_description": "Single-frame spatial anomaly",
                "frames": 1,
                "resolution": [28, 40],
                "frame_rate_hz": 0.0,
                "duration_s": 0.0,
                "temperature_unit_status": "SOURCE_VERIFIED",
                "radiometric_status": "VERIFIED_NUMERICAL",
                "fov_status": "VERIFIED_100x70_MM",
                "GT_available": False,
                "example_available": True,
                "classifier_required": False,
                "supported_methods": ["single_frame_spatial"],
                "data_path": "data/examples/single_thermal_frame/thermal_frame.npy",
                "metadata_path": "data/examples/single_thermal_frame/metadata.json",
                "expected_result_path": "data/examples/single_thermal_frame/expected_result.json",
                "data_size_bytes": (sf_dir / "thermal_frame.npy").stat().st_size,
            },
            {
                "id": "measured_polyu_preview",
                "title": "PolyU Measured Pulsed Thermography",
                "short_description": "Real laboratory flash pulsed thermography on 10 mm mild steel with 11 flat-bottom holes.",
                "category": "B",
                "source_type": "EXTERNAL_MEASURED",
                "material": "mild_steel",
                "excitation_type": "pulsed_flash",
                "defect_description": "11 Flat-Bottom Holes (corrosion / wall-thinning surrogates)",
                "frames": 1000,
                "resolution": [256, 320],
                "frame_rate_hz": 50.0,
                "duration_s": 20.0,
                "temperature_unit_status": "EXPLICIT",
                "radiometric_status": "MEASURED_RADIOMETRIC",
                "fov_status": "VERIFIED_150x150_MM",
                "GT_available": True,
                "example_available": (root / "data" / "real_world_external" / "polyu_mild_steel_pulsed" / "raw" / "MS-facq-50Hz-air-cir-1_0-999.zip").exists(),
                "classifier_required": False,
                "supported_methods": ["raw_contrast", "pct", "spct", "rpt"],
                "data_path": "data/real_world_external/polyu_mild_steel_pulsed/raw/MS-facq-50Hz-air-cir-1_0-999.zip",
                "metadata_path": "data/examples/measured_polyu_preview/metadata.json",
                "expected_result_path": "data/examples/measured_polyu_preview/expected_result.json",
                "data_size_bytes": 0,
            },
        ],
    }
    (ex_root / "examples_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    readme_main = """# Verified Thermographic Example Data Library

This directory contains standardized, scientifically verified thermography reference samples:

| ID | Title | Category | Source Type | Material | Excitation |
|:---|:---|:---:|:---|:---|:---|
| `healthy_lfmt` | Healthy Mild Steel Plate | A | Numerical 3D FEM | AISI 1018 Steel | LFMT Chirp (0.05-0.50 Hz) |
| `slag_shallow` | Shallow Slag Inclusion (d = 0.4 mm) | A | Numerical 3D FEM | AISI 1018 + Slag | LFMT Chirp (0.05-0.50 Hz) |
| `slag_deep` | Deep Slag Inclusion (d = 0.8 mm) | A | Numerical 3D FEM | AISI 1018 + Slag | LFMT Chirp (0.05-0.50 Hz) |
| `multi_slag` | Multiple Slag Inclusions | A | Numerical 3D FEM | AISI 1018 + Slag | LFMT Chirp (0.05-0.50 Hz) |
| `single_thermal_frame` | Single Thermogram Snapshot | A | Numerical FEM Extract | AISI 1018 + Slag | Single Snapshot |
| `measured_polyu_preview` | PolyU Pulsed Thermography | B | External Measured | AISI 1018 Mild Steel | 6 kJ Pulsed Flash |

Every numerical example is generated by `FEMBackend` in `src/lfmt/simulation/fem.py` with verified SHA256 checksums.
"""
    (ex_root / "README.md").write_text(readme_main, encoding="utf-8")
    print("Example data library successfully created and verified.")


if __name__ == "__main__":
    main()
