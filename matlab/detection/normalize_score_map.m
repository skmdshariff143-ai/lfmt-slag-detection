function norm_map = normalize_score_map(score_map)
% NORMALIZE_SCORE_MAP Robust min-max normalization of 2D score map to [0, 1].

s_min = min(score_map(:));
s_max = max(score_map(:));

if (s_max - s_min) > 1e-12
    norm_map = (score_map - s_min) / (s_max - s_min);
else
    norm_map = zeros(size(score_map));
end
end
