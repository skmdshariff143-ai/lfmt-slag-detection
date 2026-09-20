function mf_map = lfmt_matched_filter(T_surf, t_vec, f0, f1, T_exc, q0)
% LFMT_MATCHED_FILTER Pixel-wise matched filter using cross-correlation.

[n_frames, ny, nx] = size(T_surf);
beta = (f1 - f0) / T_exc;

% Chirp reference signal
ref = zeros(size(t_vec));
mask = (t_vec >= 0) & (t_vec <= T_exc);
phi = 2*pi*(f0*t_vec(mask) + 0.5*beta*(t_vec(mask).^2));
ref(mask) = q0 * (1 + sin(phi));
ref(mask) = ref(mask) - mean(ref(mask));
if norm(ref) > 0, ref = ref / norm(ref); end

% Vectorized cross-correlation
T_2d = reshape(T_surf, n_frames, ny * nx);
T_ac = T_2d - mean(T_2d, 1);

corr_2d = zeros(size(T_2d));
for p = 1:(ny * nx)
    c = xcorr(T_ac(:, p), ref, 'same');
    corr_2d(:, p) = c;
end

peak_vals = max(abs(corr_2d), [], 1);
mf_map = reshape(peak_vals, ny, nx);
mf_map = (mf_map - min(mf_map(:))) / (max(mf_map(:)) - min(mf_map(:)) + eps);
end
