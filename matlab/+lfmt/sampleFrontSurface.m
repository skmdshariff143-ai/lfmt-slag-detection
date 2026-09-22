function [sampled_2d, cam_x_mm, cam_y_mm] = sampleFrontSurface(T_3d_state, grid, cam_nx, cam_ny)
% SAMPLEFRONTSURFACE Interpolates 3-D solution at front face (z=0) onto camera grid
%
% Output:
%   sampled_2d: 2D matrix of dimensions (cam_ny x cam_nx)

if nargin < 4, cam_ny = 28; end
if nargin < 3, cam_nx = 40; end

Lx_mm = grid.Lx_m * 1e3;
Ly_mm = grid.Ly_m * 1e3;

cam_x_mm = linspace(0, Lx_mm, cam_nx);
cam_y_mm = linspace(0, Ly_mm, cam_ny);
[mesh_X_cam, mesh_Y_cam] = ndgrid(cam_x_mm, cam_y_mm);

% Extract top layer (k=1)
if isvector(T_3d_state)
    T_front_2d = reshape(T_3d_state(1:(grid.Nx * grid.Ny)), [grid.Nx, grid.Ny]);
else
    T_front_2d = T_3d_state(:, :, 1);
end

grid_xc_mm = grid.xc * 1e3;
grid_yc_mm = grid.yc * 1e3;

F_interp = griddedInterpolant({grid_xc_mm, grid_yc_mm}, T_front_2d, 'linear', 'nearest');
surf_sampled = F_interp(mesh_X_cam, mesh_Y_cam);
sampled_2d = surf_sampled';
end
