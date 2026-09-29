function [T_cam, t_cam, x_cam_mm, y_cam_mm] = camera(T_surf_raw, t_solver, x_nodes_m, y_nodes_m, cam_nx, cam_ny, fps, total_time_s)
% CAMERA Decoupled Virtual IR Camera spatial and temporal sampling.
%
% Inputs:
%   T_surf_raw - 2D or 3D surface temperature from solver
%   t_solver   - Time vector of the solver
%   x_nodes_m  - Spatial coordinates in X [m]
%   y_nodes_m  - Spatial coordinates in Y [m]
%   cam_nx     - Number of camera pixels along X
%   cam_ny     - Number of camera pixels along Y
%   fps        - Camera frame rate [Hz]
%   total_time_s - Total observation duration [s]
%
% Output:
%   T_cam      - 3D array [n_frames, cam_ny, cam_nx]
%   t_cam      - Camera acquisition time vector [s]
%   x_cam_mm   - Camera physical grid coordinates in X [mm]
%   y_cam_mm   - Camera physical grid coordinates in Y [mm]

if nargin < 5 || isempty(cam_nx), cam_nx = 64; end
if nargin < 6 || isempty(cam_ny), cam_ny = 64; end
if nargin < 7 || isempty(fps), fps = 25.0; end
if nargin < 8 || isempty(total_time_s), total_time_s = 10.0; end

cam_dt = 1.0 / fps;
t_cam = (0:cam_dt:total_time_s)';
n_frames = length(t_cam);

Lx_mm = max(x_nodes_m) * 1e3;
Ly_mm = max(y_nodes_m) * 1e3;

x_cam_mm = linspace(0, Lx_mm, cam_nx);
y_cam_mm = linspace(0, Ly_mm, cam_ny);
[mesh_X_cam, mesh_Y_cam] = ndgrid(x_cam_mm, y_cam_mm);

% If already sampled at camera resolution:
if size(T_surf_raw, 1) == n_frames && size(T_surf_raw, 2) == cam_ny && size(T_surf_raw, 3) == cam_nx
    T_cam = T_surf_raw;
    return;
end

% Spatial and temporal interpolation
x_nodes_mm = x_nodes_m * 1e3;
y_nodes_mm = y_nodes_m * 1e3;

T_cam = zeros(n_frames, cam_ny, cam_nx);

for k = 1:n_frames
    t_target = t_cam(k);
    
    % Find solver time bracket
    if t_target <= t_solver(1)
        frame_raw = squeeze(T_surf_raw(1, :, :));
    elseif t_target >= t_solver(end)
        frame_raw = squeeze(T_surf_raw(end, :, :));
    else
        idx = find(t_solver <= t_target, 1, 'last');
        idx_next = min(length(t_solver), idx + 1);
        t1 = t_solver(idx);
        t2 = t_solver(idx_next);
        if t2 > t1
            alpha = (t_target - t1) / (t2 - t1);
            f1 = squeeze(T_surf_raw(idx, :, :));
            f2 = squeeze(T_surf_raw(idx_next, :, :));
            frame_raw = (1.0 - alpha) * f1 + alpha * f2;
        else
            frame_raw = squeeze(T_surf_raw(idx, :, :));
        end
    end
    
    % Spatial interpolation onto camera sensor
    if size(frame_raw, 1) == length(y_nodes_mm) && size(frame_raw, 2) == length(x_nodes_mm)
        frame_grid = frame_raw';
    else
        frame_grid = frame_raw;
    end
    F = griddedInterpolant({x_nodes_mm, y_nodes_mm}, frame_grid, 'linear', 'nearest');
    interp_2d = F(mesh_X_cam, mesh_Y_cam);
    T_cam(k, :, :) = interp_2d';
end
end
