function fig_path = generate_final_waveform_figure(cfg, out_path)
% GENERATE_FINAL_WAVEFORM_FIGURE Creates publication-grade LFMT excitation waveform figure.
%
% Generates:
%   - Top Subplot: LFMT Surface Heat Flux q(t) = q0 * [1 + sin(phi(t))]
%   - Bottom Subplot: Instantaneous Chirp Frequency f(t) = f0 + (beta)*t
%
% Output: 300 DPI publication PNG

if nargin < 1 || isempty(cfg)
    root_dir = fileparts(fileparts(mfilename('fullpath')));
    addpath(fullfile(root_dir, 'config'));
    cfg = default_config();
end

if nargin < 2 || isempty(out_path)
    root_dir = fileparts(fileparts(mfilename('fullpath')));
    out_dir = fullfile(root_dir, 'results', 'figures');
    if ~exist(out_dir, 'dir'), mkdir(out_dir); end
    out_path = fullfile(out_dir, 'final_lfmt_waveform.png');
end

f0 = cfg.excitation.f0_hz;
f1 = cfg.excitation.f1_hz;
q0 = cfg.excitation.q0_w_m2;
T_dur = cfg.excitation.duration_s;
T_obs = cfg.simulation.total_time_s;

t = linspace(0, T_obs, 2000);
q = zeros(size(t));
f_inst = zeros(size(t));

beta = (f1 - f0) / T_dur;

for i = 1:length(t)
    ti = t(i);
    if ti <= T_dur
        f_inst(i) = f0 + beta * ti;
        phi = 2 * pi * (f0 * ti + 0.5 * beta * ti^2);
        q(i) = q0 * (1.0 + sin(phi));
    else
        f_inst(i) = 0;
        q(i) = 0;
    end
end

hFig = figure('Name', 'LFMT Excitation Waveform', 'Position', [100, 100, 900, 600], ...
    'Color', 'w', 'Visible', 'off');

% Top Subplot: Heat Flux
subplot(2, 1, 1);
plot(t, q, 'Color', [0.85, 0.20, 0.10], 'LineWidth', 1.8);
hold on;
xline(T_dur, 'k--', 'Excitation End (t = 10 s)', 'LineWidth', 1.2, 'LabelOrientation', 'aligned', 'LabelVerticalAlignment', 'bottom');
yline(q0, 'b:', 'Mean Power (q0)', 'LineWidth', 1.1);
hold off;
grid on;
set(gca, 'FontSize', 10, 'LineWidth', 1.0, 'XColor', [0.2, 0.2, 0.2], 'YColor', [0.2, 0.2, 0.2]);
title('Linear Frequency-Modulated Thermal (LFMT) Heat Flux Waveform q(t)', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Time t [s]', 'FontSize', 10);
ylabel('Heat Flux q(t) [W/m^2]', 'FontSize', 10);
xlim([0, T_obs]);
ylim([0, 2.1 * q0]);
legend({'q(t) = q_0 [1 + sin(2\pi(f_0 t + \beta t^2/2))]', 'Heating Duration Boundary', 'Baseline DC Level'}, ...
    'Location', 'northeast', 'FontSize', 9);

% Bottom Subplot: Instantaneous Frequency
subplot(2, 1, 2);
t_active = t(t <= T_dur);
f_active = f_inst(t <= T_dur);
plot(t_active, f_active, 'Color', [0.10, 0.45, 0.85], 'LineWidth', 2.0);
hold on;
plot([T_dur, T_obs], [0, 0], 'Color', [0.5, 0.5, 0.5], 'LineWidth', 1.5, 'LineStyle', '--');
xline(T_dur, 'k--', 'LineWidth', 1.2);
scatter([0, T_dur], [f0, f1], 60, [0.85, 0.20, 0.10], 'filled');
text(0.2, f0 + 0.03, sprintf('f_0 = %.2f Hz', f0), 'FontSize', 9, 'FontWeight', 'bold');
text(T_dur - 1.5, f1 - 0.03, sprintf('f_1 = %.2f Hz', f1), 'FontSize', 9, 'FontWeight', 'bold');
hold off;
grid on;
set(gca, 'FontSize', 10, 'LineWidth', 1.0, 'XColor', [0.2, 0.2, 0.2], 'YColor', [0.2, 0.2, 0.2]);
title('Instantaneous Excitation Modulation Frequency f(t) = f_0 + \beta t', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Time t [s]', 'FontSize', 10);
ylabel('Instantaneous Frequency f(t) [Hz]', 'FontSize', 10);
xlim([0, T_obs]);
ylim([0, f1 * 1.2]);
legend({'Chirp Frequency f(t) = f_0 + \beta t', 'Cooling / Observation Phase', 'Bandwidth Limits'}, ...
    'Location', 'northwest', 'FontSize', 9);

exportgraphics(hFig, out_path, 'Resolution', 300);
close(hFig);

fig_path = out_path;
fprintf('Exported publication LFMT waveform figure: %s (300 DPI)\n', out_path);
end
