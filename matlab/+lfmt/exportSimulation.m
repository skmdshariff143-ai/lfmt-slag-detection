function exportSimulation(sim_result, output_mat_path, config)
% EXPORTSIMULATION Saves MATLAB simulation results to .MAT and JSON manifest
%
% Standardized output for Python / AutoDefectAnalyzer interoperability

if nargin < 3, config = struct(); end

% Ensure target directory exists
out_dir = fileparts(output_mat_path);
if ~isempty(out_dir) && ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

% Extract arrays
surface_temperature = sim_result.surface_temperature;
time_vector = sim_result.time_vector;
camera_x_mm = sim_result.camera_x_mm;
camera_y_mm = sim_result.camera_y_mm;
runtime_s = sim_result.runtime_s;
solver_name = sim_result.solver_name;
solver_dt_s = 0.04;
if isfield(sim_result, 'solver_dt_s')
    solver_dt_s = sim_result.solver_dt_s;
end
camera_frame_rate_hz = 10.0;
if isfield(sim_result, 'camera_frame_rate_hz')
    camera_frame_rate_hz = sim_result.camera_frame_rate_hz;
end

save(output_mat_path, 'surface_temperature', 'time_vector', 'camera_x_mm', 'camera_y_mm', 'runtime_s', 'solver_name', 'solver_dt_s', 'camera_frame_rate_hz', '-v7');

% Manifest JSON
manifest = struct(...
    'solver_name', solver_name, ...
    'discretization', '3-D Conservative Finite Difference', ...
    'time_integration', 'Implicit Backward Euler', ...
    'matlab_version', version, ...
    'matlab_release', version('-release'), ...
    'runtime_s', runtime_s, ...
    'solver_dt_s', solver_dt_s, ...
    'camera_frame_rate_hz', camera_frame_rate_hz, ...
    'n_frames', length(time_vector), ...
    'spatial_resolution', [length(camera_y_mm), length(camera_x_mm)], ...
    'output_file', output_mat_path ...
);

manifest_path = strrep(output_mat_path, '.mat', '_manifest.json');
txt = jsonencode(manifest, 'PrettyPrint', true);
fid = fopen(manifest_path, 'w');
if fid ~= -1
    fwrite(fid, txt, 'char');
    fclose(fid);
end
end

