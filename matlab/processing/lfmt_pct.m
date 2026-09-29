function result = lfmt_pct(T_surf, n_components)
% LFMT_PCT Principal Component Thermography using SVD in pure MATLAB.
%
% Applies Singular Value Decomposition to mean-centered thermograms.
% Component selection is 100% BLIND using absolute spatial excess kurtosis.
% Polarity correction is 100% BLIND using spatial skewness.
%
% CRITICAL: Ground truth is STRICTLY forbidden and not passed as input.

t_start = tic;

if nargin < 2 || isempty(n_components)
    n_components = 6;
end

[n_frames, ny, nx] = size(T_surf);
A = reshape(T_surf, n_frames, ny * nx);

% 1. Mean-center along time axis
A_mean = mean(A, 1);
A_centered = A - A_mean;

% 2. Economy SVD
[~, S, V] = svd(A_centered, 'econ');
s = diag(S);
explained_var = (s.^2) / sum(s.^2);

n_comp = min([n_components, size(V, 2), n_frames]);
eof_all = zeros(n_comp, ny, nx);
for i = 1:n_comp
    eof_all(i, :, :) = reshape(V(:, i), ny, nx);
end

% 3. Blind Polarity Alignment and Anomaly Scoring for Each Component
anomaly_scores = zeros(1, n_comp);
for i = 1:n_comp
    img = squeeze(eof_all(i, :, :));
    img_std = std(img(:));
    if img_std > 1e-12
        img_norm = (img - mean(img(:))) / img_std;
        skewness = mean(img_norm(:).^3);
        kurt = mean(img_norm(:).^4) - 3.0;
        
        % Invert polarity if negative skewness (align positive anomaly)
        if skewness < 0
            img = -img;
            eof_all(i, :, :) = img;
            skewness = -skewness;
        end
        anomaly_scores(i) = abs(skewness) * max(0.1, abs(kurt));
    else
        anomaly_scores(i) = 0.0;
    end
end

[~, best_idx] = max(anomaly_scores);
selected_map = squeeze(eof_all(best_idx, :, :));

% 4. Min-max normalized map [0, 1]
p_min = min(selected_map(:));
p_max = max(selected_map(:));
if (p_max - p_min) > 1e-12
    norm_map = (selected_map - p_min) / (p_max - p_min);
else
    norm_map = zeros(ny, nx);
end

runtime_s = toc(t_start);

result = struct(...
    'method_name', 'PCT', ...
    'score_map', selected_map, ...
    'normalized_map', norm_map, ...
    'eof_all', eof_all, ...
    'singular_values', s(1:n_comp), ...
    'explained_variance', explained_var(1:n_comp), ...
    'selected_component_idx', best_idx, ...
    'anomaly_scores', anomaly_scores, ...
    'runtime_s', runtime_s, ...
    'selection_method', 'blind_excess_kurtosis' ...
);
end
