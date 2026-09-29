function val_results = run_validation_suite(varargin)
% RUN_VALIDATION_SUITE Executes the complete numerical and physical validation suite.
%
% Validations:
%   1. FEM vs FDM Cross-Validation
%   2. Mesh Convergence (Coarse, Medium, Fine)
%   3. Time-Step Convergence (dt, dt/2, dt/4)
%   4. Physical Sanity & Conservation Checks
%   5. Parameter Sensitivity Study
%   6. Cross-Language Python-MATLAB Scientific Parity Audit

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
addParameter(p, 'Quick', true, @islogical);
parse(p, varargin{:});
is_quick = p.Results.Quick;

t_val_start = tic;

fprintf('================================================================================\n');
fprintf('                 LFMT COMPREHENSIVE NUMERICAL VALIDATION SUITE                  \n');
fprintf('================================================================================\n');

% 1. FEM vs FDM Cross-Validation
fprintf('\n--- 1. FEM vs FDM Cross-Validation ---\n');
comp_fem_fdm = compare_fem_fdm();

% 2. Mesh Convergence
fprintf('\n--- 2. Mesh Spatial Convergence Study ---\n');
mesh_res = validate_mesh(is_quick);

% 3. Time-Step Convergence
fprintf('\n--- 3. Time-Step Temporal Convergence Study ---\n');
dt_res = validate_timestep(is_quick);

% 4. Physics Sanity
fprintf('\n--- 4. Physical Sanity & Conservation Audit ---\n');
phys_res = validate_physics(is_quick);

% 5. Parameter Sensitivity
fprintf('\n--- 5. Parameter Sensitivity Analysis ---\n');
sens_res = validate_sensitivity(is_quick);

% 6. Python-MATLAB Scientific Parity
fprintf('\n--- 6. Cross-Language Python-MATLAB Parity ---\n');
parity_res = validate_python_parity();

% 7. Plot Validation Summary Figure
fig_dir = fullfile(matlab_root, 'results', 'figures');
if ~exist(fig_dir, 'dir'), mkdir(fig_dir); end
plot_validation_results(mesh_res.table, dt_res.table, sens_res.table, fullfile(fig_dir, 'fig18_validation_summary.png'));

total_val_time = toc(t_val_start);

fprintf('\n================== VALIDATION SUITE COMPLETE ==================\n');
fprintf('All validation modules executed in %.2f s (%.2f min).\n', total_val_time, total_val_time / 60.0);
fprintf('===============================================================\n');

val_results = struct(...
    'fem_vs_fdm', comp_fem_fdm, ...
    'mesh', mesh_res, ...
    'timestep', dt_res, ...
    'physics', phys_res, ...
    'sensitivity', sens_res, ...
    'python_parity', parity_res, ...
    'runtime_s', total_val_time ...
);
end
