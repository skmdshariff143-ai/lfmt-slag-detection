function sim_result = solveTransientThermal(config)
% SOLVETRANSIENTTHERMAL 3-D Conservative Transient Heat Conduction Solver (MATLAB_FDM)
%
% Solves:
%   rho(x)*Cp(x)*dT/dt = div(k(x)*grad(T))
%
% Time integration: Implicit Backward Euler (unconditionally stable)

t_start = tic;

% 1. Parse configuration parameters
Lx_mm = config.plate.length_mm;
Ly_mm = config.plate.width_mm;
Lz_mm = config.plate.thickness_mm;

Nx = config.simulation.Nx;
Ny = config.simulation.Ny;
Nz = config.simulation.Nz;
dt = config.simulation.dt_s;
total_time = config.simulation.total_time_s;

f0 = config.excitation.f0_hz;
f1 = config.excitation.f1_hz;
q0 = config.excitation.q0_w_m2;
duration = config.excitation.duration_s;
h_conv = config.excitation.h_conv_w_m2k;
Tamb = config.excitation.ambient_temp_k;

cam_nx = config.camera.cam_nx;
cam_ny = config.camera.cam_ny;

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
C_over_dt = C_vec / dt;

% 4. System Matrix for Backward Euler: A = diag(C/dt + H_diag) + L
N = grid.total_cells;
A = spdiags(C_over_dt + H_diag, 0, N, N) + L;

% Pre-factorize sparse system (Cholesky decomposition once)
dA = decomposition(A, 'chol');

% 5. LFMT Excitation Setup
exc = lfmt.createLFMTExcitation(f0, f1, duration, q0, dt);
time_vector = (0:dt:total_time)';
n_frames = length(time_vector);

% Camera sampling coordinates
cam_x_mm = linspace(0, Lx_mm, cam_nx);
cam_y_mm = linspace(0, Ly_mm, cam_ny);
[mesh_X_cam, mesh_Y_cam] = ndgrid(cam_x_mm, cam_y_mm);

grid_xc_mm = grid.xc * 1e3;
grid_yc_mm = grid.yc * 1e3;

% 6. Transient Time Stepping
T_current = full(Tamb * ones(N, 1));
surface_frames = zeros(n_frames, cam_ny, cam_nx);

% Frame 0 represents strictly initial ambient equilibrium
surface_frames(1, :, :) = Tamb;

for k = 2:n_frames
    t_curr = time_vector(k);
    
    % Instantaneous heat flux
    if t_curr <= duration
        beta = (f1 - f0) / duration;
        phase = 2 * pi * (f0 * t_curr + 0.5 * beta * t_curr^2);
        q_curr = q0 * (1.0 + sin(phase));
    else
        q_curr = 0.0; % Cooling period
    end
    
    % Right hand side: (C/dt)*T_n + q_curr*q_unit + h_amb
    rhs = C_over_dt .* T_current + q_curr * q_unit_vec + h_amb_vec;
    
    % Solve implicit step
    T_current = dA \ rhs;
    
    % Extract z=0 front layer temperature (k=1)
    T_front_2d = reshape(T_current(1:(Nx*Ny)), [Nx, Ny]);
    
    % Robust interpolation onto regular camera grid with nearest boundary extrapolation
    F_interp = griddedInterpolant({grid_xc_mm, grid_yc_mm}, T_front_2d, 'linear', 'nearest');
    surf_sampled = F_interp(mesh_X_cam, mesh_Y_cam); % Nx_cam x Ny_cam (40 x 28)
    
    % Store in Python canonical shape [n_frames, cam_ny, cam_nx] = (101, 28, 40)
    surface_frames(k, :, :) = surf_sampled';
end

runtime_s = toc(t_start);

sim_result = struct(...
    'surface_temperature', surface_frames, ...
    'time_vector', time_vector, ...
    'camera_x_mm', cam_x_mm, ...
    'camera_y_mm', cam_y_mm, ...
    'grid', grid, ...
    'k_field', k_field, ...
    'rhoCp_field', rhoCp_field, ...
    'defect_mask', defect_mask, ...
    'runtime_s', runtime_s, ...
    'solver_name', 'MATLAB_FDM', ...
    'discretization', '3-D Conservative Finite Difference', ...
    'time_integration', 'Implicit Backward Euler' ...
);
end
