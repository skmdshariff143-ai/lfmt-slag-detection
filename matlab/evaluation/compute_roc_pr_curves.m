function roc_metrics = compute_roc_pr_curves(score_map, gt_mask, n_thresholds)
% COMPUTE_ROC_PR_CURVES Computes pixel-level ROC AUC and PR AP curves across score thresholds.

if nargin < 3 || isempty(n_thresholds)
    n_thresholds = 50;
end

s_min = min(score_map(:));
s_max = max(score_map(:));

if (s_max - s_min) > 1e-12
    norm_scores = (score_map - s_min) / (s_max - s_min);
else
    norm_scores = zeros(size(score_map));
end

gt_flat = logical(gt_mask(:));
n_pos = sum(gt_flat);
n_neg = length(gt_flat) - n_pos;

if n_pos == 0
    roc_metrics = struct('auc_roc', NaN, 'average_precision', NaN);
    return;
end

thresholds = linspace(0.0, 1.0, n_thresholds);
tpr_list = zeros(n_thresholds, 1);
fpr_list = zeros(n_thresholds, 1);
prec_list = zeros(n_thresholds, 1);
rec_list = zeros(n_thresholds, 1);

scores_flat = norm_scores(:);

for i = 1:n_thresholds
    th = thresholds(i);
    pred_pos = scores_flat >= th;
    
    tp = sum(pred_pos & gt_flat);
    fp = sum(pred_pos & ~gt_flat);
    
    if n_pos > 0, tpr_list(i) = tp / double(n_pos); end
    if n_neg > 0, fpr_list(i) = fp / double(n_neg); end
    if (tp + fp) > 0
        prec_list(i) = tp / double(tp + fp);
    else
        prec_list(i) = 1.0;
    end
    rec_list(i) = tpr_list(i);
end

% ROC AUC using trapezoidal integration
[sorted_fpr, sort_idx] = sort(fpr_list, 'ascend');
sorted_tpr = tpr_list(sort_idx);
auc_roc = trapz(sorted_fpr, sorted_tpr);
auc_roc = min(1.0, max(0.0, abs(auc_roc)));

% PR Average Precision
[sorted_rec, sort_pr_idx] = sort(rec_list, 'ascend');
sorted_prec = prec_list(sort_pr_idx);
ap = trapz(sorted_rec, sorted_prec);
ap = min(1.0, max(0.0, abs(ap)));

roc_metrics = struct(...
    'auc_roc', auc_roc, ...
    'average_precision', ap, ...
    'thresholds', thresholds, ...
    'tpr', tpr_list, ...
    'fpr', fpr_list, ...
    'precision', prec_list, ...
    'recall', rec_list ...
);
end
