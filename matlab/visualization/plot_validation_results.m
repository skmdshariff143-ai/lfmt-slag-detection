function fig = plot_validation_results(mesh_table, dt_table, sens_table, save_path)
% PLOT_VALIDATION_RESULTS Plots numerical mesh convergence, dt convergence, and parameter sensitivity.

if nargin < 4 || isempty(save_path)
    matlab_dir = fileparts(fileparts(mfilename('fullpath')));
    save_path = fullfile(matlab_dir, 'results', 'figures', 'fig18_validation_summary.png');
end

fig = figure('Visible', 'off', 'Position', [100, 100, 1400, 450], 'Color', 'w');

% 1. Mesh Convergence
subplot(1, 3, 1);
if ~isempty(mesh_table)
    plot(mesh_table.total_elements, mesh_table.peak_temp_K, 'bo-', 'LineWidth', 2.0, 'MarkerSize', 8);
    grid on;
    xlabel('Number of Hex8 Elements', 'FontSize', 11, 'FontWeight', 'bold');
    ylabel('Peak Surface Temperature (K)', 'FontSize', 11, 'FontWeight', 'bold');
    title('Mesh Spatial Convergence', 'FontSize', 12, 'FontWeight', 'bold');
end

% 2. Timestep Convergence
subplot(1, 3, 2);
if ~isempty(dt_table)
    plot(dt_table.dt_s, dt_table.peak_temp_K, 'rs-', 'LineWidth', 2.0, 'MarkerSize', 8);
    grid on;
    xlabel('Solver Timestep \Delta t (s)', 'FontSize', 11, 'FontWeight', 'bold');
    ylabel('Peak Surface Temperature (K)', 'FontSize', 11, 'FontWeight', 'bold');
    title('Time-Step Temporal Convergence', 'FontSize', 12, 'FontWeight', 'bold');
end

% 3. Parameter Sensitivity (Bar chart)
subplot(1, 3, 3);
if ~isempty(sens_table)
    labels = cell(height(sens_table), 1);
    for i = 1:height(sens_table)
        labels{i} = sprintf('%s (%+d%%)', sens_table.parameter(i), int32(sens_table.delta_percent(i)));
    end
    bar(1:length(labels), sens_table.matched_filter_cnr, 'FaceColor', '#2ca02c');
    set(gca, 'XTick', 1:length(labels), 'XTickLabel', labels);
    xtickangle(45);
    grid on;
    xlabel('Parameter Variation', 'FontSize', 10, 'FontWeight', 'bold');
    ylabel('Matched Filter CNR', 'FontSize', 11, 'FontWeight', 'bold');
    title('Parameter Sensitivity (CNR)', 'FontSize', 12, 'FontWeight', 'bold');
end

sgtitle('Numerical Verification & Physical Parameter Sensitivity', 'FontSize', 14, 'FontWeight', 'bold');

save_dir = fileparts(save_path);
if ~exist(save_dir, 'dir'), mkdir(save_dir); end
exportgraphics(fig, save_path, 'Resolution', 300);
close(fig);
fprintf('Validation summary figure saved to: %s\n', save_path);
end
