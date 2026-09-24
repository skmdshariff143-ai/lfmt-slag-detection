function dt_report = validate_timestep(quick)
% VALIDATE_TIMESTEP Temporal time-step convergence study for 3-D FEM solver.
%
% Tests:
%   - Coarse dt: dt = 0.04 s
%   - Baseline dt: dt = 0.02 s (Standard)
%   - Fine dt: dt = 0.01 s

if nargin < 1 || isempty(quick), quick = false; end

fprintf('================================================================================\n');
fprintf('               3-D FEM TIME-STEP CONVERGENCE & STABILITY STUDY                  \n');
fprintf('================================================================================\n');

cfg_base = default_config();
if quick
    cfg_base.simulation.total_time_s = 4.0;
    cfg_base.excitation.duration_s = 4.0;
    cfg_base.simulation.Nx = 20;
    cfg_base.simulation.Ny = 14;
    cfg_base.simulation.Nz = 6;
    dt_levels = [0.08, 0.04, 0.02];
else
    dt_levels = [0.04, 0.02, 0.01];
end

results = [];
for i = 1:length(dt_levels)
    dt_val = dt_levels(i);
    cfg = cfg_base;
    cfg.simulation.dt_s = dt_val;
    
    fprintf('Running Time-Step dt = %.4f s...\n', dt_val);
    res = lfmt_simulate_fem(cfg);
    
    peak_T = max(res.surface_temperature(:));
    final_mean_T = mean(reshape(res.surface_temperature(end, :, :), [], 1));
    
    row = struct(...
        'dt_s', dt_val, ...
        'n_steps', round(cfg.simulation.total_time_s / dt_val), ...
        'peak_temperature_K', peak_T, ...
        'final_mean_temperature_K', final_mean_T, ...
        'runtime_s', res.runtime_s, ...
        'surface_temp', res.surface_temperature ...
    );
    results = [results; row]; %#ok<AGROW>
end

% Compute errors relative to finest dt
fine_T = results(end).surface_temp;
table_rows = [];
for i = 1:length(results)
    curr_T = results(i).surface_temp;
    diff_T = curr_T - fine_T;
    rel_l2 = norm(diff_T(:)) / (norm(fine_T(:)) + 1e-12);
    rms_err = sqrt(mean(diff_T(:).^2));
    
    t_row = struct(...
        'dt_s', results(i).dt_s, ...
        'n_steps', results(i).n_steps, ...
        'peak_temp_K', results(i).peak_temperature_K, ...
        'rms_error_vs_fine_dt_K', rms_err, ...
        'relative_l2_error', rel_l2, ...
        'runtime_s', results(i).runtime_s ...
    );
    table_rows = [table_rows; t_row]; %#ok<AGROW>
end

dt_table = struct2table(table_rows);
disp(dt_table);

% Save table
matlab_dir = fileparts(fileparts(mfilename('fullpath')));
out_csv = fullfile(matlab_dir, 'results', 'validation', 'timestep_convergence.csv');
writetable(dt_table, out_csv);
fprintf('Timestep convergence table saved to: %s\n', out_csv);

dt_report = struct('table', dt_table, 'results', results);
end
