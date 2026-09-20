%% LFMT Slag Detection — Academic MATLAB Pipeline
% Linear Frequency-Modulated Infrared Thermography for Mild Steel Weld Defect NDT
%
% Toolboxes required:
% - Signal Processing Toolbox (for FFT matched filtering / chirp)
% - Image Processing Toolbox (for connected component segmentation)
% - Statistics and Machine Learning Toolbox (for PCA / SVD / Random Projection)

clear; clc; close all;
addpath(genpath('.'));

fprintf('=======================================================\n');
fprintf('LFMT Subsurface Slag Detection MATLAB Academic Pipeline\n');
fprintf('=======================================================\n');

%% 1. Physical & Geometric Parameters
plate.Lx = 0.100;     % Length [m] (100 mm)
plate.Ly = 0.070;     % Width [m] (70 mm)
plate.Lz = 0.0023;    % Thickness [m] (2.3 mm)
plate.k = 51.9;       % Mild steel thermal conductivity [W/(m*K)]
plate.rho = 7850;     % Density [kg/m^3]
plate.Cp = 486;       % Specific heat [J/(kg*K)]

% Subsurface Slag Inclusion
defect.cx = 0.050;    % Center X [m]
defect.cy = 0.035;    % Center Y [m]
defect.depth = 0.0006;% Depth [m] (0.6 mm)
defect.diam = 0.008;  % Diameter [m] (8.0 mm)
defect.thick = 0.0005;% Thickness [m] (0.5 mm)
defect.k = 1.20;      % Slag conductivity [W/(m*K)]
defect.rho = 2800;    % Slag density [kg/m^3]
defect.Cp = 850;      % Slag specific heat [J/(kg*K)]

%% 2. LFMT Excitation Parameters
f0 = 0.05;            % Start frequency [Hz]
f1 = 0.50;            % End frequency [Hz]
T_exc = 10.0;         % Chirp duration [s]
q0 = 5000;            % Heat flux [W/m^2]
T_total = 12.0;       % Total observation time [s]
dt = 0.1;             % Output sampling step [s]

%% 3. Forward Thermal Simulation (3D Transient Heat Conduction)
fprintf('Simulating 3-D transient heat conduction...\n');
[T_surf, t_vec, X_grid, Y_grid, gt_mask] = lfmt_simulate_3d_heat(plate, defect, f0, f1, T_exc, q0, T_total, dt);

%% 4. Thermogram Signal Processing
fprintf('Applying Matched Filtering / Pulse Compression...\n');
mf_map = lfmt_matched_filter(T_surf, t_vec, f0, f1, T_exc, q0);

fprintf('Applying Principal Component Thermography (PCT)...\n');
[pct_map, eof_all, explained_var] = lfmt_pct(T_surf, gt_mask);

fprintf('Applying Random Projection Technique (RPT)...\n');
rpt_map = lfmt_rpt(T_surf, 6, gt_mask);

%% 5. Visualization & Metrics
fprintf('Generating comparison plots...\n');
lfmt_plot_comparison(X_grid*1e3, Y_grid*1e3, gt_mask, mf_map, pct_map, rpt_map, defect);

fprintf('Academic MATLAB verification completed successfully.\n');
