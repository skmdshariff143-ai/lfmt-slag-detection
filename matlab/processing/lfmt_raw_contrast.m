function result = lfmt_raw_contrast(T_surf, t_vec)
% LFMT_RAW_CONTRAST Blind Raw Thermal Contrast Processing in pure MATLAB.
%
% Algorithm:
%   1. Computes spatial standard deviation / variance across all frames.
%   2. Blindly selects peak contrast frame t_peak = argmax_t (std_spatial(T(t))).
%   3. Subtracts spatial median baseline at peak frame to yield contrast map.
%
% CRITICAL: Ground truth is STRICTLY forbidden and not passed as input.

t_start = tic;

[n_frames, ny, nx] = size(T_surf);
if nargin < 2 || isempty(t_vec)
    t_vec = (0:(n_frames-1))';
end

% 1. Compute spatial standard deviation across frames
spatial_stds = zeros(n_frames, 1);
for k = 1:n_frames
    frame = squeeze(T_surf(k, :, :));
    spatial_stds(k) = std(frame(:));
end

% 2. Select frame with maximum spatial variance blindly
[max_contrast_val, peak_frame_idx] = max(spatial_stds);
t_peak = t_vec(peak_frame_idx);

% 3. Extract peak frame and subtract spatial median sound baseline
peak_frame = squeeze(T_surf(peak_frame_idx, :, :));
sound_baseline = median(peak_frame(:));
contrast_map = peak_frame - sound_baseline;

% 4. Min-max normalized map [0, 1]
c_min = min(contrast_map(:));
c_max = max(contrast_map(:));
if (c_max - c_min) > 1e-12
    norm_map = (contrast_map - c_min) / (c_max - c_min);
else
    norm_map = zeros(ny, nx);
end

runtime_s = toc(t_start);

result = struct(...
    'method_name', 'Raw Contrast', ...
    'score_map', contrast_map, ...
    'normalized_map', norm_map, ...
    'peak_frame_idx', peak_frame_idx, ...
    'peak_time_s', t_peak, ...
    'max_contrast_val', max_contrast_val, ...
    'runtime_s', runtime_s, ...
    'selection_method', 'blind_spatial_variance' ...
);
end
