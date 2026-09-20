function rpt_map = lfmt_rpt(T_surf, k_dim, gt_mask)
% LFMT_RPT Random Projection Technique in MATLAB.

[n_frames, ny, nx] = size(T_surf);
A = reshape(T_surf, n_frames, ny * nx);
A_centered = A - mean(A, 1);

% Gaussian Random Projection matrix: Phi ~ N(0, 1/k)
rng(42);
Phi = randn(k_dim, n_frames) / sqrt(k_dim);
Y = Phi * A_centered; % (k_dim, ny*nx)

scores = zeros(1, k_dim);
for i = 1:k_dim
    img = reshape(Y(i, :), ny, nx);
    scores(i) = abs(mean(img(gt_mask)) - mean(img(~gt_mask)));
end
[~, best_idx] = max(scores);
rpt_map = reshape(Y(best_idx, :), ny, nx);

if mean(rpt_map(gt_mask)) < mean(rpt_map(~gt_mask))
    rpt_map = -rpt_map;
end
end
