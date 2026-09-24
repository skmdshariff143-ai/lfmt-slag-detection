function sim_result = lfmt_simulate_fem(config)
% LFMT_SIMULATE_FEM Genuine 3-D Trilinear Hexahedral Finite Element Method (FEM) Solver.
%
% Solves the 3-D transient heat diffusion equation:
%   rho(x)*Cp(x)*dT/dt = div(k(x)*grad(T))
%
% Discretization:
%   - Genuine 3D 8-node trilinear hexahedral elements (Hex8)
%   - Global Sparse Stiffness Matrix K
%   - Global Sparse Consistent Mass Matrix M
%   - Surface Convection Boundary Matrix M_conv
%   - Surface Load Vector F(t)
%   - Implicit Backward Euler time integration (unconditionally stable)
%   - Pre-factorized sparse Cholesky decomposition reused across all time steps
%   - Decoupled camera spatial/temporal sampling onto virtual IR sensor

t_start = tic;

if ischar(config) || isstring(config)
    config = lfmt.loadConfig(config);
end

% 1. Geometry & Mesh Dimensions
Lx_m = double(config.plate.length_mm) * 1e-3;
Ly_m = double(config.plate.width_mm) * 1e-3;
Lz_m = double(config.plate.thickness_mm) * 1e-3;

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
cam_fps = double(config.camera.sampling_rate_hz);

% 2. Generate 1D Mesh Coordinates
x_nodes = linspace(0.0, Lx_m, double(Nx) + 1);
y_nodes = linspace(0.0, Ly_m, double(Ny) + 1);
z_nodes = linspace(0.0, Lz_m, double(Nz) + 1);

nx_nodes = length(x_nodes);
ny_nodes = length(y_nodes);
nz_nodes = length(z_nodes);
total_nodes = nx_nodes * ny_nodes * nz_nodes;
total_elements = double(Nx) * double(Ny) * double(Nz);

% Node numbering: node_idx(ix, iy, iz) = ix + (iy-1)*nx_nodes + (iz-1)*nx_nodes*ny_nodes
node_map = @(ix, iy, iz) double(ix) + double(iy - 1) * nx_nodes + double(iz - 1) * (nx_nodes * ny_nodes);

% 3. Material Properties Assignment per Element
mat_base = lfmt.materials(config.plate.material);
k_steel = mat_base.thermal_conductivity;
rhoCp_steel = mat_base.density * mat_base.specific_heat;

has_defect = isfield(config, 'defects') && ~isempty(config.defects) && (config.defects(1).diameter_mm > 0);
if has_defect
    d = config.defects(1);
    mat_slag = lfmt.materials(d.material);
    k_slag = mat_slag.thermal_conductivity;
    rhoCp_slag = mat_slag.density * mat_slag.specific_heat;
    
    cx_m = double(d.center_x_mm) * 1e-3;
    cy_m = double(d.center_y_mm) * 1e-3;
    depth_m = double(d.depth_mm) * 1e-3;
    thick_m = double(d.thickness_mm) * 1e-3;
    radius_m = (double(d.diameter_mm) / 2.0) * 1e-3;
else
    k_slag = k_steel;
    rhoCp_slag = rhoCp_steel;
    cx_m = 0; cy_m = 0; depth_m = 0; thick_m = 0; radius_m = 0;
end

% 4. Element-to-Node Connectivity & Element Material Properties
% Pre-allocate sparse triplet arrays
entries_per_elem = 64; % 8x8
total_triplets = total_elements * entries_per_elem;

I_k = zeros(total_triplets, 1);
J_k = zeros(total_triplets, 1);
V_k = zeros(total_triplets, 1);

I_m = zeros(total_triplets, 1);
J_m = zeros(total_triplets, 1);
V_m = zeros(total_triplets, 1);

% 1D Local element stiffness and mass matrices (exact analytical integration)
dx = Lx_m / double(Nx);
dy = Ly_m / double(Ny);
dz = Lz_m / double(Nz);

k1d_x = (1.0 / dx) * [ 1.0, -1.0; -1.0,  1.0];
m1d_x = (dx / 6.0) * [ 2.0,  1.0;  1.0,  2.0];

k1d_y = (1.0 / dy) * [ 1.0, -1.0; -1.0,  1.0];
m1d_y = (dy / 6.0) * [ 2.0,  1.0;  1.0,  2.0];

k1d_z = (1.0 / dz) * [ 1.0, -1.0; -1.0,  1.0];
m1d_z = (dz / 6.0) * [ 2.0,  1.0;  1.0,  2.0];

% Reference 8-node element stiffness and consistent mass matrices (unit properties)
Ke_ref = kron(k1d_z, kron(m1d_y, m1d_x)) + ...
         kron(m1d_z, kron(k1d_y, m1d_x)) + ...
         kron(m1d_z, kron(m1d_y, k1d_x));
     
Me_ref = kron(m1d_z, kron(m1d_y, m1d_x));

elem_ptr = 0;

for iz = 1:double(Nz)
    z_center = (z_nodes(iz) + z_nodes(iz+1)) / 2.0;
    is_z_defect = has_defect && (z_center >= depth_m) && (z_center <= depth_m + thick_m);
    
    for iy = 1:double(Ny)
        y_center = (y_nodes(iy) + y_nodes(iy+1)) / 2.0;
        
        for ix = 1:double(Nx)
            x_center = (x_nodes(ix) + x_nodes(ix+1)) / 2.0;
            
            % Defect classification at element centroid
            if is_z_defect && ((x_center - cx_m)^2 + (y_center - cy_m)^2 <= radius_m^2)
                k_elem = k_slag;
                rhoCp_elem = rhoCp_slag;
            else
                k_elem = k_steel;
                rhoCp_elem = rhoCp_steel;
            end
            
            % 8 Global node indices for element (ordered: z0(x0y0, x1y0, x0y1, x1y1), z1(x0y0, x1y0, x0y1, x1y1))
            nodes_e = [
                node_map(ix,   iy,   iz);
                node_map(ix+1, iy,   iz);
                node_map(ix,   iy+1, iz);
                node_map(ix+1, iy+1, iz);
                node_map(ix,   iy,   iz+1);
                node_map(ix+1, iy,   iz+1);
                node_map(ix,   iy+1, iz+1);
                node_map(ix+1, iy+1, iz+1)
            ];
            
            % Dense 8x8 element matrices
            Ke = k_elem * Ke_ref;
            Me = rhoCp_elem * Me_ref;
            
            % Store into global triplet vectors
            [grid_j, grid_i] = meshgrid(nodes_e, nodes_e);
            idx_range = (elem_ptr * entries_per_elem + 1) : ((elem_ptr + 1) * entries_per_elem);
            
            I_k(idx_range) = grid_i(:);
            J_k(idx_range) = grid_j(:);
            V_k(idx_range) = Ke(:);
            
            I_m(idx_range) = grid_i(:);
            J_m(idx_range) = grid_j(:);
            V_m(idx_range) = Me(:);
            
            elem_ptr = elem_ptr + 1;
        end
    end
end

% Assemble global sparse matrices
K_global = sparse(I_k, J_k, V_k, total_nodes, total_nodes);
M_global = sparse(I_m, J_m, V_m, total_nodes, total_nodes);

clear I_k J_k V_k I_m J_m V_m;

% 5. Boundary Convection & Front Flux Surface Assembly
% 2D Local quadrilateral face mass matrix (4x4)
m2d_xy = kron(m1d_y, m1d_x); % Top / bottom faces
m2d_xz = kron(m1d_z, m1d_x); % Front / back faces
m2d_yz = kron(m1d_z, m1d_y); % Left / right faces

M_conv = sparse(total_nodes, total_nodes);
f_front_unit = zeros(total_nodes, 1);
f_amb = zeros(total_nodes, 1);

% Top Surface (z = 0, iz = 1): LFMT Flux + Convection
face_flux_vec = (dx * dy / 4.0) * ones(4, 1);

for iy = 1:double(Ny)
    for ix = 1:double(Nx)
        nodes_face = [
            node_map(ix,   iy,   1);
            node_map(ix+1, iy,   1);
            node_map(ix,   iy+1, 1);
            node_map(ix+1, iy+1, 1)
        ];
        
        M_conv(nodes_face, nodes_face) = M_conv(nodes_face, nodes_face) + h_conv * m2d_xy;
        f_front_unit(nodes_face) = f_front_unit(nodes_face) + face_flux_vec;
        f_amb(nodes_face) = f_amb(nodes_face) + h_conv * Tamb * face_flux_vec;
    end
end

% Bottom Surface (z = Lz, iz = Nz+1): Convection
for iy = 1:double(Ny)
    for ix = 1:double(Nx)
        nodes_face = [
            node_map(ix,   iy,   nz_nodes);
            node_map(ix+1, iy,   nz_nodes);
            node_map(ix,   iy+1, nz_nodes);
            node_map(ix+1, iy+1, nz_nodes)
        ];
        
        M_conv(nodes_face, nodes_face) = M_conv(nodes_face, nodes_face) + h_conv * m2d_xy;
        f_amb(nodes_face) = f_amb(nodes_face) + h_conv * Tamb * face_flux_vec;
    end
end

% Lateral Faces (x = 0, x = Lx, y = 0, y = Ly): Convection
face_yz_vec = (dy * dz / 4.0) * ones(4, 1);
for iz = 1:double(Nz)
    for iy = 1:double(Ny)
        % x = 0
        n_x0 = [node_map(1, iy, iz); node_map(1, iy+1, iz); node_map(1, iy, iz+1); node_map(1, iy+1, iz+1)];
        M_conv(n_x0, n_x0) = M_conv(n_x0, n_x0) + h_conv * m2d_yz;
        f_amb(n_x0) = f_amb(n_x0) + h_conv * Tamb * face_yz_vec;
        
        % x = Lx
        n_x1 = [node_map(nx_nodes, iy, iz); node_map(nx_nodes, iy+1, iz); node_map(nx_nodes, iy, iz+1); node_map(nx_nodes, iy+1, iz+1)];
        M_conv(n_x1, n_x1) = M_conv(n_x1, n_x1) + h_conv * m2d_yz;
        f_amb(n_x1) = f_amb(n_x1) + h_conv * Tamb * face_yz_vec;
    end
end

face_xz_vec = (dx * dz / 4.0) * ones(4, 1);
for iz = 1:double(Nz)
    for ix = 1:double(Nx)
        % y = 0
        n_y0 = [node_map(ix, 1, iz); node_map(ix+1, 1, iz); node_map(ix, 1, iz+1); node_map(ix+1, 1, iz+1)];
        M_conv(n_y0, n_y0) = M_conv(n_y0, n_y0) + h_conv * m2d_xz;
        f_amb(n_y0) = f_amb(n_y0) + h_conv * Tamb * face_xz_vec;
        
        % y = Ly
        n_y1 = [node_map(ix, ny_nodes, iz); node_map(ix+1, ny_nodes, iz); node_map(ix, ny_nodes, iz+1); node_map(ix+1, ny_nodes, iz+1)];
        M_conv(n_y1, n_y1) = M_conv(n_y1, n_y1) + h_conv * m2d_xz;
        f_amb(n_y1) = f_amb(n_y1) + h_conv * Tamb * face_xz_vec;
    end
end

% 6. System Matrix for Backward Euler: A = M/dt + K + M_conv
M_over_dt = (1.0 / dt_solver) * M_global;
A_system = M_over_dt + K_global + M_conv;
A_system = (A_system + A_system') / 2.0;

% Pre-factorize sparse system (Cholesky decomposition with lower triangular option)
dA = decomposition(A_system, 'chol', 'lower');

% 7. Time Stepping & Decoupled Virtual Camera Acquisition
solver_time_vector = (0:dt_solver:total_time)';
n_solver_steps = length(solver_time_vector);

cam_dt = 1.0 / cam_fps;
cam_time_vector = (0:cam_dt:total_time)';
n_cam_frames = length(cam_time_vector);

cam_x_mm = linspace(0, double(config.plate.length_mm), cam_nx);
cam_y_mm = linspace(0, double(config.plate.width_mm), cam_ny);
[mesh_X_cam, mesh_Y_cam] = ndgrid(cam_x_mm, cam_y_mm);

grid_x_mm = x_nodes * 1e3;
grid_y_mm = y_nodes * 1e3;

% Front surface node indices (z = 0, iz = 1)
[ix_grid, iy_grid] = meshgrid(1:nx_nodes, 1:ny_nodes);
front_node_indices = node_map(ix_grid, iy_grid, 1)'; % [nx_nodes, ny_nodes]

T_prev = full(Tamb * ones(total_nodes, 1));
surface_frames = zeros(n_cam_frames, cam_ny, cam_nx);

% Frame 1 is strictly initial ambient equilibrium
surface_frames(1, :, :) = Tamb;
next_cam_idx = 2;

for n = 2:n_solver_steps
    t_prev = solver_time_vector(n-1);
    t_curr = solver_time_vector(n);
    
    % Heat flux at current time step
    if t_curr <= duration
        beta = (f1 - f0) / duration;
        phase = 2 * pi * (f0 * t_curr + 0.5 * beta * t_curr^2);
        q_curr = q0 * (1.0 + sin(phase));
    else
        q_curr = 0.0;
    end
    
    % Right hand side: (M/dt)*T_prev + q_curr*f_front + f_amb
    rhs = M_over_dt * T_prev + q_curr * f_front_unit + f_amb;
    
    % Solve implicit step
    T_current = dA \ rhs;
    
    % Interpolate to camera acquisition frames falling in (t_prev, t_curr]
    while next_cam_idx <= n_cam_frames && cam_time_vector(next_cam_idx) <= t_curr + 1e-9
        t_cam = cam_time_vector(next_cam_idx);
        alpha = (t_cam - t_prev) / (t_curr - t_prev);
        alpha = max(0.0, min(1.0, alpha));
        
        T_interp = (1.0 - alpha) * T_prev + alpha * T_current;
        T_front_2d = reshape(T_interp(front_node_indices), [nx_nodes, ny_nodes]);
        
        F_interp = griddedInterpolant({grid_x_mm, grid_y_mm}, T_front_2d, 'linear', 'nearest');
        surf_sampled = F_interp(mesh_X_cam, mesh_Y_cam);
        
        % Store as [n_frames, cam_ny, cam_nx]
        surface_frames(next_cam_idx, :, :) = surf_sampled';
        next_cam_idx = next_cam_idx + 1;
    end
    
    T_prev = T_current;
end

% Catch any remaining frame at boundary
while next_cam_idx <= n_cam_frames
    T_front_2d = reshape(T_current(front_node_indices), [nx_nodes, ny_nodes]);
    F_interp = griddedInterpolant({grid_x_mm, grid_y_mm}, T_front_2d, 'linear', 'nearest');
    surf_sampled = F_interp(mesh_X_cam, mesh_Y_cam);
    surface_frames(next_cam_idx, :, :) = surf_sampled';
    next_cam_idx = next_cam_idx + 1;
end

runtime_s = toc(t_start);

% 8. Build Simulation Result Struct
geom = lfmt.geometry(config.plate, config.defects);

sim_result = struct(...
    'surface_temperature', surface_frames, ...
    'time_vector', cam_time_vector, ...
    'camera_x_mm', cam_x_mm, ...
    'camera_y_mm', cam_y_mm, ...
    'solver_dt_s', dt_solver, ...
    'camera_frame_rate_hz', cam_fps, ...
    'geometry', geom, ...
    'config', config, ...
    'runtime_s', runtime_s, ...
    'solver_name', 'MATLAB_FEM', ...
    'discretization', '3-D Trilinear Hexahedral Finite Element Method (Hex8)', ...
    'time_integration', 'Implicit Backward Euler (Pre-factorized Cholesky)', ...
    'total_nodes', total_nodes, ...
    'total_elements', total_elements, ...
    'dofs', total_nodes ...
);
end
