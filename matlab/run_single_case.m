function results = run_single_case(config, varargin)
% RUN_SINGLE_CASE Runs 3-D FEM simulation, noise injection, 5 signal processing methods,
% blind detection, quantitative metrics, and generates side-by-side visualization.
%
% Usage:
%   results = run_single_case()
%   results = run_single_case(custom_config, 'Plot', true, 'SaveFigures', true)

% Ensure all project subdirectories are on the MATLAB search path
matlab_root = fileparts(mfilename('fullpath'));
addpath(matlab_root);
addpath(fullfile(matlab_root, 'config'));
addpath(fullfile(matlab_root, 'simulation'));
addpath(fullfile(matlab_root, 'processing'));
addpath(fullfile(matlab_root, 'detection'));
addpath(fullfile(matlab_root, 'evaluation'));
addpath(fullfile(matlab_root, 'validation'));
addpath(fullfile(matlab_root, 'visualization'));
addpath(fullfile(matlab_root, 'tests'));

p = inputParser;
addParameter(p, 'Plot', true, @islogical);
addParameter(p, 'SaveFigures', true, @islogical);
addParameter(p, 'Verbose', true, @islogical);

if nargin < 1 || isempty(config)
    config = default_config();
end
parse(p, varargin{:});

do_plot = p.Results.Plot;
save_figs = p.Results.SaveFigures;
verbose = p.Results.Verbose;

t_total_start = tic;

if verbose
    fprintf('================================================================================\n');
    fprintf('           LFMT 3-D FEM SIMULATION & BLIND SIGNAL PROCESSING PIPELINE           \n');
    fprintf('================================================================================\n');
end

% 1. Forward 3-D FEM Simulation (or load cached simulation)
sim_hash = lfmt.cache('hash', config);
cached_sim = lfmt.cache('load', sim_hash);

if ~isempty(cached_sim)
    if verbose, fprintf('Loaded cached 3-D simulation (SHA-256: %s...)\n', sim_hash(1:12)); end
    sim_res = cached_sim;
else
    if verbose, fprintf('Running 3-D Hexahedral FEM Thermal Solver...\n'); end
    if isfield(config.simulation, 'solver_type') && strcmpi(config.simulation.solver_type, 'fdm')
        sim_res = lfmt_simulate_fdm(config);
    else
        sim_res = lfmt_simulate_fem(config);
    end
    lfmt.cache('save', sim_hash, sim_res);
end

% 2. Noise Realization
snr_db = config.camera.noise_snr_db;
seed = config.camera.noise_seed;
[T_noisy, noise_sigma] = lfmt.noise(sim_res.surface_temperature, snr_db, seed);
if verbose
    if isempty(snr_db) || isinf(snr_db)
        fprintf('Camera Observation: Clean Thermograms (noise sigma = 0.0 K)\n');
    else
        fprintf('Camera Observation: AWGN SNR = %d dB (noise sigma = %.4f K, seed = %d)\n', int32(snr_db), noise_sigma, seed);
    end
end

% 3. Ground Truth Mask (Strictly for Evaluation ONLY)
[x_mesh, y_mesh] = meshgrid(sim_res.camera_x_mm, sim_res.camera_y_mm);
if sim_res.geometry.has_defect
    d = sim_res.geometry.defect;
    gt_mask = ((x_mesh - d.center_x_mm).^2 + (y_mesh - d.center_y_mm).^2) <= (d.radius_m * 1e3)^2;
else
    gt_mask = false(size(x_mesh));
end

% 4. Run 5 Blind Thermographic Signal Processing Methods
if verbose, fprintf('Executing 5 Blind Signal Processing Algorithms...\n'); end

% Method 1: Raw Thermal Contrast
res_raw = lfmt_raw_contrast(T_noisy, sim_res.time_vector);
det_raw = segment_defect(res_raw.score_map, [config.plate.length_mm, config.plate.width_mm], config.processing.detection_min_area_px);
met_raw = compute_metrics('Raw Contrast', det_raw, sim_res.geometry, gt_mask, res_raw.score_map, res_raw.runtime_s);
res_raw.detection = det_raw;
res_raw.metrics = met_raw;

% Method 2: Matched Filter / Pulse Compression
res_mf = lfmt_matched_filter(T_noisy, sim_res.time_vector, config.excitation.f0_hz, config.excitation.f1_hz, config.excitation.duration_s, config.excitation.q0_w_m2);
det_mf = segment_defect(res_mf.score_map, [config.plate.length_mm, config.plate.width_mm], config.processing.detection_min_area_px);
met_mf = compute_metrics('Matched Filter', det_mf, sim_res.geometry, gt_mask, res_mf.score_map, res_mf.runtime_s);
res_mf.detection = det_mf;
res_mf.metrics = met_mf;

% Method 3: Principal Component Thermography (PCT)
res_pct = lfmt_pct(T_noisy, config.processing.pct_n_components);
det_pct = segment_defect(res_pct.score_map, [config.plate.length_mm, config.plate.width_mm], config.processing.detection_min_area_px);
met_pct = compute_metrics('PCT', det_pct, sim_res.geometry, gt_mask, res_pct.score_map, res_pct.runtime_s);
res_pct.detection = det_pct;
res_pct.metrics = met_pct;

% Method 4: Sparse PCT (SPCT)
res_spct = lfmt_spct(T_noisy, config.processing.spct_n_components, config.processing.spct_alpha);
det_spct = segment_defect(res_spct.score_map, [config.plate.length_mm, config.plate.width_mm], config.processing.detection_min_area_px);
met_spct = compute_metrics('SPCT', det_spct, sim_res.geometry, gt_mask, res_spct.score_map, res_spct.runtime_s);
res_spct.detection = det_spct;
res_spct.metrics = met_spct;

% Method 5: Random Projection Technique (RPT)
res_rpt = lfmt_rpt(T_noisy, config.processing.rpt_n_components, config.processing.rpt_seed);
det_rpt = segment_defect(res_rpt.score_map, [config.plate.length_mm, config.plate.width_mm], config.processing.detection_min_area_px);
met_rpt = compute_metrics('RPT', det_rpt, sim_res.geometry, gt_mask, res_rpt.score_map, res_rpt.runtime_s);
res_rpt.detection = det_rpt;
res_rpt.metrics = met_rpt;

processed_results = struct(...
    'RAW', res_raw, ...
    'MF', res_mf, ...
    'PCT', res_pct, ...
    'SPCT', res_spct, ...
    'RPT', res_rpt ...
);

total_time = toc(t_total_start);

% Compile Summary Table
summary_rows = [
    struct('Method', "Raw Contrast", 'Detected', met_raw.is_detected, 'IoU', met_raw.iou, 'Dice', met_raw.dice, 'CNR', met_raw.cnr, 'LocError_mm', met_raw.localization_error_mm, 'Runtime_s', met_raw.runtime_s);
    struct('Method', "Matched Filter", 'Detected', met_mf.is_detected, 'IoU', met_mf.iou, 'Dice', met_mf.dice, 'CNR', met_mf.cnr, 'LocError_mm', met_mf.localization_error_mm, 'Runtime_s', met_mf.runtime_s);
    struct('Method', "PCT (SVD)", 'Detected', met_pct.is_detected, 'IoU', met_pct.iou, 'Dice', met_pct.dice, 'CNR', met_pct.cnr, 'LocError_mm', met_pct.localization_error_mm, 'Runtime_s', met_pct.runtime_s);
    struct('Method', "SPCT (L1-Sparse)", 'Detected', met_spct.is_detected, 'IoU', met_spct.iou, 'Dice', met_spct.dice, 'CNR', met_spct.cnr, 'LocError_mm', met_spct.localization_error_mm, 'Runtime_s', met_spct.runtime_s);
    struct('Method', "RPT (Gaussian JL)", 'Detected', met_rpt.is_detected, 'IoU', met_rpt.iou, 'Dice', met_rpt.dice, 'CNR', met_rpt.cnr, 'LocError_mm', met_rpt.localization_error_mm, 'Runtime_s', met_rpt.runtime_s)
];
summary_table = struct2table(summary_rows);

if verbose
    fprintf('\n================== EVALUATION METRICS SUMMARY ==================\n');
    disp(summary_table);
    fprintf('Total execution time: %.2f s\n', total_time);
    fprintf('================================================================\n');
end

% 5. Publication Plots
if do_plot || save_figs
    matlab_dir = fileparts(mfilename('fullpath'));
    plot_thermograms(sim_res, fullfile(matlab_dir, 'results', 'figures', 'fig4_thermogram_evolution.png'));
    plot_method_comparison(processed_results, sim_res, fullfile(matlab_dir, 'results', 'figures', 'fig10_method_comparison.png'));
end

results = struct(...
    'simulation', sim_res, ...
    'noisy_thermograms', T_noisy, ...
    'ground_truth_mask', gt_mask, ...
    'processed', processed_results, ...
    'summary_table', summary_table, ...
    'runtime_s', total_time ...
);
end
