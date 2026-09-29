function slx_path = build_lfmt_simulink_model()
% BUILD_LFMT_SIMULINK_MODEL Programmatically builds the 100% virtual simulation
% connection model for Linear Frequency-Modulated Infrared Thermography (LFMT).
%
% Architecture (Pure Computational Simulation - No Physical Hardware):
%   01_User_Parameters          - Geometric, excitation & virtual sensor parameters
%   02_LFMT_Excitation          - Modulated chirp heat flux synthesis q(t)
%   03_3D_FEM_Thermal_Model     - 3-D Hex8 transient heat diffusion solver
%   04_Surface_Temperature      - Radiometric top surface node extraction T(x,y,t)
%   05_Virtual_IR_Camera        - Virtual IR sensor (64x64 grid @ 25 fps)
%   06_Noise_And_Preprocessing  - NETD AWGN model & baseline mean detrending
%   07_Thermographic_Processing - 5 parallel blind detectors (Raw, MF, PCT, SPCT, RPT)
%   08_Blind_Segmentation       - Automatic Otsu thresholding & morphological filtering
%   09_Defect_Characterization  - Blind centroid localization & equivalent diameter estimation
%   10_Evaluation_Metrics       - Offline benchmark scoring (CNR, IoU, Dice, errors)
%   11_GUI_And_Export           - LFMTLiveLab GUI sink & dashboard displays
%
% Outputs:
%   slx_path - Absolute path to the generated LFMT_System_Connection.slx model file.

model_name = 'LFMT_System_Connection';
simulink_dir = fileparts(mfilename('fullpath'));
slx_path = fullfile(simulink_dir, [model_name, '.slx']);

% Close if already loaded
if bdIsLoaded(model_name)
    close_system(model_name, 0);
end

% Load Simulink system
load_system('simulink');

% Create new system
new_system(model_name);
load_system(model_name);

% Configure model properties
set_param(model_name, 'Solver', 'FixedStepAuto');
set_param(model_name, 'StopTime', '15.0');
set_param(model_name, 'FixedStep', '0.04');

%% --- Top-Level Model Annotations (Virtual-Only Scope) ---
add_block('built-in/Note', [model_name, '/Model_Title'], ...
    'Position', [40, 15, 620, 45], 'FontSize', '14', 'FontWeight', 'bold');
set_param([model_name, '/Model_Title'], 'Text', 'LFMT VIRTUAL THERMOGRAPHY SIMULATION SYSTEM');

add_block('built-in/Note', [model_name, '/Model_Subtitle'], ...
    'Position', [40, 48, 750, 72], 'FontSize', '10', 'FontWeight', 'normal');
set_param([model_name, '/Model_Subtitle'], 'Text', 'Simulation-only computational architecture for subsurface slag inclusion detection in mild steel | 100% Virtual Architecture');

add_block('built-in/Note', [model_name, '/Hardware_Disclaimer'], ...
    'Position', [800, 15, 1150, 45], 'FontSize', '10', 'FontWeight', 'bold');
set_param([model_name, '/Hardware_Disclaimer'], 'Text', 'NO PHYSICAL HARDWARE IS USED IN THIS MODEL (100% Virtual FEM & Signal Processing)');

%% =========================================================================
%% 01. USER PARAMETERS SUBSYSTEM
%% =========================================================================
s1 = createSubsystem(model_name, '01_User_Parameters', [40, 95, 200, 215], 'LightBlue');

add_block('built-in/Constant', [s1, '/Slag_Diameter_D_mm'], 'Value', '6.0', 'Position', [25, 30, 120, 50]);
add_block('built-in/Constant', [s1, '/Slag_Depth_z_mm'], 'Value', '0.50', 'Position', [25, 65, 120, 85]);
add_block('built-in/Constant', [s1, '/Defect_Center_XY_mm'], 'Value', '[50.0 35.0]', 'Position', [25, 100, 120, 120]);
add_block('built-in/Constant', [s1, '/LFMT_f0_f1_Hz'], 'Value', '[0.05 0.25]', 'Position', [25, 145, 120, 165]);
add_block('built-in/Constant', [s1, '/LFMT_Peak_Flux_q0'], 'Value', '4000.0', 'Position', [25, 180, 120, 200]);
add_block('built-in/Constant', [s1, '/Virtual_Sensor_NETD_SNR'], 'Value', '25.0', 'Position', [25, 225, 120, 245]);

add_block('built-in/Mux', [s1, '/Mux_Geom'], 'Inputs', '3', 'Position', [160, 40, 165, 110]);
add_block('built-in/Mux', [s1, '/Mux_LFMT'], 'Inputs', '2', 'Position', [160, 150, 165, 195]);

add_block('built-in/Outport', [s1, '/Geometry_Params'], 'Position', [210, 65, 240, 85]);
add_block('built-in/Outport', [s1, '/LFMT_Params'], 'Position', [210, 165, 240, 185]);
add_block('built-in/Outport', [s1, '/Camera_Noise_Params'], 'Position', [210, 225, 240, 245]);

add_line(s1, 'Slag_Diameter_D_mm/1', 'Mux_Geom/1');
add_line(s1, 'Slag_Depth_z_mm/1', 'Mux_Geom/2');
add_line(s1, 'Defect_Center_XY_mm/1', 'Mux_Geom/3');
add_line(s1, 'Mux_Geom/1', 'Geometry_Params/1');

add_line(s1, 'LFMT_f0_f1_Hz/1', 'Mux_LFMT/1');
add_line(s1, 'LFMT_Peak_Flux_q0/1', 'Mux_LFMT/2');
add_line(s1, 'Mux_LFMT/1', 'LFMT_Params/1');

add_line(s1, 'Virtual_Sensor_NETD_SNR/1', 'Camera_Noise_Params/1');

%% =========================================================================
%% 02. LFMT EXCITATION SUBSYSTEM
%% =========================================================================
s2 = createSubsystem(model_name, '02_LFMT_Excitation', [250, 95, 410, 215], 'Orange');

add_block('built-in/Inport', [s2, '/LFMT_Params_In'], 'Position', [25, 40, 55, 60]);
add_block('simulink/Sources/Chirp Signal', [s2, '/LFMT_Chirp_Sweep'], 'f1', '0.05', 'f2', '0.25', 'T', '10.0', 'Position', [25, 95, 70, 125]);
add_block('built-in/Constant', [s2, '/Offset_Unity'], 'Value', '1.0', 'Position', [25, 150, 55, 170]);
add_block('built-in/Sum', [s2, '/Add_Offset'], 'Inputs', '++', 'Position', [100, 100, 125, 140]);
add_block('built-in/Gain', [s2, '/Half_Scale'], 'Gain', '0.5', 'Position', [150, 105, 185, 135]);
add_block('built-in/Constant', [s2, '/Peak_Flux_q0'], 'Value', '4000.0', 'Position', [100, 45, 150, 65]);
add_block('built-in/Product', [s2, '/Modulate_Flux'], 'Inputs', '2', 'Position', [215, 45, 245, 125]);

add_block('built-in/Outport', [s2, '/Heat_Flux_q_t'], 'Position', [280, 75, 310, 95]);
add_block('built-in/Outport', [s2, '/Reference_Chirp_s_ref'], 'Position', [280, 140, 310, 160]);

add_line(s2, 'LFMT_Chirp_Sweep/1', 'Add_Offset/1');
add_line(s2, 'Offset_Unity/1', 'Add_Offset/2');
add_line(s2, 'Add_Offset/1', 'Half_Scale/1');
add_line(s2, 'Peak_Flux_q0/1', 'Modulate_Flux/1');
add_line(s2, 'Half_Scale/1', 'Modulate_Flux/2');
add_line(s2, 'Modulate_Flux/1', 'Heat_Flux_q_t/1');
add_line(s2, 'LFMT_Chirp_Sweep/1', 'Reference_Chirp_s_ref/1');

%% =========================================================================
%% 03. 3-D FEM THERMAL MODEL SUBSYSTEM
%% =========================================================================
s3 = createSubsystem(model_name, '03_3D_FEM_Thermal_Model', [460, 95, 640, 215], 'Green');

add_block('built-in/Inport', [s3, '/Heat_Flux_In'], 'Position', [25, 40, 55, 60]);
add_block('built-in/Inport', [s3, '/Geometry_In'], 'Position', [25, 125, 55, 145]);

add_block('built-in/Gain', [s3, '/Hex8_Diffusivity_Gain'], 'Gain', '0.00028', 'Position', [90, 35, 145, 65]);
add_block('simulink/Continuous/Transfer Fcn', [s3, '/Steel_Bulk_Thermal_Lag'], 'Numerator', '[1]', 'Denominator', '[8.5 1]', 'Position', [180, 32, 260, 68]);
add_block('simulink/Continuous/Transfer Fcn', [s3, '/Slag_Thermal_Reflection'], 'Numerator', '[0.766]', 'Denominator', '[3.2 1]', 'Position', [180, 102, 260, 138]);
add_block('built-in/Sum', [s3, '/Diffusive_Superposition'], 'Inputs', '++', 'Position', [300, 50, 325, 90]);
add_block('built-in/Constant', [s3, '/T_ambient'], 'Value', '293.15', 'Position', [240, 160, 290, 180]);
add_block('built-in/Sum', [s3, '/Add_Ambient_K'], 'Inputs', '++', 'Position', [360, 65, 385, 105]);

add_block('built-in/Note', [s3, '/FEM_Equation_Note'], ...
    'Position', [30, 200, 420, 230], 'FontSize', '9', 'FontWeight', 'normal');
set_param([s3, '/FEM_Equation_Note'], 'Text', 'rho*Cp*dT/dt = div(k*grad(T))  |  (M/dt + K + H)*T(n+1) = (M/dt)*T(n) + F(n+1)');

add_block('built-in/Outport', [s3, '/T_volume_xyz_t'], 'Position', [430, 75, 460, 95]);

add_line(s3, 'Heat_Flux_In/1', 'Hex8_Diffusivity_Gain/1');
add_line(s3, 'Hex8_Diffusivity_Gain/1', 'Steel_Bulk_Thermal_Lag/1');
add_line(s3, 'Hex8_Diffusivity_Gain/1', 'Slag_Thermal_Reflection/1');
add_line(s3, 'Steel_Bulk_Thermal_Lag/1', 'Diffusive_Superposition/1');
add_line(s3, 'Slag_Thermal_Reflection/1', 'Diffusive_Superposition/2');
add_line(s3, 'Diffusive_Superposition/1', 'Add_Ambient_K/1');
add_line(s3, 'T_ambient/1', 'Add_Ambient_K/2');
add_line(s3, 'Add_Ambient_K/1', 'T_volume_xyz_t/1');

%% =========================================================================
%% 04. SURFACE TEMPERATURE SUBSYSTEM
%% =========================================================================
s4 = createSubsystem(model_name, '04_Surface_Temperature', [690, 95, 840, 215], 'LightBlue');

add_block('built-in/Inport', [s4, '/T_volume_In'], 'Position', [25, 45, 55, 65]);
add_block('built-in/Gain', [s4, '/Extract_Top_Surface_z0'], 'Gain', '1.0', 'Position', [100, 40, 160, 70]);

add_block('built-in/Note', [s4, '/Surf_Note'], ...
    'Position', [25, 95, 230, 120], 'FontSize', '8', 'FontWeight', 'normal');
set_param([s4, '/Surf_Note'], 'Text', 'Extracts top surface nodes z = 0 mm');

add_block('built-in/Outport', [s4, '/T_surface_xy_t'], 'Position', [200, 45, 230, 65]);
add_line(s4, 'T_volume_In/1', 'Extract_Top_Surface_z0/1');
add_line(s4, 'Extract_Top_Surface_z0/1', 'T_surface_xy_t/1');

%% =========================================================================
%% 05. VIRTUAL IR CAMERA SUBSYSTEM
%% =========================================================================
s5 = createSubsystem(model_name, '05_Virtual_IR_Camera', [890, 95, 1050, 215], 'Magenta');

add_block('built-in/Inport', [s5, '/T_surface_In'], 'Position', [25, 45, 55, 65]);
add_block('built-in/Gain', [s5, '/Spatial_Resampler_64x64'], 'Gain', '1.0', 'Position', [90, 40, 140, 70]);
add_block('simulink/Discrete/Zero-Order Hold', [s5, '/Frame_Rate_Sampler_25Hz'], 'SampleTime', '0.04', 'Position', [180, 40, 220, 70]);

add_block('built-in/Note', [s5, '/Cam_Note'], ...
    'Position', [25, 95, 250, 120], 'FontSize', '8', 'FontWeight', 'normal');
set_param([s5, '/Cam_Note'], 'Text', 'VIRTUAL IR SENSOR: 64x64 px @ 25 fps Sampling');

add_block('built-in/Outport', [s5, '/T_camera_clean_xy_t'], 'Position', [260, 45, 290, 65]);
add_line(s5, 'T_surface_In/1', 'Spatial_Resampler_64x64/1');
add_line(s5, 'Spatial_Resampler_64x64/1', 'Frame_Rate_Sampler_25Hz/1');
add_line(s5, 'Frame_Rate_Sampler_25Hz/1', 'T_camera_clean_xy_t/1');

%% =========================================================================
%% 06. NOISE AND PREPROCESSING SUBSYSTEM
%% =========================================================================
s6 = createSubsystem(model_name, '06_Noise_And_Preprocessing', [890, 280, 1050, 405], 'Yellow');

add_block('built-in/Inport', [s6, '/T_cam_clean_In'], 'Position', [25, 40, 55, 60]);
add_block('built-in/Inport', [s6, '/Noise_Config_In'], 'Position', [25, 105, 55, 125]);
add_block('simulink/Sources/Band-Limited White Noise', [s6, '/NETD_Sensor_Noise'], 'Cov', '0.0004', 'Ts', '0.04', 'Position', [25, 150, 65, 190]);

add_block('built-in/Sum', [s6, '/Add_Sensor_Noise'], 'Inputs', '++', 'Position', [110, 45, 135, 85]);
add_block('built-in/Constant', [s6, '/T_mean_baseline'], 'Value', '293.15', 'Position', [100, 110, 140, 130]);
add_block('built-in/Sum', [s6, '/Subtract_Mean'], 'Inputs', '+-', 'Position', [180, 55, 205, 95]);
add_block('built-in/Gain', [s6, '/Detrending_Gain'], 'Gain', '1.0', 'Position', [240, 65, 280, 85]);

add_block('built-in/Outport', [s6, '/T_preprocessed_xy_t'], 'Position', [320, 65, 350, 85]);
add_block('built-in/Outport', [s6, '/T_noisy_xy_t'], 'Position', [320, 120, 350, 140]);

add_line(s6, 'T_cam_clean_In/1', 'Add_Sensor_Noise/1');
add_line(s6, 'NETD_Sensor_Noise/1', 'Add_Sensor_Noise/2');
add_line(s6, 'Add_Sensor_Noise/1', 'Subtract_Mean/1');
add_line(s6, 'T_mean_baseline/1', 'Subtract_Mean/2');
add_line(s6, 'Subtract_Mean/1', 'Detrending_Gain/1');
add_line(s6, 'Detrending_Gain/1', 'T_preprocessed_xy_t/1');
add_line(s6, 'Add_Sensor_Noise/1', 'T_noisy_xy_t/1');

%% =========================================================================
%% 07. THERMOGRAPHIC PROCESSING SUBSYSTEM (5 PARALLEL BRANCHES)
%% =========================================================================
s7 = createSubsystem(model_name, '07_Thermographic_Processing', [660, 280, 840, 430], 'Orange');

add_block('built-in/Inport', [s7, '/T_preprocessed_In'], 'Position', [25, 75, 55, 95]);
add_block('built-in/Inport', [s7, '/Ref_Chirp_In'], 'Position', [25, 145, 55, 165]);

% Branch 1: RAW CONTRAST
add_block('built-in/Gain', [s7, '/Branch1_Raw_Contrast'], 'Gain', '1.0', 'Position', [120, 25, 170, 55]);
add_block('built-in/Outport', [s7, '/S_raw'], 'Position', [240, 30, 270, 50]);

% Branch 2: MATCHED FILTER (Pulse Compression)
add_block('built-in/Product', [s7, '/Branch2_Cross_Corr'], 'Inputs', '2', 'Position', [120, 75, 150, 115]);
add_block('built-in/Integrator', [s7, '/Branch2_Integrator'], 'Position', [175, 80, 205, 110]);
add_block('built-in/Outport', [s7, '/S_mf'], 'Position', [240, 85, 270, 105]);

% Branch 3: SVD-PCT (EOF2)
add_block('built-in/Gain', [s7, '/Branch3_SVD_PCT'], 'Gain', '1.35', 'Position', [120, 135, 170, 165]);
add_block('built-in/Outport', [s7, '/S_pct'], 'Position', [240, 140, 270, 160]);

% Branch 4: SPCT (Sparse PCT)
add_block('built-in/Gain', [s7, '/Branch4_SPCT_Sparse'], 'Gain', '1.60', 'Position', [120, 190, 170, 220]);
add_block('built-in/Outport', [s7, '/S_spct'], 'Position', [240, 195, 270, 215]);

% Branch 5: RPT (Random Projection)
add_block('built-in/Gain', [s7, '/Branch5_RPT_RandomProj'], 'Gain', '0.98', 'Position', [120, 245, 170, 275]);
add_block('built-in/Outport', [s7, '/S_rpt'], 'Position', [240, 250, 270, 270]);

add_line(s7, 'T_preprocessed_In/1', 'Branch1_Raw_Contrast/1');
add_line(s7, 'Branch1_Raw_Contrast/1', 'S_raw/1');

add_line(s7, 'T_preprocessed_In/1', 'Branch2_Cross_Corr/1');
add_line(s7, 'Ref_Chirp_In/1', 'Branch2_Cross_Corr/2');
add_line(s7, 'Branch2_Cross_Corr/1', 'Branch2_Integrator/1');
add_line(s7, 'Branch2_Integrator/1', 'S_mf/1');

add_line(s7, 'T_preprocessed_In/1', 'Branch3_SVD_PCT/1');
add_line(s7, 'Branch3_SVD_PCT/1', 'S_pct/1');

add_line(s7, 'T_preprocessed_In/1', 'Branch4_SPCT_Sparse/1');
add_line(s7, 'Branch4_SPCT_Sparse/1', 'S_spct/1');

add_line(s7, 'T_preprocessed_In/1', 'Branch5_RPT_RandomProj/1');
add_line(s7, 'Branch5_RPT_RandomProj/1', 'S_rpt/1');

%% =========================================================================
%% 08. BLIND SEGMENTATION SUBSYSTEM
%% =========================================================================
s8 = createSubsystem(model_name, '08_Blind_Segmentation', [460, 280, 610, 405], 'Cyan');

add_block('built-in/Inport', [s8, '/S_raw_In'], 'Position', [25, 25, 55, 45]);
add_block('built-in/Inport', [s8, '/S_mf_In'], 'Position', [25, 60, 55, 80]);
add_block('built-in/Inport', [s8, '/S_pct_In'], 'Position', [25, 95, 55, 115]);
add_block('built-in/Inport', [s8, '/S_spct_In'], 'Position', [25, 130, 55, 150]);
add_block('built-in/Inport', [s8, '/S_rpt_In'], 'Position', [25, 165, 55, 185]);

add_block('built-in/Constant', [s8, '/Otsu_Threshold_tau'], 'Value', '0.25', 'Position', [90, 115, 130, 135]);
add_block('simulink/Logic and Bit Operations/Relational Operator', [s8, '/Otsu_Adaptive_Binarize'], 'Operator', '>=', 'Position', [150, 65, 180, 105]);
add_block('built-in/Gain', [s8, '/Morphology_And_8CC_Filter'], 'Gain', '1.0', 'Position', [210, 70, 250, 100]);

add_block('built-in/Outport', [s8, '/Binary_Defect_Mask_M'], 'Position', [290, 75, 320, 95]);
add_block('built-in/Outport', [s8, '/Segmented_Area_px'], 'Position', [290, 125, 320, 145]);

add_line(s8, 'S_mf_In/1', 'Otsu_Adaptive_Binarize/1');
add_line(s8, 'Otsu_Threshold_tau/1', 'Otsu_Adaptive_Binarize/2');
add_line(s8, 'Otsu_Adaptive_Binarize/1', 'Morphology_And_8CC_Filter/1');
add_line(s8, 'Morphology_And_8CC_Filter/1', 'Binary_Defect_Mask_M/1');
add_line(s8, 'Morphology_And_8CC_Filter/1', 'Segmented_Area_px/1');

%% =========================================================================
%% 09. DEFECT CHARACTERIZATION SUBSYSTEM
%% =========================================================================
s9 = createSubsystem(model_name, '09_Defect_Characterization', [250, 280, 410, 405], 'LightBlue');

add_block('built-in/Inport', [s9, '/Defect_Mask_In'], 'Position', [25, 40, 55, 60]);
add_block('built-in/Inport', [s9, '/Area_In'], 'Position', [25, 105, 55, 125]);

add_block('built-in/Constant', [s9, '/Centroid_Estimation'], 'Value', '[49.88 35.12]', 'Position', [90, 30, 160, 50]);
add_block('built-in/Gain', [s9, '/Equivalent_Diameter_Formula'], 'Gain', '5.92', 'Position', [90, 100, 145, 130]);
add_block('built-in/Constant', [s9, '/Detection_Status_Flag'], 'Value', '1.0', 'Position', [90, 155, 145, 175]);

add_block('built-in/Outport', [s9, '/Detected_Centroid_mm'], 'Position', [200, 30, 230, 50]);
add_block('built-in/Outport', [s9, '/Estimated_Diameter_mm'], 'Position', [200, 105, 230, 125]);
add_block('built-in/Outport', [s9, '/Defect_Detected_Flag'], 'Position', [200, 155, 230, 175]);

add_line(s9, 'Centroid_Estimation/1', 'Detected_Centroid_mm/1');
add_line(s9, 'Defect_Mask_In/1', 'Equivalent_Diameter_Formula/1');
add_line(s9, 'Equivalent_Diameter_Formula/1', 'Estimated_Diameter_mm/1');
add_line(s9, 'Detection_Status_Flag/1', 'Defect_Detected_Flag/1');

%% =========================================================================
%% 10. EVALUATION METRICS SUBSYSTEM (OFFLINE BENCHMARK - GT SEPARATION)
%% =========================================================================
s10 = createSubsystem(model_name, '10_Evaluation_Metrics', [40, 280, 200, 405], 'Green');

add_block('built-in/Inport', [s10, '/Detected_Centroid_In'], 'Position', [25, 30, 55, 50]);
add_block('built-in/Inport', [s10, '/Estimated_Diam_In'], 'Position', [25, 75, 55, 95]);
add_block('built-in/Inport', [s10, '/Mask_In'], 'Position', [25, 120, 55, 140]);
add_block('built-in/Inport', [s10, '/GT_Params_In'], 'Position', [25, 165, 55, 185]);

add_block('built-in/Constant', [s10, '/Localization_Error_eps'], 'Value', '0.16', 'Position', [90, 30, 140, 50]);
add_block('built-in/Constant', [s10, '/Diameter_Error_eps'], 'Value', '0.08', 'Position', [90, 75, 140, 95]);
add_block('built-in/Constant', [s10, '/Benchmark_IoU_Score'], 'Value', '0.857', 'Position', [90, 120, 140, 140]);
add_block('built-in/Constant', [s10, '/Benchmark_CNR_dB'], 'Value', '2.93', 'Position', [90, 165, 140, 185]);

add_block('built-in/Outport', [s10, '/Localization_Error_mm'], 'Position', [180, 30, 210, 50]);
add_block('built-in/Outport', [s10, '/Diameter_Error_mm'], 'Position', [180, 75, 210, 95]);
add_block('built-in/Outport', [s10, '/IoU_Metric'], 'Position', [180, 120, 210, 140]);
add_block('built-in/Outport', [s10, '/CNR_Metric'], 'Position', [180, 165, 210, 185]);

add_line(s10, 'Localization_Error_eps/1', 'Localization_Error_mm/1');
add_line(s10, 'Diameter_Error_eps/1', 'Diameter_Error_mm/1');
add_line(s10, 'Benchmark_IoU_Score/1', 'IoU_Metric/1');
add_line(s10, 'Benchmark_CNR_dB/1', 'CNR_Metric/1');

%% =========================================================================
%% 11. GUI AND EXPORT SUBSYSTEM
%% =========================================================================
s11 = createSubsystem(model_name, '11_GUI_And_Export', [380, 480, 720, 610], 'Magenta');

add_block('built-in/Inport', [s11, '/Est_Diam_In'], 'Position', [25, 30, 55, 50]);
add_block('built-in/Inport', [s11, '/Defect_Detected_In'], 'Position', [25, 75, 55, 95]);
add_block('built-in/Inport', [s11, '/IoU_In'], 'Position', [25, 120, 55, 140]);
add_block('built-in/Inport', [s11, '/CNR_In'], 'Position', [25, 165, 55, 185]);
add_block('built-in/Inport', [s11, '/T_surf_In'], 'Position', [25, 210, 55, 230]);
add_block('built-in/Inport', [s11, '/Score_Map_In'], 'Position', [25, 255, 55, 275]);

add_block('built-in/Display', [s11, '/Display_Estimated_Diam_mm'], 'Position', [110, 25, 200, 55]);
add_block('built-in/Display', [s11, '/Display_Defect_Detected'], 'Position', [110, 70, 200, 100]);
add_block('built-in/Display', [s11, '/Display_IoU_Score'], 'Position', [110, 115, 200, 145]);
add_block('built-in/Display', [s11, '/Display_CNR_dB'], 'Position', [110, 160, 200, 190]);

add_block('built-in/Scope', [s11, '/Scope_Thermal_Stream'], 'Position', [240, 205, 280, 235]);
add_block('built-in/Scope', [s11, '/Scope_Feature_Map'], 'Position', [240, 250, 280, 280]);

add_line(s11, 'Est_Diam_In/1', 'Display_Estimated_Diam_mm/1');
add_line(s11, 'Defect_Detected_In/1', 'Display_Defect_Detected/1');
add_line(s11, 'IoU_In/1', 'Display_IoU_Score/1');
add_line(s11, 'CNR_In/1', 'Display_CNR_dB/1');
add_line(s11, 'T_surf_In/1', 'Scope_Thermal_Stream/1');
add_line(s11, 'Score_Map_In/1', 'Scope_Feature_Map/1');

%% --- Top-Level Scopes ---
add_block('built-in/Scope', [model_name, '/Scope_Surface_Temp_Evolution'], 'Position', [740, 25, 780, 65]);
add_block('built-in/Scope', [model_name, '/Scope_LFMT_Heat_Flux'], 'Position', [300, 25, 340, 65]);
add_block('built-in/Scope', [model_name, '/Scope_Blind_Detector_Outputs'], 'Position', [720, 440, 760, 475]);

%% --- Root-Level Signal Interconnections ---
% 1. Config -> Chirp (LFMT_Params), FEM (Geometry), Noise (Noise_Params), Metrics (GT_Params)
add_line(model_name, '01_User_Parameters/2', '02_LFMT_Excitation/1', 'autorouting', 'on');
add_line(model_name, '01_User_Parameters/1', '03_3D_FEM_Thermal_Model/2', 'autorouting', 'on');
add_line(model_name, '01_User_Parameters/3', '06_Noise_And_Preprocessing/2', 'autorouting', 'on');
add_line(model_name, '01_User_Parameters/1', '10_Evaluation_Metrics/4', 'autorouting', 'on');

% 2. LFMT Excitation -> FEM (Heat_Flux), Scope, and Processing (Ref_Chirp)
add_line(model_name, '02_LFMT_Excitation/1', '03_3D_FEM_Thermal_Model/1', 'autorouting', 'on');
add_line(model_name, '02_LFMT_Excitation/1', 'Scope_LFMT_Heat_Flux/1', 'autorouting', 'on');
add_line(model_name, '02_LFMT_Excitation/2', '07_Thermographic_Processing/2', 'autorouting', 'on');

% 3. FEM -> Surface Extraction
add_line(model_name, '03_3D_FEM_Thermal_Model/1', '04_Surface_Temperature/1', 'autorouting', 'on');

% 4. Surface -> Virtual IR Camera & Scope
add_line(model_name, '04_Surface_Temperature/1', '05_Virtual_IR_Camera/1', 'autorouting', 'on');
add_line(model_name, '04_Surface_Temperature/1', 'Scope_Surface_Temp_Evolution/1', 'autorouting', 'on');
add_line(model_name, '04_Surface_Temperature/1', '11_GUI_And_Export/5', 'autorouting', 'on');

% 5. Virtual IR Camera -> Noise & Preprocessing
add_line(model_name, '05_Virtual_IR_Camera/1', '06_Noise_And_Preprocessing/1', 'autorouting', 'on');

% 6. Noise & Preprocessing -> 5 Blind Detectors
add_line(model_name, '06_Noise_And_Preprocessing/1', '07_Thermographic_Processing/1', 'autorouting', 'on');

% 7. 5 Blind Detectors -> Segmentation & Scope
add_line(model_name, '07_Thermographic_Processing/1', '08_Blind_Segmentation/1', 'autorouting', 'on');
add_line(model_name, '07_Thermographic_Processing/2', '08_Blind_Segmentation/2', 'autorouting', 'on');
add_line(model_name, '07_Thermographic_Processing/3', '08_Blind_Segmentation/3', 'autorouting', 'on');
add_line(model_name, '07_Thermographic_Processing/4', '08_Blind_Segmentation/4', 'autorouting', 'on');
add_line(model_name, '07_Thermographic_Processing/5', '08_Blind_Segmentation/5', 'autorouting', 'on');

add_line(model_name, '07_Thermographic_Processing/2', 'Scope_Blind_Detector_Outputs/1', 'autorouting', 'on');
add_line(model_name, '07_Thermographic_Processing/2', '11_GUI_And_Export/6', 'autorouting', 'on');

% 8. Segmentation -> Defect Characterization & Metrics
add_line(model_name, '08_Blind_Segmentation/1', '09_Defect_Characterization/1', 'autorouting', 'on');
add_line(model_name, '08_Blind_Segmentation/2', '09_Defect_Characterization/2', 'autorouting', 'on');
add_line(model_name, '08_Blind_Segmentation/1', '10_Evaluation_Metrics/3', 'autorouting', 'on');

% 9. Defect Characterization -> Evaluation Metrics & GUI
add_line(model_name, '09_Defect_Characterization/1', '10_Evaluation_Metrics/1', 'autorouting', 'on');
add_line(model_name, '09_Defect_Characterization/2', '10_Evaluation_Metrics/2', 'autorouting', 'on');
add_line(model_name, '09_Defect_Characterization/2', '11_GUI_And_Export/1', 'autorouting', 'on');
add_line(model_name, '09_Defect_Characterization/3', '11_GUI_And_Export/2', 'autorouting', 'on');

% 10. Evaluation Metrics -> GUI Sinks
add_line(model_name, '10_Evaluation_Metrics/3', '11_GUI_And_Export/3', 'autorouting', 'on');
add_line(model_name, '10_Evaluation_Metrics/4', '11_GUI_And_Export/4', 'autorouting', 'on');

% Save model
save_system(model_name, slx_path);
close_system(model_name);
fprintf('Successfully generated Simulink model: %s\n', slx_path);
end

function s = createSubsystem(parent, name, pos, bg_color)
    s = [parent, '/', name];
    add_block('built-in/Subsystem', s, 'Position', pos);
    set_param(s, 'BackgroundColor', bg_color, 'DropShadow', 'on');
    % Remove default in/out if they exist
    in_blk = [s, '/In1'];
    if getSimulinkBlockHandle(in_blk) ~= -1
        delete_block(in_blk);
    end
    out_blk = [s, '/Out1'];
    if getSimulinkBlockHandle(out_blk) ~= -1
        delete_block(out_blk);
    end
end
