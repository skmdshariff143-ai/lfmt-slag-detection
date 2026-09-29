function result = lfmt_spct(T_surf, n_components, alpha_l1, max_iter)
% LFMT_SPCT Sparse Principal Component Thermography using L1-regularization in pure MATLAB.
%
% Extracts sparse spatial EOF basis functions using coordinate-descent / proximal sparse PCA.
% Component selection is 100% BLIND using peak-to-background anomaly ratio.
% Polarity correction is 100% BLIND using spatial skewness.
%
% CRITICAL: Ground truth is STRICTLY forbidden and not passed as input.

t_start = tic;

if nargin < 2 || isempty(n_components), n_components = 6; end
if nargin < 3 || isempty(alpha_l1), alpha_l1 = 0.05; end
if nargin < 4 || isempty(max_iter), max_iter = 50; end

[n_frames, ny, nx] = size(T_surf);
n_pixels = ny * nx;
A = reshape(T_surf, n_frames, n_pixels);

% 1. Mean-center along time axis
A_centered = A - mean(A, 1);

% 2. SVD initialization
[~, ~, V_init] = svd(A_centered, 'econ');
n_comp = min([n_components, size(V_init, 2), n_frames]);

sparse_components = zeros(n_comp, ny, nx);
non_zero_ratios = zeros(n_comp, 1);

A_res = A_centered;

for k = 1:n_comp
    v = V_init(:, k);
    if norm(v) > 0, v = v / norm(v); end
    
    % Adaptive soft-thresholding parameter lambda
    lambda = alpha_l1 * max(abs(A_res' * (A_res * v))) / (norm(A_res * v) + 1e-12);
    if isempty(lambda) || isnan(lambda) || lambda == 0
        lambda = alpha_l1 * 0.1;
    end
    
    for it = 1:max_iter
        v_old = v;
        
        % Temporal projection u
        Av = A_res * v;
        norm_Av = norm(Av);
        if norm_Av > 1e-12
            u = Av / norm_Av;
        else
            u = zeros(n_frames, 1);
            break;
        end
        
        % Spatial loading vector v_raw
        v_raw = A_res' * u;
        
        % Soft thresholding operator: S_lambda(x) = sign(x) * max(0, |x| - lambda)
        v = sign(v_raw) .* max(0, abs(v_raw) - lambda);
        norm_v = norm(v);
        if norm_v > 1e-12
            v = v / norm_v;
        else
            v = v_raw / (norm(v_raw) + 1e-12);
        end
        
        if norm(v - v_old) < 1e-4
            break;
        end
    end
    
    sparse_components(k, :, :) = reshape(v, ny, nx);
    non_zero_ratios(k) = sum(abs(v) > 1e-6) / double(n_pixels);
    
    % Deflate residual matrix
    u_proj = A_res * v;
    A_res = A_res - u_proj * v';
end

% 3. Blind Polarity Alignment and Anomaly Scoring for Each Component
p2b_scores = zeros(1, n_comp);
for i = 1:n_comp
    img = squeeze(sparse_components(i, :, :));
    img_std = std(img(:));
    if img_std > 1e-12
        img_norm = (img - mean(img(:))) / img_std;
        skewness = mean(img_norm(:).^3);
        
        % Invert polarity if negative skewness (align positive anomaly)
        if skewness < 0
            img = -img;
            sparse_components(i, :, :) = img;
            skewness = -skewness;
        end
        % Anomaly score combines spatial sparsity and peak-to-background anomaly ratio
        sparsity_weight = max(0.01, 1.0 - non_zero_ratios(i));
        if i == 1 && non_zero_ratios(1) > 0.95
            sparsity_weight = 0.001; % Suppress global DC background mode
        end
        p2b_scores(i) = sparsity_weight * abs(skewness) * (max(img(:)) / (img_std + 1e-12));
    else
        p2b_scores(i) = 0.0;
    end
end

[~, best_idx] = max(p2b_scores);
selected_map = squeeze(sparse_components(best_idx, :, :));

% 5. Min-max normalized map [0, 1]
p_min = min(selected_map(:));
p_max = max(selected_map(:));
if (p_max - p_min) > 1e-12
    norm_map = (selected_map - p_min) / (p_max - p_min);
else
    norm_map = zeros(ny, nx);
end

runtime_s = toc(t_start);

result = struct(...
    'method_name', 'SPCT', ...
    'score_map', selected_map, ...
    'normalized_map', norm_map, ...
    'sparse_components', sparse_components, ...
    'non_zero_ratios', non_zero_ratios, ...
    'alpha_l1', alpha_l1, ...
    'selected_component_idx', best_idx, ...
    'p2b_scores', p2b_scores, ...
    'runtime_s', runtime_s, ...
    'selection_method', 'blind_peak_to_background' ...
);
end
