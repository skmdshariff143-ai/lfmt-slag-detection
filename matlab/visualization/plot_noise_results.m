function fig = plot_noise_results(summary_by_noise_table, save_path)
% PLOT_NOISE_RESULTS Plots Detection Rate and CNR vs Noise Conditions (Clean, 30dB, 25dB, 20dB).

if nargin < 2 || isempty(save_path)
    matlab_dir = fileparts(fileparts(mfilename('fullpath')));
    save_path = fullfile(matlab_dir, 'results', 'figures', 'fig16_noise_robustness.png');
end

tbl = summary_by_noise_table;
methods = unique(tbl.method_name);
colors = {'#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'};
markers = {'o-', 's-', '^-', 'd-', 'v-'};

noise_order = {'clean', '30dB', '25dB', '20dB'};

fig = figure('Visible', 'off', 'Position', [100, 100, 1000, 450], 'Color', 'w');

% 1. Detection Rate vs Noise
subplot(1, 2, 1);
hold on;
for m = 1:length(methods)
    meth = methods{m};
    sub = tbl(strcmp(tbl.method_name, meth), :);
    y_vals = zeros(1, length(noise_order));
    for n = 1:length(noise_order)
        row = sub(strcmp(string(sub.snr_condition), noise_order{n}), :);
        if ~isempty(row)
            y_vals(n) = row.detection_rate_pct(1);
        else
            y_vals(n) = NaN;
        end
    end
    plot(1:4, y_vals, markers{m}, 'Color', colors{m}, 'LineWidth', 1.8, 'MarkerSize', 7, 'DisplayName', meth);
end
grid on;
set(gca, 'XTick', 1:4, 'XTickLabel', noise_order);
xlabel('Noise Level (AWGN SNR)', 'FontSize', 11, 'FontWeight', 'bold');
ylabel('Detection Rate (%)', 'FontSize', 11, 'FontWeight', 'bold');
title('Noise Robustness: Detection Rate', 'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'southwest', 'FontSize', 9);
ylim([-5, 105]);

% 2. Mean CNR vs Noise
subplot(1, 2, 2);
hold on;
for m = 1:length(methods)
    meth = methods{m};
    sub = tbl(strcmp(tbl.method_name, meth), :);
    y_vals = zeros(1, length(noise_order));
    for n = 1:length(noise_order)
        row = sub(strcmp(string(sub.snr_condition), noise_order{n}), :);
        if ~isempty(row)
            y_vals(n) = row.mean_cnr(1);
        else
            y_vals(n) = NaN;
        end
    end
    plot(1:4, y_vals, markers{m}, 'Color', colors{m}, 'LineWidth', 1.8, 'MarkerSize', 7, 'DisplayName', meth);
end
grid on;
set(gca, 'XTick', 1:4, 'XTickLabel', noise_order);
xlabel('Noise Level (AWGN SNR)', 'FontSize', 11, 'FontWeight', 'bold');
ylabel('Contrast-to-Noise Ratio (CNR)', 'FontSize', 11, 'FontWeight', 'bold');
title('Noise Robustness: CNR Degradation', 'FontSize', 12, 'FontWeight', 'bold');

sgtitle('Thermal Signal Processing Robustness Under AWGN Camera Noise', 'FontSize', 14, 'FontWeight', 'bold');

save_dir = fileparts(save_path);
if ~exist(save_dir, 'dir'), mkdir(save_dir); end
exportgraphics(fig, save_path, 'Resolution', 300);
close(fig);
fprintf('Noise robustness figure saved to: %s\n', save_path);
end
