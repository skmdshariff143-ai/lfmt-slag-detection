function sim_result = solveTransientThermal(config)
% SOLVETRANSIENTTHERMAL 3-D Conservative Transient Heat Conduction Solver (MATLAB_FDM)
%
% Solves:
%   rho(x)*Cp(x)*dT/dt = div(k(x)*grad(T))
%
% Time integration: Implicit Backward Euler (unconditionally stable)
% Camera acquisition: Explicitly decoupled from solver timestep via temporal sampling

if ischar(config) || isstring(config)
    config = lfmt.loadConfig(config);
end

t_start = tic;

% 1. Parse configuration parameters
Lx_mm = double(config.plate.length_mm);
Ly_mm = double(config.plate.width_mm);
Lz_mm = double(config.plate.thickness_mm);

Nx = int32(config.simulation.Nx);
Ny = int32(config.simulation.Ny);
Nz = int32(config.simulation.Nz);
dt_solver = double(config.simulation.dt_s);
total_time = double(config.simulation.total_time_s);

f0 = double(config.excitation.f0_hz);
f1 = double(config.excitation.f1_hz);
q0 = double(config.excitation.q0_w_m2);
duration = double(config.excitation.duration_s);
h_conv = double(config.excitation.h_conv_w_m2k);
Tamb = double(config.excitation.ambient_temp_k);

cam_nx = int32(config.camera.cam_nx);
cam_ny = int32(config.camera.cam_ny);

if isfield(config.camera, 'frame_rate_hz')
    cam_fps = double(config.camera.frame_rate_hz);
elseif isfield(config.camera, 'sampling_rate_hz')
    cam_fps = double(config.camera.sampling_rate_hz);
else
    cam_fps = 10.0;
end

defects = [];
if isfield(config, 'defects')
    defects = config.defects;
end

% 2. Create Grid & Materials
grid = lfmt.createGrid(Lx_mm, Ly_mm, Lz_mm, Nx, Ny, Nz);
mat_db = lfmt.createMaterialDatabase();
[k_field, rhoCp_field, defect_mask] = lfmt.assignMaterials(grid, defects, mat_db);

% 3. Assemble Operators
L = lfmt.buildConductionOperator(grid, k_field);
[H_diag, h_amb_vec] = lfmt.buildConvectionOperator(grid, k_field, h_conv, Tamb);
q_unit_vec = lfmt.buildFrontFluxVector(grid);

% Volumetric heat capacity vector
C_vec = reshape(rhoCp_field .* grid.dV, [], 1);
C_over_dt = C_vec / dt_solver;

% 4. System Matrix for Backward Euler: A = diag(C/dt + H_diag) + L
N = grid.total_cells;
A = spdiags(C_over_dt + H_diag, 0, N, N) + L;

% Pre-factorize sparse system (Cholesky decomposition once)
dA = decomposition(A, 'chol');

% 5. Solver & Camera Time Vectors
solver_time_vector = (0:dt_solver:total_time)';
n_solver_steps = length(solver_time_vector);

cam_dt = 1.0 / cam_fps;
cam_time_vector = (0:cam_dt:total_time)';
n_cam_frames = length(cam_time_vector);

% Camera sampling coordinates
cam_x_mm = linspace(0, Lx_mm, cam_nx);
cam_y_mm = linspace(0, Ly_mm, cam_ny);
[mesh_X_cam, mesh_Y_cam] = ndgrid(cam_x_mm, cam_y_mm);

grid_xc_mm = grid.xc * 1e3;
grid_yc_mm = grid.yc * 1e3;

% 6. Transient Time Stepping with Decoupled Camera Interpolation
T_prev = full(Tamb * ones(N, 1));
T_current = T_prev;
surface_frames = zeros(n_cam_frames, cam_ny, cam_nx);

% Frame 1 represents strictly initial ambient equilibrium at t=0
surface_frames(1, :, :) = Tamb;
next_cam_idx = 2;

for n = 2:n_solver_steps
    t_prev = solver_time_vector(n-1);
    t_curr = solver_time_vector(n);
    
    % Instantaneous heat flux for solver step
    if t_curr <= duration
        beta = (f1 - f0) / duration;
        phase = 2 * pi * (f0 * t_curr + 0.5 * beta * t_curr^2);
        q_curr = q0 * (1.0 + sin(phase));
    else
        q_curr = 0.0; % Cooling period
    end
    
    % Right hand side: (C/dt)*T_{n-1} + q_curr*q_unit + h_amb
    rhs = C_over_dt .* T_prev + q_curr * q_unit_vec + h_amb_vec;
    
    % Solve implicit step
    T_current = dA \ rhs;
    
    % Check if any camera acquisition times fall in (t_prev, t_curr]
    while next_cam_idx <= n_cam_frames && cam_time_vector(next_cam_idx) <= t_curr + 1e-9
        t_cam = cam_time_vector(next_cam_idx);
        alpha = (t_cam - t_prev) / (t_curr - t_prev);
        alpha = max(0.0, min(1.0, alpha));
        
        % Interpolate front-surface solution in time
        T_interp_vec = (1.0 - alpha) * T_prev(1:(Nx*Ny)) + alpha * T_current(1:(Nx*Ny));
        T_front_2d = reshape(T_interp_vec, [Nx, Ny]);
        
        % Spatial interpolation onto camera resolution
        F_interp = griddedInterpolant({grid_xc_mm, grid_yc_mm}, T_front_2d, 'linear', 'nearest');
        surf_sampled = F_interp(mesh_X_cam, mesh_Y_cam);
        
        % Store in Python canonical shape [n_frames, cam_ny, cam_nx]
        surface_frames(next_cam_idx, :, :) = surf_sampled';
        next_cam_idx = next_cam_idx + 1;
    end
    
    T_prev = T_current;
end

% Handle edge case if last camera frame was slightly beyond final solver step
while next_cam_idx <= n_cam_frames
    T_front_2d = reshape(T_current(1:(Nx*Ny)), [Nx, Ny]);
    F_interp = griddedInterpolant({grid_xc_mm, grid_yc_mm}, T_front_2d, 'linear', 'nearest');
    surf_sampled = F_interp(mesh_X_cam, mesh_Y_cam);
    surface_frames(next_cam_idx, :, :) = surf_sampled';
    next_cam_idx = next_cam_idx + 1;
end

runtime_s = toc(t_start);

geom = lfmt.geometry(config.plate, defects);

mesh_info = struct(...
    'x_nodes_mm', grid.x_edges * 1e3, ...
    'y_nodes_mm', grid.y_edges * 1e3, ...
    'z_nodes_mm', grid.z_edges * 1e3, ...
    'Nx', Nx, ...
    'Ny', Ny, ...
    'Nz', Nz, ...
    'nx_nodes', Nx + 1, ...
    'ny_nodes', Ny + 1, ...
    'nz_nodes', Nz + 1, ...
    'dx_mm', Lx_mm / double(Nx), ...
    'dy_mm', Ly_mm / double(Ny), ...
    'dz_mm', Lz_mm / double(Nz), ...
    'total_nodes', double(Nx + 1) * double(Ny + 1) * double(Nz + 1), ...
    'total_elements', double(Nx) * double(Ny) * double(Nz), ...
    'dofs', double(Nx) * double(Ny) * double(Nz) ...
);

sim_result = struct(...
    'surface_temperature', surface_frames, ...
    'time_vector', cam_time_vector, ...
    'camera_x_mm', cam_x_mm, ...
    'camera_y_mm', cam_y_mm, ...
    'solver_dt_s', dt_solver, ...
    'camera_frame_rate_hz', cam_fps, ...
    'geometry', geom, ...
    'mesh', mesh_info, ...
    'config', config, ...
    'grid', grid, ...
    'k_field', k_field, ...
    'rhoCp_field', rhoCp_field, ...
    'defect_mask', defect_mask, ...
    'runtime_s', runtime_s, ...
    'solver_name', 'MATLAB_FDM', ...
    'discretization', '3-D Conservative Finite Difference', ...
    'time_integration', 'Implicit Backward Euler', ...
    'total_nodes', double(Nx + 1) * double(Ny + 1) * double(Nz + 1), ...
    'total_elements', double(Nx) * double(Ny) * double(Nz), ...
    'dofs', double(Nx) * double(Ny) * double(Nz) ...
);
end


