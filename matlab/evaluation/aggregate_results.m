function summaries = aggregate_results(eval_records, output_dir)
% AGGREGATE_RESULTS Aggregates evaluation records into structured scientific summary tables.
%
% Generates:
%   - summary_by_method.csv
%   - summary_by_depth.csv
%   - summary_by_diameter.csv
%   - summary_by_noise.csv
%   - healthy_specificity.csv
%   - max_detectable_depth.csv
%   - full_evaluation_records.csv

if nargin < 2 || isempty(output_dir)
    matlab_dir = fileparts(fileparts(mfilename('fullpath')));
    output_dir = fullfile(matlab_dir, 'results', 'tables');
end
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

if isstruct(eval_records)
    eval_table = struct2table(eval_records);
else
    eval_table = eval_records;
end

% Save full evaluation records
full_csv = fullfile(output_dir, 'full_evaluation_records.csv');
writetable(eval_table, full_csv);

% Filter defective cases for defect-related metrics
defective_table = eval_table(eval_table.diameter_mm > 0, :);
healthy_table = eval_table(eval_table.diameter_mm == 0, :);

methods = unique(eval_table.method_name);

% 1. Summary by Method
method_rows = [];
for m = 1:length(methods)
    meth = methods{m};
    sub = defective_table(strcmp(defective_table.method_name, meth), :);
    
    sub_detected = sub(sub.is_detected, :);
    mean_loc_detected = mean(sub_detected.localization_error_mm);
    
    row = struct(...
        'method_name', string(meth), ...
        'total_evaluations', height(sub), ...
        'detection_rate_pct', mean(double(sub.is_detected)) * 100.0, ...
        'mean_iou', mean(sub.iou), ...
        'mean_dice', mean(sub.dice), ...
        'mean_cnr', mean(sub.cnr), ...
        'mean_loc_error_mm', mean_loc_detected, ...
        'mean_diameter_error_mm', mean(sub_detected.diameter_error_mm), ...
        'mean_runtime_s', mean(sub.runtime_s) ...
    );
    method_rows = [method_rows; row]; %#ok<AGROW>
end
summary_by_method = struct2table(method_rows);
writetable(summary_by_method, fullfile(output_dir, 'summary_by_method.csv'));

% 2. Summary by Depth
depths = sort(unique(defective_table.depth_mm), 'ascend');
depth_rows = [];
for m = 1:length(methods)
    meth = methods{m};
    for d = 1:length(depths)
        dep = depths(d);
        sub = defective_table(strcmp(defective_table.method_name, meth) & (defective_table.depth_mm == dep), :);
        sub_det = sub(sub.is_detected, :);
        row = struct(...
            'method_name', string(meth), ...
            'depth_mm', dep, ...
            'total_evaluations', height(sub), ...
            'detection_rate_pct', mean(double(sub.is_detected)) * 100.0, ...
            'mean_iou', mean(sub.iou), ...
            'mean_cnr', mean(sub.cnr), ...
            'mean_loc_error_mm', mean(sub_det.localization_error_mm) ...
        );
        depth_rows = [depth_rows; row]; %#ok<AGROW>
    end
end
summary_by_depth = struct2table(depth_rows);
writetable(summary_by_depth, fullfile(output_dir, 'summary_by_depth.csv'));

% 3. Summary by Diameter
diameters = sort(unique(defective_table.diameter_mm), 'ascend');
diam_rows = [];
for m = 1:length(methods)
    meth = methods{m};
    for d = 1:length(diameters)
        diam = diameters(d);
        sub = defective_table(strcmp(defective_table.method_name, meth) & (defective_table.diameter_mm == diam), :);
        sub_det = sub(sub.is_detected, :);
        row = struct(...
            'method_name', string(meth), ...
            'diameter_mm', diam, ...
            'total_evaluations', height(sub), ...
            'detection_rate_pct', mean(double(sub.is_detected)) * 100.0, ...
            'mean_iou', mean(sub.iou), ...
            'mean_cnr', mean(sub.cnr), ...
            'mean_loc_error_mm', mean(sub_det.localization_error_mm) ...
        );
        diam_rows = [diam_rows; row]; %#ok<AGROW>
    end
end
summary_by_diameter = struct2table(diam_rows);
writetable(summary_by_diameter, fullfile(output_dir, 'summary_by_diameter.csv'));

% 4. Summary by Noise (SNR)
noise_levels = {'clean', '30dB', '25dB', '20dB'};
noise_rows = [];
for m = 1:length(methods)
    meth = methods{m};
    for s = 1:length(noise_levels)
        nl = noise_levels{s};
        if strcmp(nl, 'clean')
            sub = defective_table(strcmp(defective_table.method_name, meth) & (isnan(defective_table.snr_db) | isinf(defective_table.snr_db)), :);
        else
            val = sscanf(nl, '%ddB');
            sub = defective_table(strcmp(defective_table.method_name, meth) & (defective_table.snr_db == val), :);
        end
        if isempty(sub)
            continue;
        end
        sub_det = sub(sub.is_detected, :);
        row = struct(...
            'method_name', string(meth), ...
            'snr_condition', string(nl), ...
            'total_evaluations', height(sub), ...
            'detection_rate_pct', mean(double(sub.is_detected)) * 100.0, ...
            'mean_iou', mean(sub.iou), ...
            'mean_cnr', mean(sub.cnr), ...
            'mean_loc_error_mm', mean(sub_det.localization_error_mm) ...
        );
        noise_rows = [noise_rows; row]; %#ok<AGROW>
    end
end
summary_by_noise = struct2table(noise_rows);
writetable(summary_by_noise, fullfile(output_dir, 'summary_by_noise.csv'));

% 5. Healthy Specificity
healthy_rows = [];
for m = 1:length(methods)
    meth = methods{m};
    sub = healthy_table(strcmp(healthy_table.method_name, meth), :);
    if ~isempty(sub)
        n_false = sum(sub.is_false_positive);
        n_clean = height(sub) - n_false;
        spec = double(n_clean) / double(height(sub));
    else
        n_false = 0;
        spec = 1.0;
    end
    row = struct(...
        'method_name', string(meth), ...
        'healthy_evaluations', height(sub), ...
        'false_alarms', n_false, ...
        'specificity_pct', spec * 100.0 ...
    );
    healthy_rows = [healthy_rows; row]; %#ok<AGROW>
end
if ~isempty(healthy_rows)
    healthy_specificity = struct2table(healthy_rows);
    writetable(healthy_specificity, fullfile(output_dir, 'healthy_specificity.csv'));
else
    healthy_specificity = table();
end

% 6. Maximum Detectable Depth Table
max_depth_table = maximum_detectable_depth(eval_table);
if ~isempty(max_depth_table)
    writetable(max_depth_table, fullfile(output_dir, 'max_detectable_depth.csv'));
end

summaries = struct(...
    'by_method', summary_by_method, ...
    'by_depth', summary_by_depth, ...
    'by_diameter', summary_by_diameter, ...
    'by_noise', summary_by_noise, ...
    'healthy_specificity', healthy_specificity, ...
    'max_detectable_depth', max_depth_table ...
);
end
