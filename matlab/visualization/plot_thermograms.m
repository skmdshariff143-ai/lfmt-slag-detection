function fig = plot_thermograms(sim_result, save_path)
% PLOT_THERMOGRAMS Generates publication-quality thermogram evolution and thermal curves.
%
% Output:
%   Figure showing spatial thermogram snapshots and temporal temperature curves.

if nargin < 2 || isempty(save_path)
    matlab_dir = fileparts(fileparts(mfilename('fullpath')));
    save_path = fullfile(matlab_dir, 'results', 'figures', 'fig4_thermogram_evolution.png');
end

T_surf = sim_result.surface_temperature;
t_vec = sim_result.time_vector;
[n_frames, ny, nx] = size(T_surf);

fig = figure('Visible', 'off', 'Position', [100, 100, 1200, 800], 'Color', 'w');

% 4 Time Snapshot indices (e.g. t = 0s, 2.5s, 5.0s, 10.0s)
target_times = [0.0, 2.5, 5.0, 10.0];
snapshot_indices = zeros(1, 4);
for i = 1:4
    [~, snapshot_indices(i)] = min(abs(t_vec - target_times(i)));
end

% Subplots 1-4: Thermogram Snapshots
for i = 1:4
    idx = snapshot_indices(i);
    subplot(2, 4, i);
    imagesc(sim_result.camera_x_mm, sim_result.camera_y_mm, squeeze(T_surf(idx, :, :)));
    axis image;
    colormap(gca, 'hot');
    colorbar;
    title(sprintf('t = %.1f s', t_vec(idx)), 'FontSize', 11, 'FontWeight', 'bold');
    xlabel('X (mm)', 'FontSize', 10);
    ylabel('Y (mm)', 'FontSize', 10);
end

% Subplot 5-6: Temperature-Time Curves
subplot(2, 4, [5, 6]);
cx_idx = round(nx / 2);
cy_idx = round(ny / 2);
T_defect = squeeze(T_surf(:, cy_idx, cx_idx));
T_sound = squeeze(T_surf(:, 2, 2));

plot(t_vec, T_defect, 'r-', 'LineWidth', 2.0, 'DisplayName', 'Defect Center (50, 35 mm)');
hold on;
plot(t_vec, T_sound, 'b--', 'LineWidth', 1.8, 'DisplayName', 'Sound Background (Corner)');
grid on;
xlabel('Time t (s)', 'FontSize', 11, 'FontWeight', 'bold');
ylabel('Temperature T (K)', 'FontSize', 11, 'FontWeight', 'bold');
title('Front-Surface Transient Temperature Profiles', 'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'northwest', 'FontSize', 10);

% Subplot 7-8: Differential Contrast Delta T(t)
subplot(2, 4, [7, 8]);
delta_T = T_defect - T_sound;
plot(t_vec, delta_T, 'm-', 'LineWidth', 2.0, 'DisplayName', '\Delta T(t) = T_{def} - T_{snd}');
grid on;
xlabel('Time t (s)', 'FontSize', 11, 'FontWeight', 'bold');
ylabel('Differential Contrast \Delta T (K)', 'FontSize', 11, 'FontWeight', 'bold');
title('Transient Differential Thermal Contrast', 'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'northwest', 'FontSize', 10);

sgtitle('LFMT Thermal Diffusion & Front-Surface Transient Response', 'FontSize', 14, 'FontWeight', 'bold');

% Save at >= 300 DPI
save_dir = fileparts(save_path);
if ~exist(save_dir, 'dir'), mkdir(save_dir); end
exportgraphics(fig, save_path, 'Resolution', 300);
close(fig);
fprintf('Thermogram figure saved to: %s\n', save_path);
end
