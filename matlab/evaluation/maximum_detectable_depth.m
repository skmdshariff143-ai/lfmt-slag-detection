function depth_table = maximum_detectable_depth(eval_records)
% MAXIMUM_DETECTABLE_DEPTH Computes maximum detectable depth (z_max) where success rate >= 80%.
%
% Input:
%   eval_records - Array of evaluation structs or table with fields:
%                  method_name, diameter_mm, depth_mm, snr_db, is_detected
%
% Output:
%   depth_table - Summary table containing z_max for each (method, diameter, SNR) combination.

if isstruct(eval_records)
    eval_table = struct2table(eval_records);
else
    eval_table = eval_records;
end

methods = unique(eval_table.method_name);
diameters = unique(eval_table.diameter_mm(eval_table.diameter_mm > 0));
snr_conditions = unique(eval_table.snr_db);

results_list = [];

for m = 1:length(methods)
    meth = methods{m};
    
    for d = 1:length(diameters)
        diam = diameters(d);
        
        for s = 1:length(snr_conditions)
            snr_val = snr_conditions(s);
            
            % Filter records
            if isnan(snr_val) || isinf(snr_val)
                mask = strcmp(eval_table.method_name, meth) & ...
                       (eval_table.diameter_mm == diam) & ...
                       (isnan(eval_table.snr_db) | isinf(eval_table.snr_db));
                snr_label = 'clean';
            else
                mask = strcmp(eval_table.method_name, meth) & ...
                       (eval_table.diameter_mm == diam) & ...
                       (eval_table.snr_db == snr_val);
                snr_label = sprintf('%ddB', int32(snr_val));
            end
            
            sub = eval_table(mask, :);
            if isempty(sub)
                continue;
            end
            
            depths_available = sort(unique(sub.depth_mm), 'ascend');
            z_max = 0.0;
            
            for dep_idx = 1:length(depths_available)
                dep = depths_available(dep_idx);
                sub_dep = sub(sub.depth_mm == dep, :);
                success_rate = mean(double(sub_dep.is_detected));
                
                if success_rate >= 0.80
                    z_max = max(z_max, dep);
                end
            end
            
            row = struct(...
                'method_name', string(meth), ...
                'diameter_mm', diam, ...
                'snr_condition', string(snr_label), ...
                'max_detectable_depth_mm', z_max ...
            );
            results_list = [results_list; row]; %#ok<AGROW>
        end
    end
end

if ~isempty(results_list)
    depth_table = struct2table(results_list);
else
    depth_table = table();
end
end
