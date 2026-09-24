function result = lfmt_matched_filter(T_surf, t_vec, f0, f1, duration, q0)
% LFMT_MATCHED_FILTER Pixel-wise Matched Filter / Pulse Compression in pure MATLAB.
%
% Performs cross-correlation between pixel thermal curves and the zero-mean AC chirp reference.
%
% CRITICAL: Ground truth is STRICTLY forbidden and not passed as input.

t_start = tic;

[n_frames, ny, nx] = size(T_surf);
if nargin < 2 || isempty(t_vec), t_vec = linspace(0, 10, n_frames)'; end
if nargin < 3 || isempty(f0), f0 = 0.05; end
if nargin < 4 || isempty(f1), f1 = 0.50; end
if nargin < 5 || isempty(duration), duration = 10.0; end
if nargin < 6 || isempty(q0), q0 = 5000.0; end

dt = t_vec(2) - t_vec(1);

% 1. Generate zero-mean normalized AC reference waveform
ref = zeros(size(t_vec));
mask = (t_vec >= 0) & (t_vec <= duration);
if any(mask)
    beta = (f1 - f0) / duration;
    t_m = t_vec(mask);
    phi = 2 * pi * (f0 * t_m + 0.5 * beta * (t_m.^2));
    ref(mask) = sin(phi);
    ref(mask) = ref(mask) - mean(ref(mask));
end
norm_r = norm(ref);
if norm_r > 0
    ref = ref / norm_r;
end

% 2. Reshape thermal tensor to 2D (time x pixels) and mean-center
T_2d = reshape(T_surf, n_frames, ny * nx);
T_ac = T_2d - mean(T_2d, 1);

% 3. Vectorized Convolution-Based Matched Filter: correlate(T_ac, ref)
% Identical to scipy.signal.fftconvolve(T_ac, ref[::-1, :], mode='same', axes=0)
ref_flipped = flipud(ref(:));
corr_2d = conv2(T_ac, ref_flipped, 'same');

% 4. Peak correlation magnitude & delay maps
[peak_vals, max_indices] = max(abs(corr_2d), [], 1);
lags = ((1:n_frames) - floor(n_frames / 2)) * dt;
delay_vals = lags(max_indices);

peak_map = reshape(peak_vals, ny, nx);
delay_map = reshape(delay_vals, ny, nx);

% 5. Normalized score map [0, 1]
p_min = min(peak_map(:));
p_max = max(peak_map(:));
if (p_max - p_min) > 1e-12
    norm_map = (peak_map - p_min) / (p_max - p_min);
else
    norm_map = zeros(ny, nx);
end

runtime_s = toc(t_start);

result = struct(...
    'method_name', 'Matched Filter', ...
    'score_map', peak_map, ...
    'normalized_map', norm_map, ...
    'delay_map_s', delay_map, ...
    'runtime_s', runtime_s, ...
    'selection_method', 'fft_pulse_compression' ...
);
end
