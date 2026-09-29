function thresh = compute_otsu_threshold(image_2d, n_bins)
% COMPUTE_OTSU_THRESHOLD Computes Otsu's optimal global binarization threshold in pure MATLAB.
%
% Algorithm:
%   Maximizes inter-class variance between background and foreground distributions.

if nargin < 2 || isempty(n_bins)
    n_bins = 256;
end

img_flat = double(image_2d(:));
img_min = min(img_flat);
img_max = max(img_flat);

if (img_max - img_min) < 1e-12
    thresh = img_min;
    return;
end

% 1. Compute normalized histogram
edges = linspace(img_min, img_max, n_bins + 1);
counts = histcounts(img_flat, edges);
p = counts / sum(counts);

% Bin centers
bin_centers = (edges(1:end-1) + edges(2:end)) / 2.0;

% 2. Cumulative sums and means
omega = cumsum(p);
mu = cumsum(p .* bin_centers);
mu_t = mu(end);

% 3. Inter-class variance: sigma_b^2 = (mu_t * omega - mu)^2 / (omega * (1 - omega))
denom = omega .* (1.0 - omega);
idx_valid = denom > 1e-12;

sigma_b2 = zeros(size(p));
sigma_b2(idx_valid) = ((mu_t * omega(idx_valid) - mu(idx_valid)).^2) ./ denom(idx_valid);

[~, max_idx] = max(sigma_b2);
thresh = bin_centers(max_idx);
end
