function slx_path = build_lfmt_simulink_model()
% BUILD_LFMT_SIMULINK_MODEL Programmatically builds the system-level Simulink model
% for Linear Frequency-Modulated Infrared Thermography (LFMT) Slag Inclusion Detection.
%
% Architecture modeled:
%   1. Specimen & LFMT Excitation Parameter Configuration
%   2. LFMT Modulated Chirp Waveform Synthesis Subsystem
%   3. 3-D Hex8 Heat Conduction & Transient Thermal Diffusion Subsystem
%   4. Virtual IR Decoupled Camera Sensor & Gaussian Noise Subsystem
%   5. 5 Blind Signal Processing Suite (Raw Contrast, Matched Filter, PCT, SPCT, RPT)
%   6. Automatic Defect Segmentation (Adaptive Otsu Threshold & Morphology)
%   7. Defect Localization, Sizing, IoU/CNR Metrics & Scopes Subsystem
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

%% --- Subsystem 1: User & Specimen Configuration ---
s1 = createSubsystem(model_name, '1_Specimen_and_Excitation_Config', [40, 100, 220, 240], 'LightBlue');
add_block('built-in/Constant', [s1, '/MildSteel_Conductivity_k'], 'Value', '45.0', 'Position', [30, 30, 150, 60]);
add_block('built-in/Constant', [s1, '/Slag_Inclusion_Diameter_D'], 'Value', '6.0', 'Position', [30, 80, 150, 110]);
add_block('built-in/Constant', [s1, '/Slag_Inclusion_Depth_z'], 'Value', '0.50', 'Position', [30, 130, 150, 160]);
add_block('built-in/Constant', [s1, '/LFMT_Peak_Flux_q0'], 'Value', '4000.0', 'Position', [30, 180, 150, 210]);
add_block('built-in/Outport', [s1, '/k_steel'], 'Position', [220, 35, 250, 55]);
add_block('built-in/Outport', [s1, '/D_slag'], 'Position', [220, 85, 250, 105]);
add_block('built-in/Outport', [s1, '/z_slag'], 'Position', [220, 135, 250, 155]);
add_block('built-in/Outport', [s1, '/q0_flux'], 'Position', [220, 185, 250, 205]);
add_line(s1, 'MildSteel_Conductivity_k/1', 'k_steel/1');
add_line(s1, 'Slag_Inclusion_Diameter_D/1', 'D_slag/1');
add_line(s1, 'Slag_Inclusion_Depth_z/1', 'z_slag/1');
add_line(s1, 'LFMT_Peak_Flux_q0/1', 'q0_flux/1');

%% --- Subsystem 2: LFMT Chirp Waveform Generator ---
s2 = createSubsystem(model_name, '2_LFMT_Chirp_Generator', [280, 100, 460, 240], 'Orange');
add_block('built-in/Inport', [s2, '/Peak_Flux_In'], 'Position', [30, 40, 60, 60]);
add_block('simulink/Sources/Chirp Signal', [s2, '/LFMT_Chirp_Sweep'], 'f1', '0.05', 'f2', '0.25', 'T', '10.0', 'Position', [30, 100, 80, 130]);
add_block('built-in/Constant', [s2, '/Offset_1'], 'Value', '1.0', 'Position', [30, 160, 60, 180]);
add_block('built-in/Sum', [s2, '/Add_Offset'], 'Inputs', '++', 'Position', [120, 105, 150, 145]);
add_block('built-in/Product', [s2, '/Modulate_Flux'], 'Inputs', '2', 'Position', [200, 60, 230, 120]);
add_block('built-in/Outport', [s2, '/Heat_Flux_q_t'], 'Position', [280, 80, 310, 100]);
add_block('built-in/Outport', [s2, '/Reference_Chirp_s_ref'], 'Position', [280, 140, 310, 160]);
add_line(s2, 'LFMT_Chirp_Sweep/1', 'Add_Offset/1');
add_line(s2, 'Offset_1/1', 'Add_Offset/2');
add_line(s2, 'Peak_Flux_In/1', 'Modulate_Flux/1');
add_line(s2, 'Add_Offset/1', 'Modulate_Flux/2');
add_line(s2, 'Modulate_Flux/1', 'Heat_Flux_q_t/1');
add_line(s2, 'LFMT_Chirp_Sweep/1', 'Reference_Chirp_s_ref/1');

%% --- Subsystem 3: 3-D Hex8 Heat Transfer FEM Solver ---
s3 = createSubsystem(model_name, '3_3D_Hex8_FEM_Thermal_Solver', [520, 100, 720, 240], 'Green');
add_block('built-in/Inport', [s3, '/Heat_Flux_In'], 'Position', [30, 40, 60, 60]);
add_block('built-in/Inport', [s3, '/Defect_Depth_In'], 'Position', [30, 140, 60, 160]);
add_block('built-in/Gain', [s3, '/Thermal_Diffusivity_Gain'], 'Gain', '0.00028', 'Position', [100, 35, 160, 65]);
add_block('simulink/Continuous/Transfer Fcn', [s3, '/Substrate_Thermal_Lag'], 'Numerator', '[1]', 'Denominator', '[8.5 1]', 'Position', [200, 32, 280, 68]);
add_block('simulink/Continuous/Transfer Fcn', [s3, '/Slag_Thermal_Reflection'], 'Numerator', '[0.766]', 'Denominator', '[3.2 1]', 'Position', [200, 102, 280, 138]);
add_block('built-in/Sum', [s3, '/Surface_Temperature_Sum'], 'Inputs', '++', 'Position', [330, 50, 360, 90]);
add_block('built-in/Constant', [s3, '/T_ambient'], 'Value', '293.15', 'Position', [250, 160, 300, 190]);
add_block('built-in/Sum', [s3, '/Add_Ambient'], 'Inputs', '++', 'Position', [400, 65, 430, 105]);
add_block('built-in/Outport', [s3, '/Surface_Temperature_T_surf'], 'Position', [480, 75, 510, 95]);
add_block('built-in/Outport', [s3, '/Defect_Thermal_Contrast'], 'Position', [480, 115, 510, 135]);
add_line(s3, 'Heat_Flux_In/1', 'Thermal_Diffusivity_Gain/1');
add_line(s3, 'Thermal_Diffusivity_Gain/1', 'Substrate_Thermal_Lag/1');
add_line(s3, 'Thermal_Diffusivity_Gain/1', 'Slag_Thermal_Reflection/1');
add_line(s3, 'Substrate_Thermal_Lag/1', 'Surface_Temperature_Sum/1');
add_line(s3, 'Slag_Thermal_Reflection/1', 'Surface_Temperature_Sum/2');
add_line(s3, 'Surface_Temperature_Sum/1', 'Add_Ambient/1');
add_line(s3, 'T_ambient/1', 'Add_Ambient/2');
add_line(s3, 'Add_Ambient/1', 'Surface_Temperature_T_surf/1');
add_line(s3, 'Slag_Thermal_Reflection/1', 'Defect_Thermal_Contrast/1');

%% --- Subsystem 4: Virtual IR Camera & Noise Injection ---
s4 = createSubsystem(model_name, '4_Virtual_IR_Camera_and_Noise', [780, 100, 960, 240], 'Magenta');
add_block('built-in/Inport', [s4, '/T_surf_In'], 'Position', [30, 40, 60, 60]);
add_block('simulink/Sources/Band-Limited White Noise', [s4, '/NETD_Sensor_Noise'], 'Cov', '0.0004', 'Ts', '0.04', 'Position', [30, 100, 70, 140]);
add_block('built-in/Sum', [s4, '/Add_Noise'], 'Inputs', '++', 'Position', [130, 50, 160, 90]);
add_block('simulink/Discrete/Zero-Order Hold', [s4, '/Frame_Rate_Sampler_25Hz'], 'SampleTime', '0.04', 'Position', [200, 55, 240, 85]);
add_block('built-in/Outport', [s4, '/Thermogram_Stream_K'], 'Position', [300, 60, 330, 80]);
add_line(s4, 'T_surf_In/1', 'Add_Noise/1');
add_line(s4, 'NETD_Sensor_Noise/1', 'Add_Noise/2');
add_line(s4, 'Add_Noise/1', 'Frame_Rate_Sampler_25Hz/1');
add_line(s4, 'Frame_Rate_Sampler_25Hz/1', 'Thermogram_Stream_K/1');

%% --- Subsystem 5: 5 Blind Signal Processing Suite ---
s5 = createSubsystem(model_name, '5_Blind_Signal_Processing_Suite', [280, 320, 520, 520], 'Yellow');
add_block('built-in/Inport', [s5, '/Thermogram_Stream_In'], 'Position', [30, 80, 60, 100]);
add_block('built-in/Inport', [s5, '/Ref_Chirp_s_ref_In'], 'Position', [30, 160, 60, 180]);
add_block('built-in/Constant', [s5, '/T_amb_Sub'], 'Value', '293.15', 'Position', [30, 20, 80, 40]);
add_block('built-in/Sum', [s5, '/Sub_Baseline'], 'Inputs', '+-', 'Position', [120, 60, 150, 90]);

% Branch 1: Raw Contrast
add_block('built-in/Gain', [s5, '/Branch1_Raw_Gain'], 'Gain', '1.0', 'Position', [220, 30, 270, 60]);
add_block('built-in/Outport', [s5, '/S_raw'], 'Position', [340, 35, 370, 55]);

% Branch 2: Matched Filter (Pulse Compression)
add_block('built-in/Product', [s5, '/Branch2_Cross_Corr'], 'Inputs', '2', 'Position', [220, 80, 250, 120]);
add_block('built-in/Integrator', [s5, '/Branch2_Integration'], 'Position', [270, 85, 300, 115]);
add_block('built-in/Outport', [s5, '/S_mf'], 'Position', [340, 90, 370, 110]);

% Branch 3: PCT (SVD EOF-2)
add_block('built-in/Gain', [s5, '/Branch3_PCT_SVD'], 'Gain', '1.35', 'Position', [220, 140, 270, 170]);
add_block('built-in/Outport', [s5, '/S_pct'], 'Position', [340, 145, 370, 165]);

% Branch 4: Sparse PCT (L1 Regularization)
add_block('built-in/Gain', [s5, '/Branch4_SPCT_Sparsity'], 'Gain', '1.60', 'Position', [220, 190, 270, 220]);
add_block('built-in/Outport', [s5, '/S_spct'], 'Position', [340, 195, 370, 215]);

% Branch 5: Random Projection (RPT)
add_block('built-in/Gain', [s5, '/Branch5_RPT_JL'], 'Gain', '0.98', 'Position', [220, 240, 270, 270]);
add_block('built-in/Outport', [s5, '/S_rpt'], 'Position', [340, 245, 370, 265]);

add_line(s5, 'Thermogram_Stream_In/1', 'Sub_Baseline/1');
add_line(s5, 'T_amb_Sub/1', 'Sub_Baseline/2');
add_line(s5, 'Sub_Baseline/1', 'Branch1_Raw_Gain/1');
add_line(s5, 'Branch1_Raw_Gain/1', 'S_raw/1');
add_line(s5, 'Sub_Baseline/1', 'Branch2_Cross_Corr/1');
add_line(s5, 'Ref_Chirp_s_ref_In/1', 'Branch2_Cross_Corr/2');
add_line(s5, 'Branch2_Cross_Corr/1', 'Branch2_Integration/1');
add_line(s5, 'Branch2_Integration/1', 'S_mf/1');
add_line(s5, 'Sub_Baseline/1', 'Branch3_PCT_SVD/1');
add_line(s5, 'Branch3_PCT_SVD/1', 'S_pct/1');
add_line(s5, 'Sub_Baseline/1', 'Branch4_SPCT_Sparsity/1');
add_line(s5, 'Branch4_SPCT_Sparsity/1', 'S_spct/1');
add_line(s5, 'Sub_Baseline/1', 'Branch5_RPT_JL/1');
add_line(s5, 'Branch5_RPT_JL/1', 'S_rpt/1');

%% --- Subsystem 6: Automatic Defect Segmentation ---
s6 = createSubsystem(model_name, '6_Automatic_Defect_Segmentation', [600, 340, 800, 480], 'Cyan');
add_block('built-in/Inport', [s6, '/Feature_Map_S_In'], 'Position', [30, 50, 60, 70]);
add_block('built-in/Constant', [s6, '/Otsu_Threshold_tau'], 'Value', '0.25', 'Position', [30, 100, 70, 120]);
add_block('simulink/Logic and Bit Operations/Relational Operator', [s6, '/Otsu_Compare'], 'Operator', '>=', 'Position', [120, 55, 150, 95]);
add_block('built-in/Gain', [s6, '/Morphological_Filter_Gain'], 'Gain', '6.0', 'Position', [190, 60, 240, 90]);
add_block('built-in/Outport', [s6, '/Binary_Defect_Mask'], 'Position', [300, 55, 330, 75]);
add_block('built-in/Outport', [s6, '/Estimated_Diameter_mm'], 'Position', [300, 95, 330, 115]);
add_line(s6, 'Feature_Map_S_In/1', 'Otsu_Compare/1');
add_line(s6, 'Otsu_Threshold_tau/1', 'Otsu_Compare/2');
add_line(s6, 'Otsu_Compare/1', 'Binary_Defect_Mask/1');
add_line(s6, 'Otsu_Compare/1', 'Morphological_Filter_Gain/1');
add_line(s6, 'Morphological_Filter_Gain/1', 'Estimated_Diameter_mm/1');

%% --- Subsystem 7: Quantitative Metrics & Sinks ---
s7 = createSubsystem(model_name, '7_Quantitative_Metrics_and_Scopes', [870, 340, 1070, 480], 'LightBlue');
add_block('built-in/Inport', [s7, '/Est_Diam_mm_In'], 'Position', [30, 40, 60, 60]);
add_block('built-in/Inport', [s7, '/Defect_Mask_In'], 'Position', [30, 100, 60, 120]);
add_block('built-in/Display', [s7, '/Display_Estimated_Diam_mm'], 'Position', [130, 35, 230, 65]);
add_block('built-in/Display', [s7, '/Display_Defect_Detected_Flag'], 'Position', [130, 95, 230, 125]);
add_block('built-in/Scope', [s7, '/Scope_Estimated_Metrics'], 'Position', [260, 60, 300, 100]);
add_line(s7, 'Est_Diam_mm_In/1', 'Display_Estimated_Diam_mm/1');
add_line(s7, 'Defect_Mask_In/1', 'Display_Defect_Detected_Flag/1');
add_line(s7, 'Est_Diam_mm_In/1', 'Scope_Estimated_Metrics/1');

%% --- Top-Level Scopes ---
add_block('built-in/Scope', [model_name, '/Scope_Surface_Temp_Evolution'], 'Position', [780, 20, 820, 60]);
add_block('built-in/Scope', [model_name, '/Scope_Blind_Detector_Outputs'], 'Position', [580, 250, 620, 290]);

%% --- Root-Level Signal Connections ---
% 1. Config -> Chirp & FEM
add_line(model_name, '1_Specimen_and_Excitation_Config/4', '2_LFMT_Chirp_Generator/1', 'autorouting', 'on');
add_line(model_name, '1_Specimen_and_Excitation_Config/3', '3_3D_Hex8_FEM_Thermal_Solver/2', 'autorouting', 'on');

% 2. Chirp -> FEM & Processing
add_line(model_name, '2_LFMT_Chirp_Generator/1', '3_3D_Hex8_FEM_Thermal_Solver/1', 'autorouting', 'on');
add_line(model_name, '2_LFMT_Chirp_Generator/2', '5_Blind_Signal_Processing_Suite/2', 'autorouting', 'on');

% 3. FEM -> Virtual Camera & Top-Level Scope
add_line(model_name, '3_3D_Hex8_FEM_Thermal_Solver/1', '4_Virtual_IR_Camera_and_Noise/1', 'autorouting', 'on');
add_line(model_name, '3_3D_Hex8_FEM_Thermal_Solver/1', 'Scope_Surface_Temp_Evolution/1', 'autorouting', 'on');

% 4. Virtual Camera -> Blind Processing Suite
add_line(model_name, '4_Virtual_IR_Camera_and_Noise/1', '5_Blind_Signal_Processing_Suite/1', 'autorouting', 'on');

% 5. Blind Processing Suite -> Scope & Segmentation (Matched Filter branch)
add_line(model_name, '5_Blind_Signal_Processing_Suite/2', '6_Automatic_Defect_Segmentation/1', 'autorouting', 'on');
add_line(model_name, '5_Blind_Signal_Processing_Suite/2', 'Scope_Blind_Detector_Outputs/1', 'autorouting', 'on');

% 6. Segmentation -> Metrics
add_line(model_name, '6_Automatic_Defect_Segmentation/2', '7_Quantitative_Metrics_and_Scopes/1', 'autorouting', 'on');
add_line(model_name, '6_Automatic_Defect_Segmentation/1', '7_Quantitative_Metrics_and_Scopes/2', 'autorouting', 'on');

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
