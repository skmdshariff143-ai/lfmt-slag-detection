function mesh_report = validate_mesh(quick)
% VALIDATE_MESH Mesh spatial convergence study for 3-D Hex8 FEM solver.
%
% Tests:
%   - Coarse: Nx=20, Ny=14, Nz=6   (1,680 elements)
%   - Medium: Nx=40, Ny=28, Nz=12  (13,440 elements - Standard)
%   - Fine:   Nx=60, Ny=42, Nz=18  (45,360 elements)

if nargin < 1 || isempty(quick), quick = false; end

fprintf('================================================================================\n');
fprintf('                 3-D FEM MESH INDEPENDENCE & CONVERGENCE STUDY                  \n');
fprintf('================================================================================\n');

cfg_base = default_config();
% Use shorter duration for quick validation if requested
if quick
    cfg_base.simulation.total_time_s = 4.0;
    cfg_base.excitation.duration_s = 4.0;
    mesh_levels = [
        struct('name', 'Coarse', 'Nx', 15, 'Ny', 10, 'Nz', 4);
        struct('name', 'Medium', 'Nx', 30, 'Ny', 20, 'Nz', 8);
        struct('name', 'Fine',   'Nx', 45, 'Ny', 30, 'Nz', 12)
    ];
else
    mesh_levels = [
        struct('name', 'Coarse', 'Nx', 20, 'Ny', 14, 'Nz', 6);
        struct('name', 'Medium', 'Nx', 40, 'Ny', 28, 'Nz', 12);
        struct('name', 'Fine',   'Nx', 60, 'Ny', 42, 'Nz', 18)
    ];
end

results = [];
for i = 1:length(mesh_levels)
    lvl = mesh_levels(i);
    cfg = cfg_base;
    cfg.simulation.Nx = lvl.Nx;
    cfg.simulation.Ny = lvl.Ny;
    cfg.simulation.Nz = lvl.Nz;
    
    fprintf('Running %s Mesh (Nx=%d, Ny=%d, Nz=%d)...\n', lvl.name, lvl.Nx, lvl.Ny, lvl.Nz);
    res = lfmt_simulate_fem(cfg);
    
    peak_T = max(res.surface_temperature(:));
    final_mean_T = mean(reshape(res.surface_temperature(end, :, :), [], 1));
    
    row = struct(...
        'mesh_level', string(lvl.name), ...
        'Nx', lvl.Nx, ...
        'Ny', lvl.Ny, ...
        'Nz', lvl.Nz, ...
        'total_nodes', res.total_nodes, ...
        'total_elements', res.total_elements, ...
        'peak_temperature_K', peak_T, ...
        'final_mean_temperature_K', final_mean_T, ...
        'runtime_s', res.runtime_s, ...
        'surface_temp', res.surface_temperature ...
    );
    results = [results; row]; %#ok<AGROW>
end

% Compute Relative Errors relative to Fine Mesh
fine_T = results(end).surface_temp;
table_rows = [];
for i = 1:length(results)
    curr_T = results(i).surface_temp;
    diff_T = curr_T - fine_T;
    rel_l2 = norm(diff_T(:)) / (norm(fine_T(:)) + 1e-12);
    rms_err = sqrt(mean(diff_T(:).^2));
    
    t_row = struct(...
        'mesh_level', results(i).mesh_level, ...
        'Nx', results(i).Nx, ...
        'Ny', results(i).Ny, ...
        'Nz', results(i).Nz, ...
        'total_elements', results(i).total_elements, ...
        'peak_temp_K', results(i).peak_temperature_K, ...
        'rms_error_vs_fine_K', rms_err, ...
        'relative_l2_error', rel_l2, ...
        'runtime_s', results(i).runtime_s ...
    );
    table_rows = [table_rows; t_row]; %#ok<AGROW>
end

mesh_table = struct2table(table_rows);
disp(mesh_table);

% Save table
matlab_dir = fileparts(fileparts(mfilename('fullpath')));
out_csv = fullfile(matlab_dir, 'results', 'validation', 'mesh_convergence.csv');
writetable(mesh_table, out_csv);
fprintf('Mesh convergence table saved to: %s\n', out_csv);

mesh_report = struct('table', mesh_table, 'results', results);
end
