function metrics = compute_metrics(method_name, detection, geom, gt_mask, score_map, runtime_s, fov_mm)
% COMPUTE_METRICS Quantitative performance evaluation metrics for LFMT defect characterization.
%
% Outputs comprehensive scientific metrics:
%   IoU, Dice, Precision, Recall, Localization Error (mm/px), Diameter Error (mm),
%   Area Error (mm^2), Contrast-to-Noise Ratio (CNR), Defect Contrast,
%   Detection Success (3-tier graded), Healthy False Positive, Specificity, ROC AUC, PR AP.

if nargin < 6 || isempty(runtime_s), runtime_s = 0.0; end
if nargin < 7 || isempty(fov_mm), fov_mm = [100.0, 70.0]; end

pred_mask = logical(detection.predicted_mask);
gt_mask = logical(gt_mask);

[ny, nx] = size(gt_mask);
fov_x_mm = fov_mm(1);
fov_y_mm = fov_mm(2);
dx_mm_px = fov_x_mm / max(1, nx - 1);
dy_mm_px = fov_y_mm / max(1, ny - 1);

intersection = sum(pred_mask(:) & gt_mask(:));
union_val = sum(pred_mask(:) | gt_mask(:));
pred_sum = sum(pred_mask(:));
gt_sum = sum(gt_mask(:));

has_candidate = detection.is_detected && (pred_sum >= 3);
is_defective = geom.has_defect && (gt_sum > 0);

% 1. Overlap Metrics
if is_defective
    if union_val > 0
        iou = double(intersection) / double(union_val);
    else
        iou = 0.0;
    end
    if (pred_sum + gt_sum) > 0
        dice = (2.0 * double(intersection)) / double(pred_sum + gt_sum);
    else
        dice = 0.0;
    end
    if pred_sum > 0
        precision = double(intersection) / double(pred_sum);
    else
        precision = 0.0;
    end
    if gt_sum > 0
        recall = double(intersection) / double(gt_sum);
    else
        recall = 0.0;
    end
else
    % Healthy control plate
    iou = double(~has_candidate);
    dice = double(~has_candidate);
    precision = double(~has_candidate);
    recall = 1.0;
end

% 2. Centroid & Localization Error
if is_defective
    gt_x_mm = geom.defect.center_x_mm;
    gt_y_mm = geom.defect.center_y_mm;
else
    gt_x_mm = NaN;
    gt_y_mm = NaN;
end

pred_x_mm = detection.centroid_mm(1);
pred_y_mm = detection.centroid_mm(2);

if has_candidate && is_defective && ~isnan(pred_x_mm) && ~isnan(pred_y_mm)
    loc_err_all_mm = sqrt((pred_x_mm - gt_x_mm)^2 + (pred_y_mm - gt_y_mm)^2);
    loc_err_all_px = sqrt(((pred_x_mm - gt_x_mm) / dx_mm_px)^2 + ((pred_y_mm - gt_y_mm) / dy_mm_px)^2);
else
    loc_err_all_mm = NaN;
    loc_err_all_px = NaN;
end

% 3. Geometric Sizing Errors
if is_defective
    true_diam_mm = geom.defect.diameter_mm;
    true_radius_mm = true_diam_mm / 2.0;
    true_area_mm2 = geom.defect.area_mm2;
else
    true_diam_mm = 0.0;
    true_radius_mm = 0.0;
    true_area_mm2 = 0.0;
end

pred_diam_mm = detection.equivalent_diameter_mm;
pred_area_mm2 = detection.area_mm2;

if has_candidate && is_defective
    diam_err_mm = abs(pred_diam_mm - true_diam_mm);
    area_err_mm2 = abs(pred_area_mm2 - true_area_mm2);
else
    diam_err_mm = NaN;
    area_err_mm2 = NaN;
end

% 4. Contrast and CNR on Processed Score Map (using GT mask)
if is_defective && any(gt_mask(:)) && any(~gt_mask(:))
    mu_def = mean(score_map(gt_mask));
    mu_snd = mean(score_map(~gt_mask));
    var_def = var(score_map(gt_mask));
    var_snd = var(score_map(~gt_mask));
    
    defect_contrast = abs(mu_def - mu_snd);
    denom = sqrt(var_def + var_snd);
    if denom > 1e-12
        cnr = defect_contrast / denom;
    else
        cnr = 0.0;
    end
else
    defect_contrast = 0.0;
    cnr = 0.0;
end

% 5. Detection Success Evaluation
[is_success, tier_a, tier_b, tier_c, tier_d] = detection_success(...
    has_candidate, iou, loc_err_all_mm, true_radius_mm, is_defective);

if is_defective
    is_false_positive = false;
    specificity = 1.0;
    loc_err_detected_mm = loc_err_all_mm;
    if ~is_success
        loc_err_detected_mm = NaN;
    end
else
    is_false_positive = has_candidate;
    specificity = double(~has_candidate);
    loc_err_detected_mm = NaN;
end

% 6. ROC AUC and PR AP
if is_defective
    roc_res = compute_roc_pr_curves(score_map, gt_mask, 50);
    roc_auc = roc_res.auc_roc;
    pr_ap = roc_res.average_precision;
else
    roc_auc = NaN;
    pr_ap = NaN;
end

metrics = struct(...
    'method_name', method_name, ...
    'iou', iou, ...
    'dice', dice, ...
    'precision', precision, ...
    'recall', recall, ...
    'localization_error_detected_mm', loc_err_detected_mm, ...
    'localization_error_all_mm', loc_err_all_mm, ...
    'localization_error_mm', loc_err_detected_mm, ...
    'localization_error_px', loc_err_all_px, ...
    'true_centroid_mm', [gt_x_mm, gt_y_mm], ...
    'predicted_centroid_mm', [pred_x_mm, pred_y_mm], ...
    'diameter_error_mm', diam_err_mm, ...
    'true_diameter_mm', true_diam_mm, ...
    'predicted_diameter_mm', pred_diam_mm, ...
    'area_error_mm2', area_err_mm2, ...
    'true_area_mm2', true_area_mm2, ...
    'predicted_area_mm2', pred_area_mm2, ...
    'cnr', cnr, ...
    'defect_contrast', defect_contrast, ...
    'candidate_detected', has_candidate, ...
    'is_detected', is_success, ...
    'is_false_positive', is_false_positive, ...
    'specificity', specificity, ...
    'tier_a_detected', tier_a, ...
    'tier_b_detected', tier_b, ...
    'tier_c_detected', tier_c, ...
    'tier_d_detected', tier_d, ...
    'roc_auc', roc_auc, ...
    'pr_ap', pr_ap, ...
    'runtime_s', runtime_s ...
);
end
