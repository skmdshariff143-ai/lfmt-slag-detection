function [T_noisy, noise_sigma] = noise(T_clean, snr_db, seed)
% NOISE Injects Additive White Gaussian Noise (AWGN) matching target SNR (dB).
%
% Inputs:
%   T_clean - 3D array [n_frames, ny, nx]
%   snr_db  - Target Signal-to-Noise Ratio in dB ([] or inf for clean)
%   seed    - Deterministic random seed for reproducibility
%
% Outputs:
%   T_noisy     - 3D array with injected AWGN
%   noise_sigma - Standard deviation of added noise [K]

if nargin < 2 || isempty(snr_db) || isinf(snr_db)
    T_noisy = T_clean;
    noise_sigma = 0.0;
    return;
end

if nargin >= 3 && ~isempty(seed)
    rng(seed);
end

% Compute dynamic signal standard deviation across transient sequence
signal_std = std(T_clean(:));
if signal_std < 1e-12
    signal_std = 1.0;
end

% Target noise standard deviation: SNR_dB = 20 * log10(signal_std / noise_sigma)
noise_sigma = signal_std * (10^(-double(snr_db) / 20.0));

noise_matrix = noise_sigma * randn(size(T_clean));
T_noisy = T_clean + noise_matrix;
end
