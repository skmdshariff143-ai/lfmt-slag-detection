function [H_diag, h_amb_vec] = buildConvectionOperator(grid, k_field, h_conv, Tamb)
% BUILDCONVECTIONOPERATOR Builds Robin convective boundary condition operator
%
% Applies convection -k*dT/dn = h*(T - Tamb) on all 6 external boundary faces.
%
% Returns:
%   H_diag:    Diagonal conductance vector (N x 1)
%   h_amb_vec: Ambient load vector (N x 1) = H_diag * Tamb

Nx = grid.Nx;
Ny = grid.Ny;
Nz = grid.Nz;
N = Nx * Ny * Nz;

node_idx = @(i, j, k) (i + (j - 1) * Nx + (k - 1) * Nx * Ny);
H_diag = zeros(N, 1);

% 1. X=0 (Left) and X=Lx (Right) faces
for k = 1:Nz
    dz = grid.dz(k);
    for j = 1:Ny
        dy = grid.dy(j);
        Area_x = dy * dz;
        
        % i = 1 (Left)
        p_left = node_idx(1, j, k);
        k_val = k_field(1, j, k);
        dx_half = 0.5 * grid.dx(1);
        G_conv = Area_x / (dx_half / k_val + 1.0 / h_conv);
        H_diag(p_left) = H_diag(p_left) + G_conv;
        
        % i = Nx (Right)
        p_right = node_idx(Nx, j, k);
        k_val = k_field(Nx, j, k);
        dx_half = 0.5 * grid.dx(Nx);
        G_conv = Area_x / (dx_half / k_val + 1.0 / h_conv);
        H_diag(p_right) = H_diag(p_right) + G_conv;
    end
end

% 2. Y=0 (Bottom) and Y=Ly (Top) faces
for k = 1:Nz
    dz = grid.dz(k);
    for i = 1:Nx
        dx = grid.dx(i);
        Area_y = dx * dz;
        
        % j = 1 (Bottom)
        p_bot = node_idx(i, 1, k);
        k_val = k_field(i, 1, k);
        dy_half = 0.5 * grid.dy(1);
        G_conv = Area_y / (dy_half / k_val + 1.0 / h_conv);
        H_diag(p_bot) = H_diag(p_bot) + G_conv;
        
        % j = Ny (Top)
        p_top = node_idx(i, Ny, k);
        k_val = k_field(i, Ny, k);
        dy_half = 0.5 * grid.dy(Ny);
        G_conv = Area_y / (dy_half / k_val + 1.0 / h_conv);
        H_diag(p_top) = H_diag(p_top) + G_conv;
    end
end

% 3. Z=0 (Front) and Z=Lz (Back) faces
for j = 1:Ny
    dy = grid.dy(j);
    for i = 1:Nx
        dx = grid.dx(i);
        Area_z = dx * dy;
        
        % k = 1 (Front surface, z=0)
        p_front = node_idx(i, j, 1);
        k_val = k_field(i, j, 1);
        dz_half = 0.5 * grid.dz(1);
        G_conv = Area_z / (dz_half / k_val + 1.0 / h_conv);
        H_diag(p_front) = H_diag(p_front) + G_conv;
        
        % k = Nz (Back surface, z=Lz)
        p_back = node_idx(i, j, Nz);
        k_val = k_field(i, j, Nz);
        dz_half = 0.5 * grid.dz(Nz);
        G_conv = Area_z / (dz_half / k_val + 1.0 / h_conv);
        H_diag(p_back) = H_diag(p_back) + G_conv;
    end
end

h_amb_vec = H_diag * Tamb;
end
