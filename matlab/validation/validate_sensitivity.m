function sens_report = validate_sensitivity(quick)
% VALIDATE_SENSITIVITY Evaluates parameter sensitivity on benchmark case (D=8mm, z=0.4mm).
%
% Parameter variations:
%   - Applied heat flux q0: [-10%, 0%, +10%] -> [4500, 5000, 5500] W/m^2
%   - Slag thermal conductivity k_slag: [-10%, 0%, +10%] -> [1.08, 1.20, 1.32] W/(m·K)
%   - Convection coefficient h_conv: [-20%, 0%, +20%] -> [8.0, 10.0, 12.0] W/(m^2·K)
%   - Slag specific heat Cp_slag: [-10%, 0%, +10%] -> [765, 850, 935] J/(kg·K)

if nargin < 1 || isempty(quick), quick = true; end

fprintf('================================================================================\n');
fprintf('                 3-D FEM PARAMETER SENSITIVITY ANALYSIS                         \n');
fprintf('================================================================================\n');

cfg_base = default_config();
cfg_base.defects(1).diameter_mm = 8.0;
cfg_base.defects(1).depth_mm = 0.4;

if quick
    cfg_base.simulation.total_time_s = 4.0;
    cfg_base.excitation.duration_s = 4.0;
    cfg_base.simulation.Nx = 20;
    cfg_base.simulation.Ny = 14;
    cfg_base.simulation.Nz = 6;
end

variations = [
    struct('param', 'Baseline', 'delta_pct', 0.0, 'field', '', 'val', 0.0);
    struct('param', 'q0', 'delta_pct', -10.0, 'field', 'excitation.q0_w_m2', 'val', 4500.0);
    struct('param', 'q0', 'delta_pct', +10.0, 'field', 'excitation.q0_w_m2', 'val', 5500.0);
    struct('param', 'k_slag', 'delta_pct', -10.0, 'field', 'defects(1).thermal_conductivity', 'val', 1.08);
    struct('param', 'k_slag', 'delta_pct', +10.0, 'field', 'defects(1).thermal_conductivity', 'val', 1.32);
    struct('param', 'h_conv', 'delta_pct', -20.0, 'field', 'excitation.h_conv_w_m2k', 'val', 8.0);
    struct('param', 'h_conv', 'delta_pct', +20.0, 'field', 'excitation.h_conv_w_m2k', 'val', 12.0);
    struct('param', 'cp_slag', 'delta_pct', -10.0, 'field', 'defects(1).specific_heat', 'val', 765.0);
    struct('param', 'cp_slag', 'delta_pct', +10.0, 'field', 'defects(1).specific_heat', 'val', 935.0)
];

results_list = [];

for i = 1:length(variations)
    v = variations(i);
    cfg = cfg_base;
    
    if ~isempty(v.field)
        eval(sprintf('cfg.%s = %f;', v.field, v.val));
    end
    
    fprintf('Running Sensitivity Case: %s (Delta = %+d%%)...\n', v.param, int32(v.delta_pct));
    res = lfmt_simulate_fem(cfg);
    
    [~, ny, nx] = size(res.surface_temperature);
    T_center = squeeze(res.surface_temperature(:, round(ny/2), round(nx/2)));
    T_sound = squeeze(res.surface_temperature(:, 2, 2));
    peak_T = max(res.surface_temperature(:));
    max_contrast = max(T_center - T_sound);
    
    % Matched filter on sensitivity case
    mf_res = lfmt_matched_filter(res.surface_temperature, res.time_vector);
    mf_map = mf_res.score_map;
    
    % GT mask for CNR
    [x_mesh, y_mesh] = meshgrid(res.camera_x_mm, res.camera_y_mm);
    gt_mask = ((x_mesh - cfg.defects(1).center_x_mm).^2 + (y_mesh - cfg.defects(1).center_y_mm).^2) <= (cfg.defects(1).diameter_mm/2)^2;
    
    mu_d = mean(mf_map(gt_mask));
    mu_s = mean(mf_map(~gt_mask));
    denom = sqrt(var(mf_map(gt_mask)) + var(mf_map(~gt_mask)));
    cnr_mf = abs(mu_d - mu_s) / max(1e-12, denom);
    
    row = struct(...
        'parameter', string(v.param), ...
        'delta_percent', v.delta_pct, ...
        'peak_temperature_K', peak_T, ...
        'max_contrast_K', max_contrast, ...
        'matched_filter_cnr', cnr_mf ...
    );
    results_list = [results_list; row]; %#ok<AGROW>
end

sens_table = struct2table(results_list);
disp(sens_table);

% Save sensitivity table
matlab_dir = fileparts(fileparts(mfilename('fullpath')));
out_csv = fullfile(matlab_dir, 'results', 'validation', 'sensitivity_summary.csv');
writetable(sens_table, out_csv);
fprintf('Sensitivity table saved to: %s\n', out_csv);

sens_report = struct('table', sens_table);
end
