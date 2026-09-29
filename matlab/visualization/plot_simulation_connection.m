function varargout = plot_simulation_connection(cfg, varargin)
% PLOT_SIMULATION_CONNECTION Generates publication-quality circuit/block-style
% connection diagrams for Linear Frequency-Modulated Infrared Thermography (LFMT).
%
% Visualizes the complete scientific simulation connection, physical experimental
% rig layout, and 3-D specimen cross-section heat transfer mechanics.
%
% Syntax:
%   plot_simulation_connection()
%   plot_simulation_connection(cfg)
%   plot_simulation_connection(cfg, 'Target', 'all')
%   [h_sim, h_phys, h_spec] = plot_simulation_connection(...)
%
% Parameters:
%   cfg       - Optional struct or JSON path with simulation parameters.
%   'Target'  - 'all' (default), 'simulation', 'physical', or 'specimen'
%   'Export'  - true (default: saves 300-DPI PNG figures to results/figures)
%   'Visible' - 'on' (default) or 'off'
%
% Project:
%   Linear Frequency-Modulated Infrared Thermography for Subsurface Slag
%   Inclusion Detection in Mild Steel

if nargin < 1 || isempty(cfg)
    cfg = default_config();
elseif ischar(cfg) || isstring(cfg)
    cfg = lfmt.loadConfig(char(cfg));
end

if ~isfield(cfg.plate, 'has_defect')
    cfg.plate.has_defect = ~isempty(cfg.defects) && length(cfg.defects) > 0 && (cfg.defects(1).diameter_mm > 0);
end
if cfg.plate.has_defect && ~isfield(cfg.plate, 'defect') && ~isempty(cfg.defects)
    cfg.plate.defect = cfg.defects(1);
end
if ~isfield(cfg.plate, 'defect') && ~cfg.plate.has_defect
    cfg.plate.defect = struct('diameter_mm', 0, 'depth_mm', 0, 'thickness_mm', 0, 'center_x_mm', 0, 'center_y_mm', 0);
end

% Parse optional parameters
p = inputParser;
addParameter(p, 'Target', 'all', @(x) any(validatestring(x, {'all', 'simulation', 'physical', 'specimen'})));
addParameter(p, 'Export', true, @islogical);
addParameter(p, 'Visible', 'on', @(x) ischar(x) || isstring(x));
parse(p, varargin{:});

target_mode = lower(p.Results.Target);
do_export = p.Results.Export;
vis_mode = char(p.Results.Visible);

root_dir = fileparts(fileparts(mfilename('fullpath')));
fig_dir = fullfile(root_dir, 'results', 'figures');
if ~exist(fig_dir, 'dir')
    mkdir(fig_dir);
end

h_sim = [];
h_phys = [];
h_spec = [];

%% 1. Simulation Connection Pipeline Diagram
if strcmp(target_mode, 'all') || strcmp(target_mode, 'simulation')
    h_sim = renderSimulationPipelineFigure(cfg, vis_mode);
    if do_export
        export_path = fullfile(fig_dir, 'simulation_connection.png');
        exportgraphics(h_sim, export_path, 'Resolution', 300);
        savefig(h_sim, fullfile(fig_dir, 'simulation_connection.fig'));
        fprintf('Saved simulation connection diagram: %s\n', export_path);
    end
end

%% 2. Proposed Physical Experimental Connection Diagram
if strcmp(target_mode, 'all') || strcmp(target_mode, 'physical')
    h_phys = renderPhysicalConnectionFigure(cfg, vis_mode);
    if do_export
        export_path = fullfile(fig_dir, 'physical_connection.png');
        exportgraphics(h_phys, export_path, 'Resolution', 300);
        savefig(h_phys, fullfile(fig_dir, 'physical_connection.fig'));
        fprintf('Saved physical connection diagram: %s\n', export_path);
    end
end

%% 3. 3-D Specimen Heat Transfer Connection Schematic
if strcmp(target_mode, 'all') || strcmp(target_mode, 'specimen')
    h_spec = renderSpecimenSchematicFigure(cfg, vis_mode);
    if do_export
        export_path = fullfile(fig_dir, 'specimen_connection.png');
        exportgraphics(h_spec, export_path, 'Resolution', 300);
        savefig(h_spec, fullfile(fig_dir, 'specimen_connection.fig'));
        fprintf('Saved specimen connection schematic: %s\n', export_path);
    end
end

if strcmp(target_mode, 'physical')
    if nargout > 0, varargout{1} = h_phys; end
elseif strcmp(target_mode, 'specimen')
    if nargout > 0, varargout{1} = h_spec; end
elseif strcmp(target_mode, 'simulation')
    if nargout > 0, varargout{1} = h_sim; end
else % 'all'
    if nargout == 1
        varargout{1} = [h_sim, h_phys, h_spec];
    else
        if nargout > 0, varargout{1} = h_sim; end
        if nargout > 1, varargout{2} = h_phys; end
        if nargout > 2, varargout{3} = h_spec; end
    end
end

end

%% =========================================================================
%% SUB-ROUTINE 1: Render Simulation Computational Pipeline
%% =========================================================================
function fig = renderSimulationPipelineFigure(cfg, vis_mode)
    fig = figure('Name', 'LFMT Complete Simulation Connection Architecture', ...
        'NumberTitle', 'off', 'Color', [0.07, 0.08, 0.11], ...
        'Position', [50, 40, 1400, 880], 'Visible', vis_mode);
    
    ax = axes(fig, 'Position', [0, 0, 1, 1], 'Color', [0.07, 0.08, 0.11]);
    hold(ax, 'on');
    xlim(ax, [0, 100]);
    ylim(ax, [0, 100]);
    axis(ax, 'off');
    
    % Color Palette
    col_bg_card    = [0.12, 0.14, 0.19];
    col_border     = [0.25, 0.35, 0.50];
    col_accent_cyan= [0.15, 0.75, 0.95];
    col_accent_gold= [0.95, 0.80, 0.25];
    col_accent_grn = [0.25, 0.85, 0.45];
    col_accent_red = [0.95, 0.35, 0.35];
    col_accent_purp= [0.75, 0.45, 0.95];
    col_arrow      = [0.45, 0.65, 0.85];
    
    % 1. Header Banner
    drawRoundedBox(ax, 2, 92, 96, 6.5, [0.10, 0.12, 0.17], [0.3, 0.45, 0.65], 1.5);
    text(ax, 50, 96.2, 'LINEAR FREQUENCY-MODULATED INFRARED THERMOGRAPHY (LFMT) - SIMULATION CONNECTION ARCHITECTURE', ...
        'Color', col_accent_cyan, 'FontSize', 12, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 93.4, 'Complete End-to-End Scientific Pipeline: Excitation -> 3-D Hex8 FEM -> Decoupled IR Camera -> 5 Blind Detectors -> Automated Segmentation -> Verification Audit', ...
        'Color', [0.75, 0.82, 0.90], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % --- COLUMN 1: Forward Simulation Pipeline (x in [3, 47]) ---
    
    % Safe field helpers
    if isfield(cfg.excitation, 'observation_time_s')
        tobs = cfg.excitation.observation_time_s;
    elseif isfield(cfg.simulation, 'total_time_s')
        tobs = cfg.simulation.total_time_s;
    else
        tobs = cfg.excitation.duration_s;
    end
    
    if isfield(cfg.camera, 'frame_rate_hz')
        fps = cfg.camera.frame_rate_hz;
    elseif isfield(cfg.camera, 'sampling_rate_hz')
        fps = cfg.camera.sampling_rate_hz;
    else
        fps = 25.0;
    end
    
    if isfield(cfg.simulation, 'dt_s')
        dt_val = cfg.simulation.dt_s;
    else
        dt_val = 0.04;
    end
    
    if isfield(cfg.simulation, 'solver_type')
        solver_type_str = upper(cfg.simulation.solver_type);
    else
        solver_type_str = 'FEM';
    end

    % Stage 1: User Input Parameters
    if cfg.plate.has_defect
        def_str = sprintf('Slag Cyl: D=%.1f mm, z=%.2f mm, h=%.2f mm, Loc=(%.1f, %.1f) mm', ...
            cfg.plate.defect.diameter_mm, cfg.plate.defect.depth_mm, cfg.plate.defect.thickness_mm, ...
            cfg.plate.defect.center_x_mm, cfg.plate.defect.center_y_mm);
    else
        def_str = 'Healthy Control Plate (No Subsurface Inclusion)';
    end
    snr_str = sprintf('SNR = %s, Seed = %d', string(cfg.camera.noise_snr_db), cfg.camera.noise_seed);
    if isempty(cfg.camera.noise_snr_db) || isinf(cfg.camera.noise_snr_db), snr_str = 'Clean (Inf dB, sigma=0 K)'; end
    
    drawStageBlock(ax, 3, 76, 44, 13.5, 1, 'USER INPUT PARAMETERS', col_accent_cyan, col_bg_card, col_border, ...
        {sprintf('Plate Size: %.1f x %.1f x %.2f mm (Mild Steel)', cfg.plate.length_mm, cfg.plate.width_mm, cfg.plate.thickness_mm); ...
         sprintf('Defect Config: %s', def_str); ...
         sprintf('Camera Setup: %d x %d px @ %.1f Hz | %s', cfg.camera.cam_nx, cfg.camera.cam_ny, fps, snr_str); ...
         sprintf('Solver Config: Type=%s, dt=%.3f s, Texc=%.1f s, Tobs=%.1f s', solver_type_str, dt_val, cfg.excitation.duration_s, tobs)}, ...
        'Output: Structured Config Vector ->');
    
    drawLabeledArrow(ax, 25, 76, 25, 66, 'Geometry & Thermal Properties', col_arrow);
    
    % Stage 2: LFMT Excitation Generator
    drawStageBlock(ax, 3, 53.5, 44, 12.5, 2, 'LFMT CHIRP GENERATOR', col_accent_gold, col_bg_card, col_border, ...
        {sprintf('Sweep Band: f0 = %.3f Hz -> f1 = %.3f Hz (Sweep Rate = %.4f Hz/s)', cfg.excitation.f0_hz, cfg.excitation.f1_hz, (cfg.excitation.f1_hz - cfg.excitation.f0_hz)/cfg.excitation.duration_s); ...
         sprintf('Flux Amplitude: q0 = %.0f W/m^2 | Duration Texc = %.1f s', cfg.excitation.q0_w_m2, cfg.excitation.duration_s); ...
         'Waveform Equation: q(t) = q0 [1 + sin(2*pi*(f0*t + ((f1-f0)/(2*Texc))*t^2))]  (t <= Texc)'; ...
         'Post-Excitation Phase: q(t) = 0.0 W/m^2  (t > Texc, Thermal Cooling Window)'}, ...
        'Output: Modulated Flux Waveform q(t) [W/m^2]');
    
    drawLabeledArrow(ax, 25, 53.5, 25, 44.5, 'Excitation Heat Flux q(t) [W/m^2]', col_arrow);
    
    % Stage 3: Heat Conduction & 3-D Hex8 FEM Solver
    drawStageBlock(ax, 3, 22.5, 44, 22, 3, '3-D HEXAHEDRAL FEM TRANSIENT SOLVER', col_accent_grn, col_bg_card, col_border, ...
        {'Continuum PDE: rho(x) * Cp(x) * dT/dt = div( k(x) * grad(T) )'; ...
         'Substrate: Mild Steel (k = 45 W/m-K, rho = 7850 kg/m^3, Cp = 460 J/kg-K)'; ...
         'Inclusion: Slag (k = 1.20 W/m-K, rho = 2800 kg/m^3, Cp = 850 J/kg-K, Effusivity Contrast = 7.54x)'; ...
         'Boundary Conditions: -k*(dT/dn)|z=0 = q(t) - h*(T - Tamb),  -k*(dT/dn)|other = -h*(T - Tamb)'; ...
         'Discrete System: M*(dT/dt) + (K + Mconv)*T = F(t) + Famb'; ...
         'Implicit Integration: ((1/dt)*M + K + Mconv)*T^(n+1) = (1/dt)*M*T^(n) + F^(n+1) + Famb'; ...
         'Pre-factorized Cholesky: dA = decomposition(A, ''chol'', ''lower'')'}, ...
        'Output: 3-D Temperature Tensor T(x,y,z,t) [K]');
    
    drawLabeledArrow(ax, 25, 22.5, 25, 14.5, 'Surface Field Extraction T(x,y,0,t)', col_arrow);
    
    % Stage 4: Virtual IR Camera & Noise Injection
    n_cam_frames = round(tobs * fps) + 1;
    drawStageBlock(ax, 3, 3, 44, 11.5, 4, 'VIRTUAL IR CAMERA & NOISE INJECTION', col_accent_purp, col_bg_card, col_border, ...
        {sprintf('Spatial Interpolation: Decoupled camera sensor (%d x %d pixels) via griddedInterpolant', cfg.camera.cam_nx, cfg.camera.cam_ny); ...
         sprintf('Temporal Sampling: Frame Rate fs = %.1f Hz (dt_cam = %.3f s, %d Frames)', fps, 1.0/fps, n_cam_frames); ...
         'Noise Injection: T_noisy(x,y,t) = T(x,y,t) + N(0, sigma^2),  sigma = RMS(T - T_bar) / 10^(SNR/20)'; ...
         'Ground Truth Mask Isolation: GT defect mask strictly isolated for evaluation only (zero leakage)'}, ...
        'Output: Thermogram Video Cube [Nt x Ny x Nx]');
    
    % Transition connector from Stage 4 (left) to Stage 5 (right)
    drawHorizontalConnector(ax, 47, 8.5, 53, 80, 'Thermogram Cube [Nt x Ny x Nx]', col_accent_cyan);
    
    % --- COLUMN 2: Blind Signal Processing & Evaluation Pipeline (x in [53, 97]) ---
    
    % Stage 5: 5 Blind Signal Processing Methods
    drawStageBlock(ax, 53, 56.5, 44, 27, 5, 'BLIND SIGNAL PROCESSING SUITE (5 METHODS)', col_accent_gold, col_bg_card, col_border, ...
        {'Branch 1: RAW CONTRAST - Delta T_raw(x,y) = max_t T(x,y,t) - T(x,y,0)'; ...
         'Branch 2: MATCHED FILTER - R_xs(tau) = integral T_tilde(x,y,t) * s_ref(t+tau) dt (Pulse Compression SNR Boost)'; ...
         'Branch 3: PRINCIPAL COMPONENT THERMOGRAPHY (SVD-PCT) - A = U * Sigma * V^T, Eigen-mode EOF-2 Extraction'; ...
         'Branch 4: SPARSE PCT (SPCT) - min ||A - U*V^T||_F^2 + lambda*||V||_1 (L1 Regularized Defect Sparsity)'; ...
         'Branch 5: RANDOM PROJECTION (RPT) - Y = (1/sqrt(k)) * R * A, R_ij ~ N(0,1) (Johnson-Lindenstrauss)'; ...
         'Blindness Guarantee: Methods process blind raw thermograms with ZERO knowledge of defect position/size.'}, ...
        'Output: 5 Normalized 2-D Feature Maps S_m(x,y) in [0, 1]');
    
    drawLabeledArrow(ax, 75, 56.5, 75, 48.5, 'Normalized Feature Score Maps S_m(x,y)', col_arrow);
    
    % Stage 6: Automatic Defect Segmentation
    drawStageBlock(ax, 53, 34, 44, 14.5, 6, 'AUTOMATIC DEFECT SEGMENTATION', col_accent_cyan, col_bg_card, col_border, ...
        {'Adaptive Thresholding: Otsu automatic global threshold tau_m minimizing intra-class variance'; ...
         'Binarization: B_raw(x,y) = S_m(x,y) > tau_m'; ...
         'Morphological Post-processing: Morphological Opening (disk r=2 px) + Closing (disk r=3 px)'; ...
         'Connected Components: 8-connectivity labeling, filtering components with Area < A_min'; ...
         'Candidate Selection: Highest average feature saliency component selected as defect candidate'}, ...
        'Output: Segmented Binary Defect Masks B_m(x,y)');
    
    drawLabeledArrow(ax, 75, 34, 75, 26, 'Binary Masks B_m(x,y) & Region Props', col_arrow);
    
    % Stage 7: Defect Estimation & Quantitative Evaluation
    drawStageBlock(ax, 53, 3, 44, 23, 7, 'QUANTITATIVE EVALUATION & SCIENTIFIC AUDIT', col_accent_grn, col_bg_card, col_border, ...
        {'Defect Centroid Localization: (xc_hat, yc_hat) = (mean(x), mean(y)) | Error eps_loc = ||(xc_hat - x_gt, yc_hat - y_gt)||_2'; ...
         'Equivalent Diameter Estimation: D_hat = 2 * sqrt(Area / pi) | Error eps_diam = |D_hat - D_gt|'; ...
         'Contrast-to-Noise Ratio: CNR = |mu_defect - mu_sound| / sigma_sound (Sound = Periphery 10% Margin)'; ...
         'Intersection-over-Union: IoU = |B_m & G_gt| / |B_m | G_gt|,   Dice = 2*|B_m & G_gt| / (|B_m| + |G_gt|)'; ...
         'Detection Rule: is_detected = (IoU >= 0.20) & (eps_loc <= 5.0 mm)'; ...
         'Execution Profiling: Algorithmic wall-clock runtime (s) and throughput ranking'}, ...
        'Final Deliverable: CSV Summary Tables, Visual Dashboards & Audit Package');
end

%% =========================================================================
%% SUB-ROUTINE 2: Render Proposed Physical Experimental Connection
%% =========================================================================
function fig = renderPhysicalConnectionFigure(cfg, vis_mode)
    fig = figure('Name', 'LFMT Proposed Physical Experimental Architecture', ...
        'NumberTitle', 'off', 'Color', [0.07, 0.08, 0.11], ...
        'Position', [80, 60, 1300, 840], 'Visible', vis_mode);
    
    ax = axes(fig, 'Position', [0, 0, 1, 1], 'Color', [0.07, 0.08, 0.11]);
    hold(ax, 'on');
    xlim(ax, [0, 100]);
    ylim(ax, [0, 100]);
    axis(ax, 'off');
    
    col_bg_card    = [0.12, 0.14, 0.19];
    col_border     = [0.25, 0.35, 0.50];
    col_accent_cyan= [0.15, 0.75, 0.95];
    col_accent_gold= [0.95, 0.80, 0.25];
    col_accent_grn = [0.25, 0.85, 0.45];
    col_accent_red = [0.95, 0.35, 0.35];
    col_accent_purp= [0.75, 0.45, 0.95];
    col_arrow      = [0.45, 0.65, 0.85];
    
    % Safe field helpers
    if isfield(cfg.camera, 'frame_rate_hz')
        fps = cfg.camera.frame_rate_hz;
    elseif isfield(cfg.camera, 'sampling_rate_hz')
        fps = cfg.camera.sampling_rate_hz;
    else
        fps = 25.0;
    end
    
    % 1. Header Banner
    drawRoundedBox(ax, 3, 91, 94, 7, [0.10, 0.12, 0.17], [0.3, 0.45, 0.65], 1.5);
    text(ax, 50, 95.5, 'PROPOSED PHYSICAL EXPERIMENTAL CONNECTION (HARDWARE REFERENCE ARCHITECTURE)', ...
        'Color', col_accent_cyan, 'FontSize', 12, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 92.5, 'Simulation-to-Experiment Correspondence for Linear Frequency-Modulated Infrared Thermography NDT&E', ...
        'Color', [0.75, 0.82, 0.90], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % 2. Computer / MATLAB Workstation (Top Left)
    drawRoundedBox(ax, 5, 68, 26, 18, col_bg_card, col_accent_cyan, 1.5);
    text(ax, 18, 83.5, 'MATLAB / PC WORKSTATION', 'Color', col_accent_cyan, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 7, 79, '- LFMT Chirp Synthesis Engine', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 7, 76, sprintf('- f0 = %.2f Hz -> f1 = %.2f Hz', cfg.excitation.f0_hz, cfg.excitation.f1_hz), 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 7, 73, '- Synchronized DAC Output (0-5V)', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 7, 70, '- Radiometric Frame Acquisition', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Arrow 1: PC -> Power Amplifier
    drawLabeledArrow(ax, 31, 77, 41, 77, 'Analog Modulation Signal s(t)', col_arrow);
    
    % 3. Power Amplifier / Controller
    drawRoundedBox(ax, 41, 68, 22, 18, col_bg_card, col_accent_gold, 1.5);
    text(ax, 52, 83.5, 'POWER CONTROLLER', 'Color', col_accent_gold, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 43, 79, '- Linear Power Amplifier', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 43, 76, '- Current / Voltage Regulation', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 43, 73, '- Solid-State Relay / Dimmer', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 43, 70, sprintf('- Rated Power: ~%.0f W', cfg.excitation.q0_w_m2 * 0.1 * 0.07 * 2), 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Arrow 2: Power Amp -> Halogen Source
    drawLabeledArrow(ax, 63, 77, 73, 77, 'Modulated AC Current I(t)', col_arrow);
    
    % 4. Optical Excitation Heat Source
    drawRoundedBox(ax, 73, 68, 22, 18, col_bg_card, col_accent_red, 1.5);
    text(ax, 84, 83.5, 'OPTICAL HEAT SOURCE', 'Color', col_accent_red, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 75, 79, '- Twin Halogen Lamp Array (2 kW)', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 75, 76, '- Parabolic Reflectors', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 75, 73, '- Uniform Spatial Flux Profile', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 75, 70, sprintf('- Peak Flux: q0 = %.0f W/m^2', cfg.excitation.q0_w_m2), 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Arrow 3: Heat Source -> Steel Specimen
    drawLabeledArrow(ax, 84, 68, 84, 52, 'Heat Flux q(t) [W/m^2]', col_accent_red);
    
    % 5. Specimen Block (Center)
    drawRoundedBox(ax, 20, 36, 68, 16, [0.14, 0.17, 0.23], [0.35, 0.55, 0.80], 2.0);
    text(ax, 54, 49, 'MILD STEEL SPECIMEN WITH SUB-SURFACE SLAG INCLUSION', 'Color', [0.95, 0.95, 1.0], 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 23, 44, sprintf('- Dimensions: %.1f x %.1f x %.2f mm (Lx x Ly x Lz)', cfg.plate.length_mm, cfg.plate.width_mm, cfg.plate.thickness_mm), 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    if cfg.plate.has_defect
        text(ax, 23, 41, sprintf('- Defect: Slag Inclusion D = %.1f mm, Depth z = %.2f mm, Thickness h = %.2f mm', ...
            cfg.plate.defect.diameter_mm, cfg.plate.defect.depth_mm, cfg.plate.defect.thickness_mm), 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    else
        text(ax, 23, 41, '- Specimen: Healthy Homogeneous Mild Steel Reference Plate', 'Color', col_accent_grn, 'FontSize', 8.5, 'Interpreter', 'none');
    end
    text(ax, 23, 38, '- Thermal Contrast: Steel (e ~ 12,740 J/m^2-K-s^0.5) vs Slag (e ~ 1,689 J/m^2-K-s^0.5) -> Reflection R ~ +0.766', 'Color', [0.75, 0.8, 0.88], 'FontSize', 8.0, 'Interpreter', 'none');
    
    % Small visual defect marker inside plate block
    if cfg.plate.has_defect
        drawRoundedBox(ax, 70, 38, 12, 5, [0.3, 0.1, 0.1], [1.0, 0.3, 0.3], 1.2);
        text(ax, 76, 40.5, 'SLAG DEFECT', 'Color', [1.0, 0.8, 0.8], 'FontSize', 7.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    end
    
    % Arrow 4: Specimen -> IR Camera
    drawLabeledArrow(ax, 38, 36, 38, 24, 'Thermal Infrared Emission [3-5 um]', col_accent_gold);
    
    % 6. Infrared Camera Block
    drawRoundedBox(ax, 25, 8, 26, 16, col_bg_card, col_accent_purp, 1.5);
    text(ax, 38, 21.5, 'INFRARED CAMERA', 'Color', col_accent_purp, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 27, 17.5, '- Radiometric Thermal Camera', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 27, 14.5, sprintf('- Spatial Resolution: %d x %d px', cfg.camera.cam_nx, cfg.camera.cam_ny), 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 27, 11.5, sprintf('- Sampling Rate: fs = %.1f Hz', fps), 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Arrow 5: IR Camera -> Processing Engine
    drawLabeledArrow(ax, 51, 16, 61, 16, 'Digital Video Stream [GigE]', col_arrow);
    
    % 7. MATLAB Signal Processing & Defect Detection (Bottom Right)
    drawRoundedBox(ax, 61, 8, 33, 16, col_bg_card, col_accent_grn, 1.5);
    text(ax, 77.5, 21.5, 'NDT&E PROCESSING ENGINE', 'Color', col_accent_grn, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 63, 17.5, '- 5 Blind Detectors: Raw, MF, PCT, SPCT, RPT', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 63, 14.5, '- Automatic Otsu + Morphological Segmentation', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 63, 11.5, '- Defect Sizing (D), Centroid (x,y), CNR & IoU', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Bottom Prominent Note
    text(ax, 50, 3.2, 'NOTE: The current project repository is 100% computational and verified via 3-D Hex8 FEM numerical simulation.', ...
        'Color', [0.95, 0.75, 0.35], 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 1.2, 'This diagram describes the proposed physical NDT&E inspection rig design for future hardware validation.', ...
        'Color', [0.70, 0.75, 0.85], 'FontSize', 8.0, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
end

%% =========================================================================
%% SUB-ROUTINE 3: Render 3-D Specimen Cross-Section Connection Schematic
%% =========================================================================
function fig = renderSpecimenSchematicFigure(cfg, vis_mode)
    fig = figure('Name', 'LFMT 3-D Specimen Heat Transfer Connection Schematic', ...
        'NumberTitle', 'off', 'Color', [0.07, 0.08, 0.11], ...
        'Position', [100, 80, 1200, 780], 'Visible', vis_mode);
    
    ax = axes(fig, 'Position', [0, 0, 1, 1], 'Color', [0.07, 0.08, 0.11]);
    hold(ax, 'on');
    xlim(ax, [0, 100]);
    ylim(ax, [0, 100]);
    axis(ax, 'off');
    
    col_accent_cyan= [0.15, 0.75, 0.95];
    col_accent_gold= [0.95, 0.80, 0.25];
    col_accent_grn = [0.25, 0.85, 0.45];
    col_accent_red = [0.95, 0.35, 0.35];
    
    % Header
    drawRoundedBox(ax, 4, 91, 92, 7, [0.10, 0.12, 0.17], [0.3, 0.45, 0.65], 1.5);
    text(ax, 50, 95.5, '3-D SPECIMEN CROSS-SECTION & HEAT TRANSFER MECHANICS SCHEMATIC', ...
        'Color', col_accent_cyan, 'FontSize', 12, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 92.5, 'Mild Steel Plate with Embedded Slag Inclusion Under Modulated Thermal-Wave Excitation (z-axis depth view)', ...
        'Color', [0.75, 0.82, 0.90], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Top: IR Camera Icon & Heat Flux Arrows
    % Camera Box
    drawRoundedBox(ax, 40, 76, 20, 10, [0.15, 0.18, 0.26], [0.5, 0.4, 0.9], 1.5);
    text(ax, 50, 82.5, 'VIRTUAL IR CAMERA', 'Color', [0.8, 0.7, 1.0], 'FontSize', 9.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 78.5, sprintf('Resolution: %d x %d px', cfg.camera.cam_nx, cfg.camera.cam_ny), 'Color', [0.75, 0.8, 0.9], 'FontSize', 8, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % IR Ray Observation Arrows
    drawLabeledArrow(ax, 46, 60, 46, 75, '', [0.95, 0.85, 0.3]);
    drawLabeledArrow(ax, 50, 60, 50, 75, 'Thermal Emission eps * sigma * T^4', [0.95, 0.85, 0.3]);
    drawLabeledArrow(ax, 54, 60, 54, 75, '', [0.95, 0.85, 0.3]);
    
    % Excitation Flux Arrows (Red, pointing down to front surface)
    for x_arr = [18, 26, 34, 66, 74, 82]
        drawLabeledArrow(ax, x_arr, 72, x_arr, 60, '', col_accent_red);
    end
    text(ax, 26, 74, 'Incident Flux q(t)', 'Color', col_accent_red, 'FontSize', 9, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 74, 74, 'Incident Flux q(t)', 'Color', col_accent_red, 'FontSize', 9, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Main Mild Steel Plate Cross Section (x in [10, 90], y in [24, 60])
    rectangle(ax, 'Position', [10, 24, 80, 36], 'Curvature', [0.02, 0.04], ...
        'FaceColor', [0.18, 0.22, 0.30], 'EdgeColor', [0.40, 0.60, 0.85], 'LineWidth', 2.0);
    
    % Front Surface (z = 0) Label
    text(ax, 12, 62, 'FRONT SURFACE (z = 0): Irradiated by q(t), Convection -h*(T - Tamb)', ...
        'Color', [0.3, 0.85, 1.0], 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    
    % Back Surface (z = Lz) Label
    text(ax, 12, 21.5, sprintf('BACK SURFACE (z = Lz = %.2f mm): Convection -h*(T - Tamb)', cfg.plate.thickness_mm), ...
        'Color', [0.7, 0.75, 0.85], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Substrate Material Text
    text(ax, 15, 34, sprintf('MILD STEEL SUBSTRATE\nk = 45.0 W/m-K\nrho = 7850 kg/m^3\nCp = 460 J/kg-K\ne ~ 12,740 J/m^2-K-s^0.5'), ...
        'Color', [0.65, 0.75, 0.88], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Slag Defect Cylinder Patch (Centered at x = 50, depth = z)
    if cfg.plate.has_defect
        d = cfg.plate.defect;
        % Defect box
        rectangle(ax, 'Position', [40, 38, 20, 16], 'Curvature', [0.08, 0.08], ...
            'FaceColor', [0.45, 0.15, 0.15], 'EdgeColor', [1.0, 0.3, 0.3], 'LineWidth', 2.0);
        text(ax, 50, 48, 'SLAG INCLUSION', 'Color', [1.0, 0.9, 0.9], 'FontSize', 9.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
        text(ax, 50, 44, sprintf('D = %.1f mm | Depth z = %.2f mm', d.diameter_mm, d.depth_mm), 'Color', [1.0, 0.85, 0.85], 'FontSize', 8.5, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
        text(ax, 50, 40.5, 'k=1.20 W/m-K, rho=2800, Cp=850', 'Color', [0.95, 0.75, 0.75], 'FontSize', 8.0, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
        
        % Dimension Arrows for Defect Depth & Diameter
        line(ax, [62, 62], [60, 54], 'Color', col_accent_gold, 'LineWidth', 1.5);
        text(ax, 64, 57, sprintf('Depth z = %.2f mm', d.depth_mm), 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
        
        line(ax, [40, 60], [35, 35], 'Color', col_accent_gold, 'LineWidth', 1.5);
        text(ax, 50, 32.5, sprintf('Diameter D = %.1f mm', d.diameter_mm), 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
        
        % Thermal Wave Reflection Callout
        drawLabeledArrow(ax, 50, 57, 50, 59.5, 'Thermal Wave Reflection (R ~ +0.766)', col_accent_gold);
        text(ax, 50, 64.5, 'Delta T_defect(x,y,t) Peak Thermal Contrast Accumulation', 'Color', [1.0, 0.85, 0.3], 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    else
        text(ax, 50, 42, 'HOMOGENEOUS HEALTHY SPECIMEN (NO INCLUSION)', 'Color', col_accent_grn, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    end
    
    % Plate Length Lx Dimension
    line(ax, [10, 90], [14, 14], 'Color', [0.5, 0.6, 0.75], 'LineWidth', 1.2);
    text(ax, 50, 11.5, sprintf('Plate Length Lx = %.1f mm (Width Ly = %.1f mm)', cfg.plate.length_mm, cfg.plate.width_mm), ...
        'Color', [0.7, 0.8, 0.9], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Plate Thickness Lz Dimension
    line(ax, [93, 93], [24, 60], 'Color', [0.5, 0.6, 0.75], 'LineWidth', 1.2);
    text(ax, 94.5, 42, sprintf('Lz = %.2f mm', cfg.plate.thickness_mm), 'Color', [0.7, 0.8, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Bottom Disclaimer Note
    text(ax, 50, 4, 'SCHEMATIC - NOT TO SCALE (EXAGGERATED DEFECT DEPTH & THICKNESS FOR SCIENTIFIC CLARITY)', ...
        'Color', [0.95, 0.75, 0.35], 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
end

%% =========================================================================
%% UTILITY DRAWING HELPERS
%% =========================================================================
function drawStageBlock(ax, x, y, w, h, stage_num, stage_title, col_hdr, col_bg, col_border, text_lines, out_label)
    % Background Card
    drawRoundedBox(ax, x, y, w, h, col_bg, col_border, 1.2);
    
    % Header Banner
    drawRoundedBox(ax, x, y + h - 3.8, w, 3.8, [0.15, 0.18, 0.25], col_border, 1.0);
    
    % Stage Badge
    badge_w = 4.2;
    drawRoundedBox(ax, x + 0.8, y + h - 3.4, badge_w, 3.0, col_hdr, col_hdr, 1.0);
    text(ax, x + 0.8 + badge_w/2, y + h - 1.9, sprintf('S%d', stage_num), ...
        'Color', 'k', 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Stage Title
    text(ax, x + 5.8, y + h - 1.9, stage_title, 'Color', col_hdr, 'FontSize', 9, 'FontWeight', 'bold', 'Interpreter', 'none');
    
    % Body Text Lines
    n_lines = length(text_lines);
    spacing = (h - 6.8) / max(1, n_lines);
    for k = 1:n_lines
        y_pos = y + h - 4.8 - (k - 0.5) * spacing;
        text(ax, x + 1.5, y_pos, text_lines{k}, 'Color', [0.82, 0.88, 0.94], 'FontSize', 7.5, 'Interpreter', 'none');
    end
    
    % Output Label at bottom
    if nargin >= 12 && ~isempty(out_label)
        text(ax, x + w - 1.2, y + 1.2, out_label, 'Color', col_hdr, 'FontSize', 7.0, ...
            'FontWeight', 'bold', 'HorizontalAlignment', 'right', 'Interpreter', 'none');
    end
end

function drawRoundedBox(ax, x, y, w, h, face_col, edge_col, line_w)
    rectangle(ax, 'Position', [x, y, w, h], 'Curvature', [0.06, 0.08], ...
        'FaceColor', face_col, 'EdgeColor', edge_col, 'LineWidth', line_w);
end

function drawLabeledArrow(ax, x1, y1, x2, y2, label_str, col)
    % Draw line with arrowhead
    line(ax, [x1, x2], [y1, y2], 'Color', col, 'LineWidth', 1.8);
    
    % Arrowhead
    if x1 == x2 % Vertical
        if y2 < y1 % Downward
            patch(ax, [x2-0.8, x2+0.8, x2], [y2+1.2, y2+1.2, y2], col, 'EdgeColor', col);
            if ~isempty(label_str)
                text(ax, x2 + 1.0, (y1 + y2)/2, label_str, 'Color', col, 'FontSize', 7.5, 'FontWeight', 'bold', 'Interpreter', 'none');
            end
        else % Upward
            patch(ax, [x2-0.8, x2+0.8, x2], [y2-1.2, y2-1.2, y2], col, 'EdgeColor', col);
            if ~isempty(label_str)
                text(ax, x2 + 1.0, (y1 + y2)/2, label_str, 'Color', col, 'FontSize', 7.5, 'FontWeight', 'bold', 'Interpreter', 'none');
            end
        end
    elseif y1 == y2 % Horizontal
        if x2 > x1 % Rightward
            patch(ax, [x2-1.0, x2-1.0, x2], [y2-0.7, y2+0.7, y2], col, 'EdgeColor', col);
            if ~isempty(label_str)
                text(ax, (x1 + x2)/2, y2 + 1.2, label_str, 'Color', col, 'FontSize', 7.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
            end
        else % Leftward
            patch(ax, [x2+1.0, x2+1.0, x2], [y2-0.7, y2+0.7, y2], col, 'EdgeColor', col);
            if ~isempty(label_str)
                text(ax, (x1 + x2)/2, y2 + 1.2, label_str, 'Color', col, 'FontSize', 7.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
            end
        end
    end
end

function drawHorizontalConnector(ax, x1, y1, x2, y2, label_str, col)
    % Polyline connector with rightward turn
    xm = (x1 + x2) / 2;
    line(ax, [x1, xm, xm, x2], [y1, y1, y2, y2], 'Color', col, 'LineWidth', 1.8, 'LineStyle', '--');
    patch(ax, [x2-1.0, x2-1.0, x2], [y2-0.7, y2+0.7, y2], col, 'EdgeColor', col);
    text(ax, xm, (y1 + y2)/2, label_str, 'Color', col, 'FontSize', 7.5, 'FontWeight', 'bold', ...
        'HorizontalAlignment', 'center', 'BackgroundColor', [0.08, 0.09, 0.13], 'Interpreter', 'none');
end
