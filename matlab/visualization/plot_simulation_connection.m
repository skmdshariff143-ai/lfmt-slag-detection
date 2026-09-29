function varargout = plot_simulation_connection(cfg, varargin)
% PLOT_SIMULATION_CONNECTION Generates publication-quality circuit/block-style
% connection diagrams for Linear Frequency-Modulated Infrared Thermography (LFMT).
%
% 100% VIRTUAL SIMULATION ARCHITECTURE (No physical hardware).
% Visualizes:
%   1. End-to-end computational simulation pipeline (simulation_connection.png)
%   2. 3-D Hex8 FEM numerical formulation architecture (virtual_fem_connection.png)
%   3. 5 Blind Signal Processing & Segmentation suite (processing_connection.png)
%   4. 3-D Specimen Cross-Section Heat Transfer schematic (specimen_connection.png)
%
% Syntax:
%   plot_simulation_connection()
%   plot_simulation_connection(cfg)
%   plot_simulation_connection(cfg, 'Target', 'all')
%   [h_sim, h_fem, h_proc, h_spec] = plot_simulation_connection(...)
%
% Parameters:
%   cfg       - Optional struct or JSON path with simulation parameters.
%   'Target'  - 'all' (default), 'simulation', 'virtual_fem', 'processing', 'specimen'
%               (Note: 'physical' is gracefully redirected to 'virtual_fem')
%   'Export'  - true (default: saves 300-DPI PNG figures to results/figures)
%   'Visible' - 'on' (default) or 'off'
%
% Project:
%   Linear Frequency-Modulated Infrared Thermography for Subsurface Slag
%   Inclusion Detection in Mild Steel (Virtual Computational Framework)

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
addParameter(p, 'Target', 'all', @(x) any(validatestring(x, {'all', 'simulation', 'virtual_fem', 'processing', 'specimen', 'physical'})));
addParameter(p, 'Export', true, @islogical);
addParameter(p, 'Visible', 'on', @(x) ischar(x) || isstring(x));
parse(p, varargin{:});

target_mode = lower(p.Results.Target);
if strcmp(target_mode, 'physical')
    target_mode = 'virtual_fem';
end
do_export = p.Results.Export;
vis_mode = char(p.Results.Visible);

root_dir = fileparts(fileparts(mfilename('fullpath')));
fig_dir = fullfile(root_dir, 'results', 'figures');
if ~exist(fig_dir, 'dir')
    mkdir(fig_dir);
end

h_sim = [];
h_fem = [];
h_proc = [];
h_spec = [];

%% 1. End-to-End Simulation Connection Pipeline Diagram
if strcmp(target_mode, 'all') || strcmp(target_mode, 'simulation')
    h_sim = renderSimulationPipelineFigure(cfg, vis_mode);
    if do_export
        export_path = fullfile(fig_dir, 'simulation_connection.png');
        exportgraphics(h_sim, export_path, 'Resolution', 300);
        savefig(h_sim, fullfile(fig_dir, 'simulation_connection.fig'));
        fprintf('Saved simulation connection diagram: %s\n', export_path);
    end
end

%% 2. 3-D Hex8 FEM Numerical Heat Transfer Architecture
if strcmp(target_mode, 'all') || strcmp(target_mode, 'virtual_fem')
    h_fem = renderVirtualFEMFigure(cfg, vis_mode);
    if do_export
        export_path = fullfile(fig_dir, 'virtual_fem_connection.png');
        exportgraphics(h_fem, export_path, 'Resolution', 300);
        savefig(h_fem, fullfile(fig_dir, 'virtual_fem_connection.fig'));
        fprintf('Saved virtual FEM connection diagram: %s\n', export_path);
    end
end

%% 3. 5 Blind Signal Processing & Segmentation Suite Diagram
if strcmp(target_mode, 'all') || strcmp(target_mode, 'processing')
    h_proc = renderProcessingSuiteFigure(cfg, vis_mode);
    if do_export
        export_path = fullfile(fig_dir, 'processing_connection.png');
        exportgraphics(h_proc, export_path, 'Resolution', 300);
        savefig(h_proc, fullfile(fig_dir, 'processing_connection.fig'));
        fprintf('Saved processing connection diagram: %s\n', export_path);
    end
end

%% 4. 3-D Specimen Heat Transfer Connection Schematic
if strcmp(target_mode, 'all') || strcmp(target_mode, 'specimen')
    h_spec = renderSpecimenSchematicFigure(cfg, vis_mode);
    if do_export
        export_path = fullfile(fig_dir, 'specimen_connection.png');
        exportgraphics(h_spec, export_path, 'Resolution', 300);
        savefig(h_spec, fullfile(fig_dir, 'specimen_connection.fig'));
        fprintf('Saved specimen connection schematic: %s\n', export_path);
    end
end

if strcmp(target_mode, 'virtual_fem')
    if nargout > 0, varargout{1} = h_fem; end
elseif strcmp(target_mode, 'processing')
    if nargout > 0, varargout{1} = h_proc; end
elseif strcmp(target_mode, 'specimen')
    if nargout > 0, varargout{1} = h_spec; end
elseif strcmp(target_mode, 'simulation')
    if nargout > 0, varargout{1} = h_sim; end
else % 'all'
    if nargout == 1
        varargout{1} = [h_sim, h_fem, h_proc, h_spec];
    else
        if nargout > 0, varargout{1} = h_sim; end
        if nargout > 1, varargout{2} = h_fem; end
        if nargout > 2, varargout{3} = h_proc; end
        if nargout > 3, varargout{4} = h_spec; end
    end
end

end

%% =========================================================================
%% SUB-ROUTINE 1: Render Complete Simulation Computational Pipeline
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
    
    if isfield(cfg.excitation, 'observation_time_s')
        tobs = cfg.excitation.observation_time_s;
    elseif isfield(cfg.simulation, 'total_time_s')
        tobs = cfg.simulation.total_time_s;
    else
        tobs = 10.0;
    end
    
    % 1. Header Banner (100% Virtual Framework)
    drawRoundedBox(ax, 2, 92, 96, 6.5, [0.10, 0.12, 0.17], [0.3, 0.45, 0.65], 1.5);
    text(ax, 50, 96.2, 'LINEAR FREQUENCY-MODULATED INFRARED THERMOGRAPHY (LFMT) - VIRTUAL SIMULATION ARCHITECTURE', ...
        'Color', col_accent_cyan, 'FontSize', 12, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 93.4, '100% Computational Simulation: Parameters -> Chirp -> 3-D Hex8 FEM -> Virtual IR Camera -> 5 Blind Detectors -> Segmentation -> Audit', ...
        'Color', [0.75, 0.82, 0.90], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % --- COLUMN 1: Forward Numerical Simulation Pipeline (x in [3, 47]) ---
    
    % Stage 1: User & Material Inputs
    if cfg.plate.has_defect
        d_str = sprintf('Slag Defect: D = %.1f mm, Depth z = %.2f mm, Loc = (%.1f, %.1f) mm', ...
            cfg.plate.defect.diameter_mm, cfg.plate.defect.depth_mm, cfg.plate.defect.center_x_mm, cfg.plate.defect.center_y_mm);
    else
        d_str = 'Reference Healthy Plate (Zero Defect)';
    end
    
    drawStageBlock(ax, 3, 76, 44, 14.5, 1, 'USER PARAMETERS & THERMOPHYSICAL PROPERTIES', col_accent_cyan, col_bg_card, col_border, ...
        {sprintf('Geometry: Mild Steel Plate %.1f x %.1f x %.2f mm', cfg.plate.length_mm, cfg.plate.width_mm, cfg.plate.thickness_mm); ...
         d_str; ...
         'Steel Substrate: k = 45.0 W/m-K, rho = 7850 kg/m^3, Cp = 460 J/kg-K (alpha = 1.246e-5 m^2/s)'; ...
         'Slag Inclusion: k = 1.5 W/m-K, rho = 2800 kg/m^3, Cp = 800 J/kg-K (alpha = 6.696e-7 m^2/s)'; ...
         'Thermal Impedance Mismatch: Reflection Coefficient R = +0.766 (Strong Thermal Barrier)'}, ...
        'Output: Mesh Specifications & Material Property Tensor');
    
    drawLabeledArrow(ax, 25, 76, 25, 68, 'Mesh & Physical Parameters', col_arrow);
    
    % Stage 2: LFMT Optical Excitation Chirp
    drawStageBlock(ax, 3, 53.5, 44, 14.5, 2, 'LFMT OPTICAL EXCITATION SYNTHESIS', col_accent_gold, col_bg_card, col_border, ...
        {sprintf('Modulation Bandwidth: f0 = %.3f Hz -> f1 = %.3f Hz (Sweep Delta f = %.3f Hz)', cfg.excitation.f0_hz, cfg.excitation.f1_hz, cfg.excitation.f1_hz - cfg.excitation.f0_hz); ...
         sprintf('Duration & Energy: Texc = %.1f s, Tobs = %.1f s, Peak Flux q0 = %.0f W/m^2', cfg.excitation.duration_s, tobs, cfg.excitation.q0_w_m2); ...
         'Chirp Law: phi(t) = 2*pi*(f0*t + 0.5*(f1-f0)/Texc * t^2) - pi/2'; ...
         'Heat Flux: q(t) = q0 * 0.5 * (1 + sin(phi(t))) for t in [0, Texc], 0 otherwise'; ...
         'Chirp Reference Signal: s_ref(t) = sin(phi(t)) for Matched Filter correlation'}, ...
        'Output: Temporal Heat Flux Vector q(t) [W/m^2] & Reference Waveform s_ref(t)');
    
    drawLabeledArrow(ax, 25, 53.5, 25, 45.5, 'Heat Flux Boundary Condition q(t)', col_arrow);
    
    % Stage 3: 3-D Hex8 Transient FEM Heat Solver
    drawStageBlock(ax, 3, 31, 44, 14.5, 3, '3-D HEX8 FEM TRANSIENT THERMAL ENGINE', col_accent_red, col_bg_card, col_border, ...
        {'PDE: rho * Cp * dT/dt = div(k * grad(T)) with Convective & Radiative Losses'; ...
         'Spatial Discretization: 8-node Hexahedral (Hex8) Elements with 2x2x2 Gauss Quadrature'; ...
         'Global Matrix Assembly: [M]*T_dot + [K]*T + [H]*T = F(t) (Implicit Euler Time-Stepping)'; ...
         'Boundary BCs: Top q_top = q(t) - h(T-Tamb), Bottom/Sides Insulated (Adiabatic)'; ...
         'Physical Sanity: Strict Energy Conservation & Zero-Flux Stability Audited'}, ...
        'Output: 3-D Internal Node Temperature Field T(x, y, z, t)');
    
    drawLabeledArrow(ax, 25, 31, 25, 23, 'Surface Node Temperature Field T(x, y, z=0, t)', col_arrow);
    
    % Stage 4: Virtual IR Decoupled Camera Sensor
    if isfield(cfg.camera, 'noise_snr_db') && ~isempty(cfg.camera.noise_snr_db)
        snr_str = sprintf('Sensor Noise Model: Gaussian AWGN with NETD SNR = %.1f dB', cfg.camera.noise_snr_db);
    elseif isfield(cfg.camera, 'snr_db') && ~isempty(cfg.camera.snr_db)
        snr_str = sprintf('Sensor Noise Model: Gaussian AWGN with NETD SNR = %.1f dB', cfg.camera.snr_db);
    else
        snr_str = 'Sensor Noise Model: Clean Thermograms (Inf dB) or Configured NETD AWGN';
    end
    
    fps_val = 25.0;
    if isfield(cfg.camera, 'frame_rate_hz')
        fps_val = cfg.camera.frame_rate_hz;
    elseif isfield(cfg.camera, 'sampling_rate_hz')
        fps_val = cfg.camera.sampling_rate_hz;
    end
    
    drawStageBlock(ax, 3, 3, 44, 20, 4, 'VIRTUAL DECOUPLED IR CAMERA SENSOR MODEL', col_accent_purp, col_bg_card, col_border, ...
        {sprintf('Spatial Grid: %d x %d px (dx = %.2f mm, dy = %.2f mm)', cfg.camera.cam_nx, cfg.camera.cam_ny, cfg.plate.length_mm/cfg.camera.cam_nx, cfg.plate.width_mm/cfg.camera.cam_ny); ...
         sprintf('Temporal Sampling: Frame Rate = %.1f fps (dt_cam = %.3f s, Nt = %d frames)', fps_val, 1/fps_val, round(tobs * fps_val)+1); ...
         'Radiometric Decoupling: Decoupled camera sensor model preserves pure thermal evolution'; ...
         snr_str; ...
         'Noise Synthesis: T_noisy(x,y,t) = T_clean(x,y,t) + N(0, sigma_netd^2)'}, ...
        'Output: Synthetic Noisy Thermal Video Sequence T(x,y,t) [K]');
    
    % Cross-Pipeline Arrow (Bottom left -> Top right)
    drawLabeledArrow(ax, 47, 13, 53, 76, 'Synthetic Thermal Video Cube T(x,y,t)', col_accent_purp);
    
    % --- COLUMN 2: 5 Blind Signal Processing & Detection (x in [53, 97]) ---
    
    % Stage 5: 5 Blind Signal Processing Suite
    drawStageBlock(ax, 53, 56.5, 44, 34, 5, '5 BLIND ADVANCED THERMOGRAPHIC DETECTORS', col_accent_gold, col_bg_card, col_border, ...
        {'Preprocessing: Frame-zero subtraction T_norm(x,y,t) = T(x,y,t) - T(x,y,0)'; ...
         '-----------------------------------------------------------------------------------------'; ...
         'Method 1 [Raw Contrast]: S_raw(x,y) = max_t |T_norm(x,y,t)|  (Peak Thermal Contrast)'; ...
         'Method 2 [Matched Filter]: S_mf(x,y) = int_0^T T_norm(x,y,t) * s_ref(t) dt  (Pulse Compression)'; ...
         'Method 3 [SVD-PCT]: A = U*S*V'' -> S_pct(x,y) = EOF-2 (Principal Component Thermography)'; ...
         'Method 4 [Sparse PCT]: min ||A - U*V''||_F^2 + lambda*||V||_1 (SPCT Saliency Enhancement)'; ...
         'Method 5 [Random Projection]: S_rpt(x,y) = Phi * A (Johnson-Lindenstrauss Dimensionality Reduction)'; ...
         '-----------------------------------------------------------------------------------------'; ...
         'Score Normalization: S_norm(x,y) = (S - min(S)) / (max(S) - min(S)) in [0, 1]'}, ...
        'Output: 5 Calibrated Feature Maps S_raw, S_mf, S_pct, S_spct, S_rpt');
    
    drawLabeledArrow(ax, 75, 56.5, 75, 48.5, 'Normalized Feature Score Maps S_m(x,y)', col_arrow);
    
    % Stage 6: Automatic Defect Segmentation
    drawStageBlock(ax, 53, 34, 44, 14.5, 6, 'AUTOMATIC BLIND DEFECT SEGMENTATION', col_accent_cyan, col_bg_card, col_border, ...
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
%% SUB-ROUTINE 2: Render 3-D Hex8 FEM Numerical Architecture
%% =========================================================================
function fig = renderVirtualFEMFigure(cfg, vis_mode)
    fig = figure('Name', 'LFMT 3-D Hex8 FEM Numerical Architecture', ...
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
    
    % 1. Header Banner
    drawRoundedBox(ax, 3, 91, 94, 7, [0.10, 0.12, 0.17], [0.3, 0.45, 0.65], 1.5);
    text(ax, 50, 95.5, '3-D HEX8 FEM TRANSIENT HEAT DIFFUSION NUMERICAL ARCHITECTURE', ...
        'Color', col_accent_cyan, 'FontSize', 12, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 92.5, 'Validated Finite Element Formulation for Subsurface Slag Inclusion Thermography in Mild Steel Plates', ...
        'Color', [0.75, 0.82, 0.90], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Left Panel: Governing PDE & Weak Form Discretization
    drawRoundedBox(ax, 5, 50, 43, 38, col_bg_card, col_accent_cyan, 1.5);
    text(ax, 26.5, 85, 'GOVERNING PDE & VARIATIONAL FORMULATION', 'Color', col_accent_cyan, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 7, 80, '1. Heat Diffusion Equation:', 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    text(ax, 7, 76, '   rho * Cp * (dT/dt) = div( k * grad(T) )', 'Color', [0.95, 0.95, 0.95], 'FontSize', 9, 'FontName', 'Consolas', 'Interpreter', 'none');
    text(ax, 7, 71, '2. Boundary Conditions:', 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    text(ax, 7, 67, '   Top (z = 0): -k*(dT/dz) = q(t) - h*(T - Tamb)', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.5, 'FontName', 'Consolas', 'Interpreter', 'none');
    text(ax, 7, 63, '   Bottom & Edges: Insulated Adiabatic BC (grad(T)*n = 0)', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 7, 58, '3. Heterogeneous Material Assignment:', 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    text(ax, 7, 54, '   Mild Steel: k = 45 W/m-K | rho = 7850 kg/m^3 | Cp = 460 J/kg-K', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.0, 'Interpreter', 'none');
    text(ax, 7, 51, '   Slag Defect: k = 1.5 W/m-K | rho = 2800 kg/m^3 | Cp = 800 J/kg-K', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.0, 'Interpreter', 'none');
    
    % Right Panel: Hex8 Discretization & Time-Stepping Solver
    drawRoundedBox(ax, 52, 50, 43, 38, col_bg_card, col_accent_grn, 1.5);
    text(ax, 73.5, 85, 'HEX8 DISCRETIZATION & IMPLICIT EULER SOLVER', 'Color', col_accent_grn, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 54, 80, '1. Hex8 Isoparametric Element Matrices:', 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    text(ax, 54, 76, '   K_e = int B'' * k * B dOmega  (Conductivity Matrix)', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.5, 'FontName', 'Consolas', 'Interpreter', 'none');
    text(ax, 54, 72, '   M_e = int N'' * rho * Cp * N dOmega  (Capacitance Matrix)', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.5, 'FontName', 'Consolas', 'Interpreter', 'none');
    text(ax, 54, 67, '2. Numerical Quadrature: 2x2x2 Gauss-Legendre Points', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 54, 62, '3. Unconditionally Stable Implicit Time Stepping:', 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    text(ax, 54, 58, '   (M/dt + K + H) * T(n+1) = (M/dt) * T(n) + F(n+1)', 'Color', [0.95, 0.95, 0.95], 'FontSize', 9, 'FontName', 'Consolas', 'Interpreter', 'none');
    text(ax, 54, 53, '4. Verification: Spatial mesh independence & temporal convergence audited', 'Color', [0.75, 0.85, 0.75], 'FontSize', 8.0, 'Interpreter', 'none');
    
    % Arrow Down from Matrices to Thermal Field Output
    drawLabeledArrow(ax, 50, 50, 50, 42, 'Global Matrix Solution Vector T_xyz(t)', col_arrow);
    
    % Bottom Specimen Geometry & Thermal Reflection Summary
    drawRoundedBox(ax, 5, 8, 90, 32, [0.14, 0.17, 0.23], [0.35, 0.55, 0.80], 2.0);
    text(ax, 50, 36.5, '3-D SPECIMEN DISCRETIZATION & THERMAL WAVE MECHANICS', 'Color', [0.95, 0.95, 1.0], 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 8, 31.5, sprintf('- Plate Dimensions: Lx = %.1f mm, Ly = %.1f mm, Lz = %.2f mm', cfg.plate.length_mm, cfg.plate.width_mm, cfg.plate.thickness_mm), 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.5, 'Interpreter', 'none');
    if cfg.plate.has_defect
        text(ax, 8, 27.5, sprintf('- Slag Defect Geometry: Diameter D = %.1f mm, Depth z = %.2f mm, Thickness h = %.2f mm', ...
            cfg.plate.defect.diameter_mm, cfg.plate.defect.depth_mm, cfg.plate.defect.thickness_mm), 'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    else
        text(ax, 8, 27.5, '- Baseline Homogeneous Mild Steel Plate (No Defect Inclusion)', 'Color', col_accent_grn, 'FontSize', 8.5, 'Interpreter', 'none');
    end
    text(ax, 8, 23.5, '- Thermal Effusivity Contrast: e_steel ~ 12,740 J/(m^2-K-s^0.5) vs e_slag ~ 1,689 J/(m^2-K-s^0.5)', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 8, 19.5, '- Theoretical Thermal Wave Reflection: R = (e_steel - e_slag)/(e_steel + e_slag) = +0.766', 'Color', col_accent_cyan, 'FontSize', 8.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    text(ax, 8, 15.5, '- Diffusion Length: mu(f) = sqrt(alpha / (pi * f)) | LFMT sweep covers subsurface depth range 0.1 to 2.0 mm', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'Interpreter', 'none');
    text(ax, 8, 11.5, '- Surface Temperature Extraction: Top surface nodes (z = 0) mapped to Decoupled Virtual IR Sensor grid', 'Color', [0.75, 0.85, 0.95], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Footer Note
    text(ax, 50, 3.0, '100% COMPUTATIONAL SIMULATION FRAMEWORK (MATLAB Hex8 3-D Finite Element Method)', ...
        'Color', col_accent_gold, 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
end

%% =========================================================================
%% SUB-ROUTINE 3: Render 5 Blind Signal Processing Suite Diagram
%% =========================================================================
function fig = renderProcessingSuiteFigure(cfg, vis_mode)
    fig = figure('Name', 'LFMT 5 Blind Signal Processing Suite Architecture', ...
        'NumberTitle', 'off', 'Color', [0.07, 0.08, 0.11], ...
        'Position', [70, 50, 1320, 850], 'Visible', vis_mode);
    
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
    
    % Header
    drawRoundedBox(ax, 3, 91, 94, 7, [0.10, 0.12, 0.17], [0.3, 0.45, 0.65], 1.5);
    text(ax, 50, 95.5, '5 BLIND SIGNAL PROCESSING ALGORITHMS & SEGMENTATION ARCHITECTURE', ...
        'Color', col_accent_cyan, 'FontSize', 12, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 92.5, 'Parallel Feature Extraction Suite: Raw Contrast, Matched Filter, SVD-PCT, SPCT, and RPT', ...
        'Color', [0.75, 0.82, 0.90], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Top Input Box: Synthetic Thermogram Cube
    drawRoundedBox(ax, 20, 77, 60, 11, col_bg_card, col_accent_purp, 1.5);
    text(ax, 50, 84, 'PREPROCESSED THERMOGRAM CUBE T_norm(x, y, t)', 'Color', col_accent_purp, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 80, 'Baseline frame subtraction T_norm = T(x,y,t) - T(x,y,0) | Reference chirp s_ref(t) = sin(phi(t))', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.5, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % 5 Branches (5 Columns)
    methods = {
        '1. RAW CONTRAST', col_accent_cyan, {'Peak Contrast Extraction', 'S_raw(x,y) = max_t |T_norm|', 'Fast Baseline (O(1))', 'Sensitive to Noise'};
        '2. MATCHED FILTER', col_accent_gold, {'Pulse Compression', 'S_mf = int T_norm * s_ref dt', 'Optimal Linear SNR (O(Nt))', 'High Contrast Boost'};
        '3. SVD-PCT', col_accent_grn, {'Principal Component', 'A = U * S * V''', 'S_pct(x,y) = EOF-2', 'Unsupervised Separation'};
        '4. SPARSE PCT', col_accent_red, {'L1 Sparsity Regularization', 'min ||A - UV''||^2 + lambda*||V||_1', 'Enhanced Defect Saliency', 'Robust to Artifacts'};
        '5. RPT', col_accent_purp, {'Random Projection', 'Phi ~ N(0, 1/d)', 'S_rpt = Phi * A (JL Lemma)', 'Ultra-Fast SVD Speedup'}
    };
    
    x_starts = [4, 23, 42, 61, 80];
    w_box = 16.5;
    
    for m = 1:5
        xs = x_starts(m);
        m_name = methods{m, 1};
        m_col = methods{m, 2};
        m_lines = methods{m, 3};
        
        drawLabeledArrow(ax, 50, 77, xs + w_box/2, 62, '', col_arrow);
        drawRoundedBox(ax, xs, 32, w_box, 30, col_bg_card, m_col, 1.5);
        text(ax, xs + w_box/2, 58, m_name, 'Color', m_col, 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
        
        for l = 1:length(m_lines)
            text(ax, xs + 1, 52 - (l-1)*5.5, ['- ', m_lines{l}], 'Color', [0.8, 0.85, 0.9], 'FontSize', 7.5, 'Interpreter', 'none');
        end
        
        drawLabeledArrow(ax, xs + w_box/2, 32, xs + w_box/2, 23, '', col_arrow);
    end
    
    % Bottom Combined Segmentation & Metric Evaluation Block
    drawRoundedBox(ax, 4, 7, 92, 16, [0.10, 0.12, 0.17], col_accent_cyan, 1.5);
    text(ax, 50, 19.5, 'BLIND OTSU SEGMENTATION & BENCHMARK QUANTITATIVE EVALUATION', 'Color', col_accent_cyan, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 6, 15, '1. Adaptive Otsu Thresholding tau_m -> Binary Mask B_m(x,y) = S_norm(x,y) > tau_m (Minimizing intra-class variance)', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.0, 'Interpreter', 'none');
    text(ax, 6, 11.5, '2. Morphological Post-Processing: Disk Opening (r=2 px) + Closing (r=3 px) + 8-Connected Component Saliency Filter', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.0, 'Interpreter', 'none');
    text(ax, 6, 8.0, '3. Metrics: CNR = |mu_def - mu_sound|/sigma_sound | IoU = |B_m & G_gt|/|B_m | G_gt| | eps_loc = ||(x_hat,y_hat) - (x_gt,y_gt)||', 'Color', col_accent_gold, 'FontSize', 8.0, 'Interpreter', 'none');
end

%% =========================================================================
%% SUB-ROUTINE 4: Render Specimen Heat Transfer Cross-Section Schematic
%% =========================================================================
function fig = renderSpecimenSchematicFigure(cfg, vis_mode)
    fig = figure('Name', 'LFMT 3-D Specimen Heat Transfer Schematic', ...
        'NumberTitle', 'off', 'Color', [0.07, 0.08, 0.11], ...
        'Position', [90, 70, 1280, 800], 'Visible', vis_mode);
    
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
    
    % Header
    drawRoundedBox(ax, 3, 91, 94, 7, [0.10, 0.12, 0.17], [0.3, 0.45, 0.65], 1.5);
    text(ax, 50, 95.5, '3-D SPECIMEN CROSS-SECTION & THERMAL WAVE DIFFUSION MECHANICS', ...
        'Color', col_accent_cyan, 'FontSize', 12, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 50, 92.5, 'Mild Steel Plate with Subsurface Slag Inclusion: Wave Reflections & Contrast Generation', ...
        'Color', [0.75, 0.82, 0.90], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Top Surface Heat Flux Arrow Array
    for x_arr = 20:10:80
        drawLabeledArrow(ax, x_arr, 85, x_arr, 71, '', col_accent_red);
    end
    text(ax, 50, 88, 'Uniform LFMT Modulated Heat Flux q(t) [W/m^2]', 'Color', col_accent_red, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Steel Plate Block Cross-Section (y in [30, 70], x in [15, 85])
    rectangle(ax, 'Position', [15, 30, 70, 40], 'FaceColor', [0.16, 0.20, 0.28], 'EdgeColor', [0.35, 0.55, 0.85], 'LineWidth', 2.0);
    text(ax, 20, 66, 'TOP SURFACE z = 0 mm (Virtual Radiometric Thermal Camera Field T(x,y,t))', 'Color', col_accent_cyan, 'FontSize', 9, 'FontWeight', 'bold', 'Interpreter', 'none');
    text(ax, 20, 34, 'BOTTOM SURFACE z = Lz = 1.50 mm (Adiabatic / Insulated Boundary)', 'Color', [0.7, 0.75, 0.85], 'FontSize', 8.5, 'Interpreter', 'none');
    
    % Slag Inclusion Region
    if cfg.plate.has_defect
        rectangle(ax, 'Position', [42, 45, 16, 12], 'FaceColor', [0.45, 0.15, 0.15], 'EdgeColor', col_accent_red, 'LineWidth', 2.0);
        text(ax, 50, 52, sprintf('SLAG INCLUSION\nD = %.1f mm\nz = %.2f mm', cfg.plate.defect.diameter_mm, cfg.plate.defect.depth_mm), ...
            'Color', [1.0, 0.9, 0.9], 'FontSize', 8.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
        
        % Thermal Wave Reflection Arrows
        drawLabeledArrow(ax, 50, 68, 50, 58, '', col_accent_gold);
        drawLabeledArrow(ax, 50, 58, 50, 68, '', col_accent_gold);
        text(ax, 52, 63, 'Thermal Wave Reflection (R = +0.766)', 'Color', col_accent_gold, 'FontSize', 8.0, 'FontWeight', 'bold', 'Interpreter', 'none');
    end
    
    % Side Dimensions
    text(ax, 11, 50, 'Lz = 1.5 mm', 'Color', [0.8, 0.85, 0.9], 'FontSize', 8.5, 'HorizontalAlignment', 'center', 'Rotation', 90, 'Interpreter', 'none');
    text(ax, 50, 26, 'Plate Length Lx = 100 mm  |  Width Ly = 70 mm', 'Color', [0.8, 0.85, 0.9], 'FontSize', 9, 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    
    % Bottom Explanation Panel
    drawRoundedBox(ax, 5, 5, 90, 18, col_bg_card, col_border, 1.2);
    text(ax, 50, 19.5, 'THERMAL DIFFUSION & IMPEDANCE CONTRAST MECHANICS', 'Color', col_accent_gold, 'FontSize', 9.5, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Interpreter', 'none');
    text(ax, 7, 15, '- High thermal effusivity substrate (Steel e1 ~ 12,740 J/m^2-K-s^0.5) vs Low effusivity defect (Slag e2 ~ 1,689 J/m^2-K-s^0.5)', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.0, 'Interpreter', 'none');
    text(ax, 7, 11.5, '- Slag inclusion acts as a thermal barrier, reflecting heat back towards the top surface and creating a delayed hot-spot Delta T(t)', 'Color', [0.85, 0.9, 0.95], 'FontSize', 8.0, 'Interpreter', 'none');
    text(ax, 7, 8.0, '- The 5 Blind Detectors isolate this modulated thermal contrast without requiring prior defect depth or size knowledge', 'Color', col_accent_grn, 'FontSize', 8.0, 'Interpreter', 'none');
end

%% =========================================================================
%% HELPER DRAWING FUNCTIONS
%% =========================================================================
function drawRoundedBox(ax, x, y, w, h, bg_col, edge_col, lw)
    rectangle(ax, 'Position', [x, y, w, h], 'Curvature', [0.08, 0.08], ...
        'FaceColor', bg_col, 'EdgeColor', edge_col, 'LineWidth', lw);
end

function drawStageBlock(ax, x, y, w, h, stage_num, title_str, title_col, bg_col, edge_col, body_lines, footer_str)
    drawRoundedBox(ax, x, y, w, h, bg_col, edge_col, 1.5);
    
    % Stage Number Badge
    rectangle(ax, 'Position', [x+0.8, y+h-4.5, 3.6, 3.6], 'Curvature', [1, 1], ...
        'FaceColor', title_col, 'EdgeColor', 'none');
    text(ax, x+2.6, y+h-2.7, num2str(stage_num), 'Color', [0.07, 0.08, 0.11], ...
        'FontSize', 9, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
    
    % Title
    text(ax, x+5.5, y+h-2.7, title_str, 'Color', title_col, ...
        'FontSize', 9.5, 'FontWeight', 'bold', 'Interpreter', 'none');
    
    % Separator line
    plot(ax, [x+1, x+w-1], [y+h-5.2, y+h-5.2], 'Color', [edge_col, 0.5], 'LineWidth', 1.0);
    
    % Body lines
    n_lines = length(body_lines);
    avail_h = h - 8.5;
    line_spacing = avail_h / max(n_lines, 1);
    
    for i = 1:n_lines
        y_pos = y + h - 6.5 - (i-0.5)*line_spacing;
        text(ax, x+1.5, y_pos, ['- ', body_lines{i}], 'Color', [0.85, 0.90, 0.95], ...
            'FontSize', 7.5, 'Interpreter', 'none');
    end
    
    % Footer Tag
    if nargin >= 12 && ~isempty(footer_str)
        text(ax, x+1.5, y+1.8, footer_str, 'Color', [0.45, 0.75, 0.95], ...
            'FontSize', 7.0, 'FontAngle', 'italic', 'Interpreter', 'none');
    end
end

function drawLabeledArrow(ax, x1, y1, x2, y2, label_str, col)
    if nargin < 7 || isempty(col), col = [0.45, 0.65, 0.85]; end
    
    % Draw main arrow line
    annotation_arrow(ax, x1, y1, x2, y2, col);
    
    % Label at midpoint
    if nargin >= 6 && ~isempty(label_str)
        mx = (x1 + x2) / 2;
        my = (y1 + y2) / 2;
        text(ax, mx + 1.2, my, label_str, 'Color', col, ...
            'FontSize', 7.2, 'FontAngle', 'italic', 'Interpreter', 'none');
    end
end

function annotation_arrow(ax, x1, y1, x2, y2, col)
    dx = x2 - x1;
    dy = y2 - y1;
    L = sqrt(dx^2 + dy^2);
    if L < 1e-6, return; end
    
    u = [dx, dy] / L;
    v = [-u(2), u(1)];
    
    head_len = min(2.0, L * 0.35);
    head_wid = min(1.2, head_len * 0.6);
    
    % Line
    plot(ax, [x1, x2 - u(1)*head_len*0.8], [y1, y2 - u(2)*head_len*0.8], ...
        'Color', col, 'LineWidth', 1.6);
    
    % Head triangle
    p_tip = [x2, y2];
    p_left = p_tip - u * head_len + v * head_wid;
    p_right = p_tip - u * head_len - v * head_wid;
    
    fill(ax, [p_tip(1), p_left(1), p_right(1)], [p_tip(2), p_left(2), p_right(2)], ...
        col, 'EdgeColor', col, 'LineWidth', 1.0);
end
