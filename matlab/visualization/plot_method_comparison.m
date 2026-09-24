function fig = plot_method_comparison(processed_results, sim_result, save_path)
% PLOT_METHOD_COMPARISON Side-by-side comparison of 5 signal processing methods.
%
% Displays:
%   Raw Contrast | Matched Filter | PCT | SPCT | RPT
%   Overlaid with detected binary candidate contour (green) and GT defect (red dashed).

if nargin < 3 || isempty(save_path)
    matlab_dir = fileparts(fileparts(mfilename('fullpath')));
    save_path = fullfile(matlab_dir, 'results', 'figures', 'fig10_method_comparison.png');
end

methods = {'Raw Contrast', 'Matched Filter', 'PCT', 'SPCT', 'RPT'};
method_keys = {'RAW', 'MF', 'PCT', 'SPCT', 'RPT'};

fig = figure('Visible', 'off', 'Position', [50, 100, 1600, 400], 'Color', 'w');

x_mm = sim_result.camera_x_mm;
y_mm = sim_result.camera_y_mm;

% Ground truth circle coordinates
has_def = sim_result.geometry.has_defect;
if has_def
    cx = sim_result.geometry.defect.center_x_mm;
    cy = sim_result.geometry.defect.center_y_mm;
    r = sim_result.geometry.defect.diameter_mm / 2.0;
    theta = linspace(0, 2*pi, 100);
    gt_x = cx + r * cos(theta);
    gt_y = cy + r * sin(theta);
end

for i = 1:5
    subplot(1, 5, i);
    key = method_keys{i};
    
    if isfield(processed_results, key)
        res_proc = processed_results.(key);
        score_map = res_proc.normalized_map;
        det_res = res_proc.detection;
    else
        score_map = zeros(length(y_mm), length(x_mm));
        det_res = struct('is_detected', false);
    end
    
    imagesc(x_mm, y_mm, score_map);
    axis image;
    colormap(gca, 'jet');
    colorbar;
    hold on;
    
    % GT defect circle overlay (Red Dashed)
    if has_def
        plot(gt_x, gt_y, 'r--', 'LineWidth', 2.0, 'DisplayName', 'True Inclusion');
    end
    
    % Detected Candidate Centroid & Boundary (Cyan marker)
    if det_res.is_detected && ~isnan(det_res.centroid_mm(1))
        plot(det_res.centroid_mm(1), det_res.centroid_mm(2), 'c+', 'MarkerSize', 10, 'LineWidth', 2.0, 'DisplayName', 'Pred Centroid');
        if isfield(det_res, 'metrics') && isfield(det_res.metrics, 'iou')
            iou_val = det_res.metrics.iou;
            cnr_val = det_res.metrics.cnr;
            title_str = sprintf('%s\nIoU: %.2f | CNR: %.2f', methods{i}, iou_val, cnr_val);
        else
            title_str = methods{i};
        end
    else
        title_str = sprintf('%s\n(Not Detected)', methods{i});
    end
    
    title(title_str, 'FontSize', 11, 'FontWeight', 'bold');
    xlabel('X (mm)', 'FontSize', 9);
    ylabel('Y (mm)', 'FontSize', 9);
end

sgtitle('Blind Thermographic Signal Processing & Defect Isolation Comparison', 'FontSize', 13, 'FontWeight', 'bold');

% Save at >= 300 DPI
save_dir = fileparts(save_path);
if ~exist(save_dir, 'dir'), mkdir(save_dir); end
exportgraphics(fig, save_path, 'Resolution', 300);
close(fig);
fprintf('Method comparison figure saved to: %s\n', save_path);
end
