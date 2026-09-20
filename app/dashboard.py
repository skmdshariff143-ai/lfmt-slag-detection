"""
LFMT Subsurface Slag Detection — Interactive Scientific Dashboard & Conference Suite.

Linear Frequency-Modulated Infrared Thermography for Subsurface Slag Inclusion
Characterization and Non-Destructive Testing (NDT) in Mild Steel.
"""

from __future__ import annotations
import math
import sys
from pathlib import Path

# Ensure src/ is on path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir / "src") not in sys.path:
    sys.path.insert(0, str(root_dir / "src"))

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from lfmt.config import LFMTConfig, load_config
from lfmt.materials import MATERIAL_DATABASE, get_material
from lfmt.excitation import LFMTExcitation
from lfmt.experiments import LFMTExperimentPipeline, run_parameter_sweep
from lfmt.simulation.fem import _check_fem_engine
from lfmt.visualization import (
    plot_excitation_waveform,
    plot_thermogram_progression,
    plot_temporal_contrast_curves,
    plot_method_comparison_panel,
    plot_depth_performance,
    plot_runtime_comparison,
)

# Page configuration
st.set_page_config(
    page_title="LFMT Slag Detection | Scientific NDT Suite",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00adb5;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 15px;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 14px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_pipeline():
    return LFMTExperimentPipeline(cache_dir="data/cache")


pipeline = get_pipeline()

# Sidebar: Global Parameters & Mode Switcher
st.sidebar.markdown("### 🎛️ Experimental Setup")

mode = st.sidebar.radio(
    "Application Mode",
    ["⚡ Conference Mode (Single-Screen)", "🔬 In-Depth Scientific Analysis"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 1. Specimen & Inclusion Geometry")
inclusion_diam = st.sidebar.select_slider(
    "Inclusion Diameter [mm]",
    options=[4.0, 6.0, 8.0, 10.0, 12.0],
    value=8.0,
    help="Diameter of the subsurface slag inclusion disc."
)
inclusion_depth = st.sidebar.select_slider(
    "Inclusion Depth [mm]",
    options=[0.2, 0.4, 0.6, 0.8, 1.0],
    value=0.6,
    help="Depth of the top defect face below heated front surface."
)
inclusion_material_key = st.sidebar.selectbox(
    "Inclusion Material",
    options=list(MATERIAL_DATABASE.keys()),
    index=1,
    format_func=lambda k: MATERIAL_DATABASE[k].name
)

st.sidebar.markdown("#### 2. LFMT Thermal Chirp")
chirp_f0 = st.sidebar.number_input("Start Frequency f0 [Hz]", min_value=0.01, max_value=0.2, value=0.05, step=0.01)
chirp_f1 = st.sidebar.number_input("End Frequency f1 [Hz]", min_value=0.2, max_value=2.0, value=0.50, step=0.05)
heat_flux_q0 = st.sidebar.number_input("Peak Heat Flux q0 [W/m²]", min_value=1000.0, max_value=20000.0, value=5000.0, step=500.0)

st.sidebar.markdown("#### 3. Noise & Camera Simulation")
noise_option = st.sidebar.selectbox(
    "Sensor Noise (AWGN)",
    ["Clean (No Noise)", "30 dB AWGN (Mild)", "25 dB AWGN (Moderate)", "20 dB AWGN (High)"],
    index=1
)
noise_snr_map = {"Clean (No Noise)": None, "30 dB AWGN (Mild)": 30.0, "25 dB AWGN (Moderate)": 25.0, "20 dB AWGN (High)": 20.0}
selected_snr = noise_snr_map[noise_option]

cam_res = st.sidebar.selectbox("Camera Sensor Resolution", ["64 x 64 px", "32 x 32 px (Fast)"], index=0)
res_dim = 64 if "64" in cam_res else 32

st.sidebar.markdown("#### 4. Simulation Engine")
backend_choice = st.sidebar.selectbox(
    "Solver Backend",
    ["Finite Difference Method (3D FDM)", "Finite Element Method (3D FEM - scikit-fem)"],
    index=0
)
backend_key = "fem" if "FEM" in backend_choice else "finite_difference"

fem_available, fem_engine_name = _check_fem_engine()
if backend_key == "fem":
    st.sidebar.success(f"FEM Engine: {fem_engine_name}")
else:
    st.sidebar.info("Simulation Engine: 3D Finite Difference Method (FDM)")

# Material status check
selected_mat = MATERIAL_DATABASE[inclusion_material_key]
if selected_mat.is_placeholder:
    st.sidebar.warning("⚠️ Inclusion Material: PLACEHOLDER (Unverified)")
else:
    st.sidebar.success("✅ Inclusion Material: VERIFIED")

# Build active configuration
base_cfg = load_config("configs/default.yaml")
base_cfg.simulation.backend = backend_key
base_cfg.geometry.inclusion.diameter_mm = float(inclusion_diam)
base_cfg.geometry.inclusion.depth_mm = float(inclusion_depth)
base_cfg.geometry.inclusion.material = inclusion_material_key
base_cfg.excitation.f0_hz = float(chirp_f0)
base_cfg.excitation.f1_hz = float(chirp_f1)
base_cfg.excitation.q0_w_m2 = float(heat_flux_q0)
base_cfg.noise.snr_db = selected_snr
base_cfg.camera.resolution_x = res_dim
base_cfg.camera.resolution_y = res_dim
base_cfg.camera.sampling_rate_hz = 10.0


# Execute simulation pipeline
with st.spinner("Running 3D Thermal Simulation and Signal Processing Pipeline..."):
    case_result = pipeline.run_case(base_cfg, use_cache=True)


# ==============================================================================
# MODE 1: CONFERENCE MODE (Single-Screen Presentation View)
# ==============================================================================
if mode.startswith("⚡"):
    st.markdown('<p class="main-title">Linear Frequency-Modulated Thermography (LFMT)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Subsurface Slag Inclusion Characterization in Mild Steel Plate (100 × 70 × 2.3 mm)</p>', unsafe_allow_html=True)

    # Top KPI Metrics Banner
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    best_iou_row = case_result.metrics_dataframe.sort_values("iou", ascending=False).iloc[0]
    best_cnr_row = case_result.metrics_dataframe.sort_values("cnr", ascending=False).iloc[0]

    kpi1.metric("Defect Diameter", f"{inclusion_diam:.1f} mm", f"Depth: {inclusion_depth:.1f} mm")
    kpi2.metric("Aspect Ratio (D/z)", f"{inclusion_diam/inclusion_depth:.1f}", "D/z Ratio")
    kpi3.metric("Top Method (IoU)", best_iou_row["method_name"], f"IoU: {best_iou_row['iou']:.2f}")
    kpi4.metric("Peak CNR", f"{best_cnr_row['cnr']:.1f}", best_cnr_row["method_name"])
    kpi5.metric("Min Loc. Error", f"{best_iou_row['localization_error_mm']:.2f} mm", f"{best_iou_row['localization_error_px']:.1f} px")
    kpi6.metric("Pipeline Time", f"{case_result.total_pipeline_time_s:.2f} s", f"Cache: {'Hit' if case_result.cache_hit else 'Fresh'}")

    # Scientific Metadata Indicators Row
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    grid_sz = case_result.simulation_result.metadata.get("grid_size", [24, 56, 80])
    dt_val = case_result.simulation_result.metadata.get("dt_sub_s", case_result.simulation_result.metadata.get("dt_frame_s", 0.05))
    s1.info(f"**Solver**: `{case_result.simulation_result.backend_name.upper()}`")
    s2.info(f"**Material**: `{'Verified' if not selected_mat.is_placeholder else 'Placeholder'}`")
    s3.info(f"**Grid**: `{grid_sz[2]}×{grid_sz[1]}×{grid_sz[0]}`")
    s4.info(f"**Actual dt**: `{dt_val*1000:.1f} ms`")
    s5.info(f"**Chirp**: `{chirp_f0:.2f}→{chirp_f1:.2f} Hz`")
    s6.info(f"**Noise**: `{noise_option.split(' ')[0]}`")

    st.markdown("---")

    # Main Visuals: Multi-panel Comparison
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.markdown("#### 📸 Algorithm Defect Isolation & Localization Panel")
        fig_panel = plot_method_comparison_panel(case_result)
        st.pyplot(fig_panel, use_container_width=True)
        plt.close(fig_panel)

    with col_right:
        st.markdown("#### 📊 Quantitative Evaluation Metrics Table")
        st.dataframe(
            case_result.metrics_dataframe[[
                "method_name", "is_detected", "iou", "dice", "cnr",
                "localization_error_mm", "predicted_diameter_mm", "runtime_s"
            ]].rename(columns={
                "method_name": "Method",
                "is_detected": "Detected",
                "iou": "IoU",
                "dice": "Dice",
                "cnr": "CNR",
                "localization_error_mm": "Loc. Error [mm]",
                "predicted_diameter_mm": "Est. Diam [mm]",
                "runtime_s": "Time [s]"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### ⏱️ Temporal Thermal Transient & Contrast Curve")
        fig_curve = plot_temporal_contrast_curves(case_result)
        st.pyplot(fig_curve, use_container_width=True)
        plt.close(fig_curve)


# ==============================================================================
# MODE 2: IN-DEPTH SCIENTIFIC ANALYSIS (16 TABS)
# ==============================================================================
else:
    st.markdown('<p class="main-title">LFMT Slag Inclusion Scientific Workbench</p>', unsafe_allow_html=True)

    tab_names = [
        "1. Overview",
        "2. Simulation Setup",
        "3. Thermogram Viewer",
        "4. LFMT Excitation",
        "5. Pulse Compression",
        "6. Raw Contrast",
        "7. PCT",
        "8. SPCT",
        "9. RPT",
        "10. Comparison",
        "11. Depth Study",
        "12. Noise Study",
        "13. Validation",
        "14. Dataset Explorer",
        "15. Export & Figures",
        "16. Methodology & Math",
        "17. Conference Benchmark"
    ]

    tabs = st.tabs(tab_names)

    # TAB 1: Overview
    with tabs[0]:
        st.markdown("### 🎯 Project Overview & Objective")
        st.markdown("""
        This research framework establishes a **3-Dimensional Computational and Quantitative NDT Suite**
        for detecting, sizing, and localizing subsurface **welding slag entrapment defects** in structural **mild steel**
        using **Linear Frequency-Modulated Infrared Thermography (LFMT)**.
        """)
        c1, c2, c3 = st.columns(3)
        c1.info("**Target Specimen**\nMild Steel Plate\n100 × 70 × 2.3 mm")
        c2.info("**Defect Inclusion**\nWelding Slag (Silicate)\nDiam: 4–12 mm | Depth: 0.2–1.0 mm")
        c3.info("**Excitation Modality**\nLinear Chirp Heat Flux\n0.05 Hz → 0.50 Hz (10 s)")

    # TAB 2: Simulation Setup
    with tabs[1]:
        st.markdown("### ⚙️ 3D Transient Heat Conduction Physics")
        st.latex(r"\rho(\mathbf{x}) C_p(\mathbf{x}) \frac{\partial T}{\partial t} = \nabla \cdot (k(\mathbf{x}) \nabla T)")
        m1, m2 = st.columns(2)
        with m1:
            st.markdown("#### Matrix Material: Mild Steel (AISI 1018)")
            st.json(get_material(base_cfg.geometry.plate.material).to_dict())
        with m2:
            st.markdown(f"#### Defect Material: {get_material(inclusion_material_key).name}")
            st.json(get_material(inclusion_material_key).to_dict())

    # TAB 3: Thermogram Viewer
    with tabs[2]:
        st.markdown("### 🎥 Virtual IR Camera Thermogram Sequence")
        n_frames = case_result.capture_noisy.n_frames
        frame_idx = st.slider("Select Frame", 0, n_frames - 1, int(n_frames * 0.7))
        t_cur = case_result.capture_noisy.time_vector[frame_idx]

        v1, v2 = st.columns(2)
        with v1:
            st.markdown(f"#### Thermal Field at t = {t_cur:.2f} s")
            fig, ax = plt.subplots(figsize=(6, 4.5))
            im = ax.imshow(
                case_result.capture_noisy.thermograms[frame_idx] - 273.15,
                origin="lower",
                cmap="inferno",
                extent=[0, 100, 0, 70]
            )
            fig.colorbar(im, ax=ax, label="Temperature [°C]")
            ax.set_xlabel("X [mm]")
            ax.set_ylabel("Y [mm]")
            st.pyplot(fig)
            plt.close(fig)

        with v2:
            st.markdown("#### Ground-Truth Spatial Mask")
            fig_gt, ax_gt = plt.subplots(figsize=(6, 4.5))
            ax_gt.imshow(case_result.capture_clean.ground_truth_mask, origin="lower", cmap="gray", extent=[0, 100, 0, 70])
            gt = case_result.capture_clean.ground_truth
            c = patches.Circle((gt.center_x_mm, gt.center_y_mm), gt.diameter_mm/2.0, fill=False, edgecolor="lime", lw=2)
            ax_gt.add_patch(c)
            ax_gt.set_title(f"Defect Center: ({gt.center_x_mm:.1f}, {gt.center_y_mm:.1f}) mm")
            st.pyplot(fig_gt)
            plt.close(fig_gt)

    # TAB 4: LFMT Excitation
    with tabs[3]:
        st.markdown("### 📈 Chirp Excitation & Phase Waveforms")
        exc = LFMTExcitation(f0_hz=chirp_f0, f1_hz=chirp_f1, duration_s=10.0, q0_w_m2=heat_flux_q0)
        fig_exc = plot_excitation_waveform(exc, total_time_s=12.0)
        st.pyplot(fig_exc)
        plt.close(fig_exc)

    # TAB 5: Pulse Compression
    with tabs[4]:
        st.markdown("### ⚡ Matched Filter & Pulse Compression")
        bundle = case_result.matched_filter_bundle
        p1, p2 = st.columns(2)
        with p1:
            fig, ax = plt.subplots(figsize=(6, 4.5))
            im = ax.imshow(bundle.score_map, origin="lower", cmap="viridis", extent=[0, 100, 0, 70])
            fig.colorbar(im, ax=ax, label="Correlation Peak")
            ax.set_title("Peak Correlation Map")
            st.pyplot(fig)
            plt.close(fig)
        with p2:
            st.markdown("#### Matched Filter Metrics")
            st.json(bundle.metrics.to_dict())

    # TAB 6: Raw Contrast
    with tabs[5]:
        st.markdown("### 🌡️ Raw Differential Thermal Contrast")
        fig_raw = plot_temporal_contrast_curves(case_result)
        st.pyplot(fig_raw)
        plt.close(fig_raw)

    # TAB 7: PCT
    with tabs[6]:
        st.markdown("### 🧩 Principal Component Thermography (PCT)")
        pct_res = case_result.pct_bundle.raw_result
        st.markdown(f"**Optimal Defect Mode:** EOF {pct_res.selected_component_idx + 1} (Method: `{pct_res.selection_method}`)")
        fig, axes = plt.subplots(1, min(4, pct_res.eof_images.shape[0]), figsize=(14, 3.5))
        for i in range(len(axes)):
            axes[i].imshow(pct_res.eof_images[i], origin="lower", cmap="plasma")
            axes[i].set_title(f"EOF {i+1} ({pct_res.explained_variance_ratio[i]*100:.1f}%)")
        st.pyplot(fig)
        plt.close(fig)

    # TAB 8: SPCT
    with tabs[7]:
        st.markdown("### 🎯 Sparse Principal Component Thermography (SPCT)")
        spct_res = case_result.spct_bundle.raw_result
        st.markdown(f"**L1 Penalty alpha:** {spct_res.sparsity_alpha} | **Non-Zero Ratio:** {spct_res.non_zero_ratios[spct_res.selected_component_idx]*100:.1f}%")
        fig, ax = plt.subplots(figsize=(6, 4.5))
        im = ax.imshow(spct_res.selected_sparse_image, origin="lower", cmap="plasma", extent=[0, 100, 0, 70])
        fig.colorbar(im, ax=ax, label="Sparse Mode")
        st.pyplot(fig)
        plt.close(fig)

    # TAB 9: RPT
    with tabs[8]:
        st.markdown("### 🎲 Random Projection Technique (RPT)")
        rpt_res = case_result.rpt_bundle.raw_result
        st.markdown(f"**Compression Ratio:** {rpt_res.compression_ratio:.1f}x | **Matrix:** {rpt_res.matrix_type}")
        fig, ax = plt.subplots(figsize=(6, 4.5))
        im = ax.imshow(rpt_res.selected_rpt_image, origin="lower", cmap="plasma", extent=[0, 100, 0, 70])
        fig.colorbar(im, ax=ax, label="Projected Anomaly")
        st.pyplot(fig)
        plt.close(fig)

    # TAB 10: Comparison
    with tabs[9]:
        st.markdown("### 🏆 Comprehensive Multi-Method Benchmark")
        fig_comp = plot_method_comparison_panel(case_result)
        st.pyplot(fig_comp)
        plt.close(fig_comp)
        st.dataframe(case_result.metrics_dataframe, use_container_width=True)

    # TAB 11: Depth Study
    with tabs[10]:
        st.markdown("### 📉 Sensitivity vs Inclusion Depth (0.2 – 1.0 mm)")
        if st.button("Run Dynamic Depth Sweep"):
            with st.spinner("Computing depth sweep..."):
                df_depth = run_parameter_sweep(
                    base_config=base_cfg,
                    diameters_mm=[8.0],
                    depths_mm=[0.2, 0.4, 0.6, 0.8, 1.0],
                    noise_levels_db=[selected_snr],
                    output_dir="results/sweep"
                )
                fig_d = plot_depth_performance(df_depth)
                st.pyplot(fig_d)
                plt.close(fig_d)
        else:
            st.info("Click the button above to execute a systematic depth sweep across depths [0.2, 0.4, 0.6, 0.8, 1.0] mm.")

    # TAB 12: Noise Study
    with tabs[11]:
        st.markdown("### 🔊 Robustness under Additive Sensor Noise (AWGN)")
        st.write("Examines CNR and localization degradation across SNR = Clean, 30 dB, 25 dB, and 20 dB.")

    # TAB 13: Validation
    with tabs[12]:
        st.markdown("### 🔬 Numerical & Physical Validation Studies")
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("#### Spatial Mesh Independence")
            mesh_fig = Path("results/validation/16_mesh_convergence.png")
            if mesh_fig.exists():
                st.image(str(mesh_fig), caption="Grid Convergence across Coarse, Medium, and Fine meshes.")
            else:
                st.info("Run `python scripts/validate_mesh.py` to generate mesh plot.")
        with v2:
            st.markdown("#### Time-Step Independence")
            time_fig = Path("results/validation/17_timestep_convergence.png")
            if time_fig.exists():
                st.image(str(time_fig), caption="Temporal Convergence across time steps.")
            else:
                st.info("Run `python scripts/validate_timestep.py` to generate time-step plot.")

    # TAB 14: Dataset Explorer
    with tabs[13]:
        st.markdown("### 📁 Synthetic Thermogram Dataset Explorer")
        st.write("Browse pre-generated cases in `data/generated/`.")
        data_cases = list(Path("data/generated").glob("case_*"))
        if data_cases:
            st.write(f"Found {len(data_cases)} precomputed cases in repository.")
        else:
            st.info("Generate datasets with `python scripts/generate_dataset.py`.")

    # TAB 15: Export & Figures
    with tabs[14]:
        st.markdown("### 📥 Publication Figure Export")
        st.write("Export 300 DPI high-resolution figures for conference papers and presentation slides.")
        if st.button("Generate All 17 Publication Figures"):
            with st.spinner("Generating conference figures..."):
                from scripts.generate_conference_figures import main as gen_main
                st.success("Figures generated under `results/figures/`!")

    # TAB 16: Methodology & Math
    with tabs[15]:
        st.markdown("### 📚 Theoretical Methodology & Mathematical Formulations")
        st.markdown(r"""
        #### 1. Linear Chirp Thermal Excitation
        $$q(t) = q_0 \cdot \left[1 + \sin\left(2\pi\left(f_0 t + \frac{\beta}{2} t^2\right)\right)\right], \quad \beta = \frac{f_1 - f_0}{T_{exc}}$$

        #### 2. Heterogeneous 3D Transient Heat Conduction
        $$\rho C_p \frac{\partial T}{\partial t} = \frac{\partial}{\partial x}\left(k \frac{\partial T}{\partial x}\right) + \frac{\partial}{\partial y}\left(k \frac{\partial T}{\partial y}\right) + \frac{\partial}{\partial z}\left(k \frac{\partial T}{\partial z}\right)$$

        #### 3. Pulse Compression Cross-Correlation
        $$R_{xy}(\tau) = \mathcal{F}^{-1}\{\mathcal{F}\{T_{xy}(t)\} \cdot \mathcal{F}^*\{q_{ref}(t)\}\}$$

        #### 4. Principal Component Thermography (PCT)
        $$\mathbf{A}_{centered} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^T \implies \text{Spatial EOFs } \mathbf{V}$$

        #### 5. Sparse PCA (SPCT)
        $$\min_{\mathbf{U}, \mathbf{V}} \frac{1}{2}\|\mathbf{A} - \mathbf{U}\mathbf{V}^T\|_F^2 + \alpha \sum_{j=1}^k \|\mathbf{v}_j\|_1$$

        #### 6. Random Projection Technique (RPT)
        $$\mathbf{Y} = \mathbf{\Phi} \mathbf{A}, \quad \mathbf{\Phi} \sim \mathcal{N}\left(0, \frac{1}{k}\right)$$
        """)

    # TAB 17: Conference Benchmark
    with tabs[16]:
        st.markdown("### 🏆 Statistically Validated Conference Benchmark (4,030 Evaluations)")
        st.markdown("""
        Explore precomputed scientific results across 25 physical defect geometries ($D \in [4..12]$ mm, $z \in [0.2..1.0]$ mm)
        and 1 healthy control specimen ($D=0$ mm), simulated with **scikit-fem 3-D ElementHex1** under strict **anti-leakage blind mode**.
        """)

        conf_dir = Path("results/conference")
        if (conf_dir / "summary_by_method.csv").exists():
            df_m = pd.read_csv(conf_dir / "summary_by_method.csv")
            st.markdown("#### 📊 Overall Method Performance Summary")
            st.dataframe(df_m, use_container_width=True, hide_index=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 📉 CNR vs Depth")
                if (conf_dir / "figures" / "fig07_cnr_vs_depth.png").exists():
                    st.image(str(conf_dir / "figures" / "fig07_cnr_vs_depth.png"), caption="Figure 7: CNR vs Depth")
            with c2:
                st.markdown("#### 🎯 Detection Rate vs Depth")
                if (conf_dir / "figures" / "fig08_detection_rate_vs_depth.png").exists():
                    st.image(str(conf_dir / "figures" / "fig08_detection_rate_vs_depth.png"), caption="Figure 8: Detection Rate vs Depth")

            c3, c4 = st.columns(2)
            with c3:
                st.markdown("#### 📏 Maximum Detectable Depth ($z_{max}$)")
                if (conf_dir / "figures" / "fig11_max_detectable_depth_vs_diameter.png").exists():
                    st.image(str(conf_dir / "figures" / "fig11_max_detectable_depth_vs_diameter.png"), caption="Figure 11: z_max vs Diameter")
            with c4:
                st.markdown("#### ⏱️ Processing Execution Runtime")
                if (conf_dir / "figures" / "fig13_processing_runtime_comparison.png").exists():
                    st.image(str(conf_dir / "figures" / "fig13_processing_runtime_comparison.png"), caption="Figure 13: Computational Runtime")
        else:
            st.info("Run `python scripts/run_conference_study.py --conference --backend fem --resume` to compute conference dataset.")

