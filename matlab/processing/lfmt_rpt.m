function result = lfmt_rpt(T_surf, n_components, seed)
% LFMT_RPT Random Projection Technique (RPT) in pure MATLAB.
%
% Projects temporal thermal signatures into a low-dimensional subspace using
% Gaussian random projection satisfying the Johnson-Lindenstrauss lemma.
% Component selection is 100% BLIND using maximum dynamic range.
% Polarity correction is 100% BLIND using spatial skewness.
%
% CRITICAL: Ground truth is STRICTLY forbidden and not passed as input.

t_start = tic;

if nargin < 2 || isempty(n_components), n_components = 6; end
if nargin < 3 || isempty(seed), seed = 42; end

[n_frames, ny, nx] = size(T_surf);
n_pixels = ny * nx;
A = reshape(T_surf, n_frames, n_pixels);

% 1. Mean-center along time axis
A_centered = A - mean(A, 1);

% 2. Generate deterministic Gaussian Random Projection Matrix: Phi ~ N(0, 1/k)
rng(seed);
k_dim = min([n_components, n_frames - 1, n_pixels]);
Phi = randn(k_dim, n_frames) / sqrt(double(k_dim));

% 3. Project temporal curves: Y = Phi * A_centered (k_dim x n_pixels)
Y = Phi * A_centered;

proj_components = zeros(k_dim, ny, nx);
for i = 1:k_dim
    proj_components(i, :, :) = reshape(Y(i, :), ny, nx);
end

% 4. Blind Polarity Alignment and Dynamic Range Selection
dynamic_ranges = zeros(1, k_dim);
for i = 1:k_dim
    img = squeeze(proj_components(i, :, :));
    img_std = std(img(:));
    if img_std > 1e-12
        img_norm = (img - mean(img(:))) / img_std;
        skewness = mean(img_norm(:).^3);
        if skewness < 0
            img = -img;
            proj_components(i, :, :) = img;
            skewness = -skewness;
        end
        dynamic_ranges(i) = abs(skewness) * (max(img(:)) - min(img(:)));
    else
        dynamic_ranges(i) = 0.0;
    end
end

[~, best_idx] = max(dynamic_ranges);
selected_map = squeeze(proj_components(best_idx, :, :));

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
    'method_name', 'RPT', ...
    'score_map', selected_map, ...
    'normalized_map', norm_map, ...
    'projected_components', proj_components, ...
    'k_dim', k_dim, ...
    'compression_ratio', double(n_frames) / double(k_dim), ...
    'selected_component_idx', best_idx, ...
    'dynamic_ranges', dynamic_ranges, ...
    'runtime_s', runtime_s, ...
    'selection_method', 'blind_dynamic_range' ...
);
end
