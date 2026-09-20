function [pct_map, eof_all, explained_var] = lfmt_pct(T_surf, gt_mask)
% LFMT_PCT Principal Component Thermography using SVD in MATLAB.

[n_frames, ny, nx] = size(T_surf);
A = reshape(T_surf, n_frames, ny * nx);
A_mean = mean(A, 1);
A_centered = A - A_mean;

[U, S, V] = svd(A_centered, 'econ');
s = diag(S);
explained_var = (s.^2) / sum(s.^2);

n_comp = min(6, size(V, 2));
eof_all = zeros(n_comp, ny, nx);
for i = 1:n_comp
    eof_all(i, :, :) = reshape(V(:, i), ny, nx);
end

% Select best EOF component using contrast
scores = zeros(1, n_comp);
for i = 1:n_comp
    img = squeeze(eof_all(i, :, :));
    scores(i) = abs(mean(img(gt_mask)) - mean(img(~gt_mask)));
end
[~, best_idx] = max(scores);
pct_map = squeeze(eof_all(best_idx, :, :));

% Ensure positive contrast
if mean(pct_map(gt_mask)) < mean(pct_map(~gt_mask))
    pct_map = -pct_map;
end
end
