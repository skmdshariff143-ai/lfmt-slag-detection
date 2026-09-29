function fig = plot_diameter_results(summary_by_diameter_table, save_path)
% PLOT_DIAMETER_RESULTS Plots Detection Rate and IoU vs Defect Diameter for all 5 methods.

if nargin < 2 || isempty(save_path)
    matlab_dir = fileparts(fileparts(mfilename('fullpath')));
    save_path = fullfile(matlab_dir, 'results', 'figures', 'fig12_diameter_study.png');
end

tbl = summary_by_diameter_table;
methods = unique(tbl.method_name);
colors = {'#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'};
markers = {'o-', 's-', '^-', 'd-', 'v-'};

fig = figure('Visible', 'off', 'Position', [100, 100, 1000, 450], 'Color', 'w');

% 1. Detection Rate vs Diameter
subplot(1, 2, 1);
hold on;
for m = 1:length(methods)
    meth = methods{m};
    sub = tbl(strcmp(tbl.method_name, meth), :);
    sub = sortrows(sub, 'diameter_mm');
    plot(sub.diameter_mm, sub.detection_rate_pct, markers{m}, 'Color', colors{m}, 'LineWidth', 1.8, 'MarkerSize', 6, 'DisplayName', meth);
end
grid on;
xlabel('Defect Diameter D (mm)', 'FontSize', 11, 'FontWeight', 'bold');
ylabel('Detection Rate (%)', 'FontSize', 11, 'FontWeight', 'bold');
title('Detection Rate vs. Diameter', 'FontSize', 12, 'FontWeight', 'bold');
legend('Location', 'southeast', 'FontSize', 9);
ylim([-5, 105]);

% 2. Mean IoU vs Diameter
subplot(1, 2, 2);
hold on;
for m = 1:length(methods)
    meth = methods{m};
    sub = tbl(strcmp(tbl.method_name, meth), :);
    sub = sortrows(sub, 'diameter_mm');
    plot(sub.diameter_mm, sub.mean_iou, markers{m}, 'Color', colors{m}, 'LineWidth', 1.8, 'MarkerSize', 6, 'DisplayName', meth);
end
grid on;
xlabel('Defect Diameter D (mm)', 'FontSize', 11, 'FontWeight', 'bold');
ylabel('Mean IoU', 'FontSize', 11, 'FontWeight', 'bold');
title('Segmentation IoU vs. Diameter', 'FontSize', 12, 'FontWeight', 'bold');
ylim([-0.05, 1.05]);

sgtitle('Defect Size Sensitivity & Spatial Resolution across Processing Methods', 'FontSize', 14, 'FontWeight', 'bold');

save_dir = fileparts(save_path);
if ~exist(save_dir, 'dir'), mkdir(save_dir); end
exportgraphics(fig, save_path, 'Resolution', 300);
close(fig);
fprintf('Diameter study figure saved to: %s\n', save_path);
end
