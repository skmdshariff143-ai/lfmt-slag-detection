function [T_surf, t_vec, X_grid, Y_grid, gt_mask] = lfmt_simulate_3d_heat(plate, defect, f0, f1, T_exc, q0, T_total, dt_out)
% LFMT_SIMULATE_3D_HEAT 3-D transient heat conduction simulation in MATLAB.

nx = 40; ny = 28; nz = 16;
dx = plate.Lx / nx;
dy = plate.Ly / ny;
dz = plate.Lz / nz;

x = ((1:nx) - 0.5) * dx;
y = ((1:ny) - 0.5) * dy;
z = ((1:nz) - 0.5) * dz;
[X_grid, Y_grid] = meshgrid(x, y);

% Initialize 3D property fields
k_field = plate.k * ones(nz, ny, nx);
rho_field = plate.rho * ones(nz, ny, nx);
Cp_field = plate.Cp * ones(nz, ny, nx);

[X3, Y3, Z3] = meshgrid(x, y, z);
X3 = permute(X3, [3, 2, 1]);
Y3 = permute(Y3, [3, 2, 1]);
Z3 = permute(Z3, [3, 2, 1]);

% Identify defect region
dist_xy_sq = (X3 - defect.cx).^2 + (Y3 - defect.cy).^2;
inc_mask = (dist_xy_sq <= (defect.diam/2)^2) & (Z3 >= defect.depth) & (Z3 <= (defect.depth + defect.thick));

k_field(inc_mask) = defect.k;
rho_field(inc_mask) = defect.rho;
Cp_field(inc_mask) = defect.Cp;
Cv_field = rho_field .* Cp_field;

% Ground truth 2D mask
gt_dist_sq = (X_grid - defect.cx).^2 + (Y_grid - defect.cy).^2;
gt_mask = gt_dist_sq <= (defect.diam/2)^2;

% Time parameters & stability
alpha_max = plate.k / (plate.rho * plate.Cp);
dt_crit = 0.40 / (alpha_max * (1/dx^2 + 1/dy^2 + 1/dz^2));
n_sub = ceil(dt_out / dt_crit);
dt_sub = dt_out / n_sub;

t_vec = 0:dt_out:T_total;
n_frames = length(t_vec);
beta = (f1 - f0) / T_exc;

T_amb = 293.15;
h_conv = 10.0;
T = T_amb * ones(nz, ny, nx);
T_surf = zeros(n_frames, ny, nx);
T_surf(1, :, :) = T(1, :, :);

for frame = 2:n_frames
    t_start = t_vec(frame-1);
    for s = 1:n_sub
        t_curr = t_start + (s-1)*dt_sub;
        if t_curr <= T_exc
            phi = 2*pi*(f0*t_curr + 0.5*beta*t_curr^2);
            q_flux = q0 * (1 + sin(phi));
        else
            q_flux = 0.0;
        end
        
        % Finite difference diffusion step
        T_new = T;
        for iz = 1:nz
            for iy = 1:ny
                for ix = 1:nx
                    t_val = T(iz, iy, ix);
                    
                    % X-flux
                    if ix > 1, fx_m = k_field(iz,iy,ix-1)*(T(iz,iy,ix-1)-t_val)/dx^2; else, fx_m = -h_conv*(t_val-T_amb)/dx; end
                    if ix < nx, fx_p = k_field(iz,iy,ix)*(T(iz,iy,ix+1)-t_val)/dx^2; else, fx_p = -h_conv*(t_val-T_amb)/dx; end
                    
                    % Y-flux
                    if iy > 1, fy_m = k_field(iz,iy-1,ix)*(T(iz,iy-1,ix)-t_val)/dy^2; else, fy_m = -h_conv*(t_val-T_amb)/dy; end
                    if iy < ny, fy_p = k_field(iz,iy,ix)*(T(iz,iy+1,ix)-t_val)/dy^2; else, fy_p = -h_conv*(t_val-T_amb)/dy; end
                    
                    % Z-flux
                    if iz > 1, fz_m = k_field(iz-1,iy,ix)*(T(iz-1,iy,ix)-t_val)/dz^2; else, fz_m = (q_flux - h_conv*(t_val-T_amb))/dz; end
                    if iz < nz, fz_p = k_field(iz,iy,ix)*(T(iz+1,iy,ix)-t_val)/dz^2; else, fz_p = -h_conv*(t_val-T_amb)/dz; end
                    
                    div_q = (fx_m + fx_p) + (fy_m + fy_p) + (fz_m + fz_p);
                    T_new(iz, iy, ix) = t_val + dt_sub * (div_q / Cv_field(iz, iy, ix));
                end
            end
        end
        T = T_new;
    end
    T_surf(frame, :, :) = T(1, :, :);
end
end
