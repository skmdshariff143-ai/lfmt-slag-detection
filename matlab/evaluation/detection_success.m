function [is_success, tier_a, tier_b, tier_c, tier_d] = detection_success(has_candidate, iou, loc_err_mm, true_radius_mm, is_defective)
% DETECTION_SUCCESS Formal scientific 3-criterion detection success evaluation.
%
% A run is a Successful Detection iff:
%   1. Defect candidate isolated (area >= 3 px)
%   2. Spatial overlap (IoU > 0 and Dice > 0)
%   3. Centroid localization tolerance: loc_err_mm <= max(R_true, 5.0 mm)
%
% For healthy plates: any candidate is recorded as a False Alarm.

if ~is_defective
    % Healthy control specimen
    is_success = false;
    tier_a = false;
    tier_b = false;
    tier_c = false;
    tier_d = false;
    return;
end

if isnan(loc_err_mm) || ~has_candidate
    is_success = false;
    tier_a = false;
    tier_b = false;
    tier_c = false;
    tier_d = false;
    return;
end

tol_a = max(true_radius_mm, 5.0);
tol_b = max(true_radius_mm, 3.0);
tol_c = max(true_radius_mm, 1.0);
tol_d = max(0.5 * true_radius_mm, 0.5);

tier_a = has_candidate && (iou > 0.0) && (loc_err_mm <= tol_a);
tier_b = has_candidate && (iou >= 0.10) && (loc_err_mm <= tol_b);
tier_c = has_candidate && (iou >= 0.25) && (loc_err_mm <= tol_c);
tier_d = has_candidate && (iou >= 0.50) && (loc_err_mm <= tol_d);

is_success = tier_a;
end
