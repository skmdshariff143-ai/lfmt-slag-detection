function diag = computeDiagnostics(sim_result)
% COMPUTEDIAGNOSTICS Computes physical invariants and health diagnostics
surf = sim_result.surface_temperature;
t_vec = sim_result.time_vector;

% Invariant 1: Finite numbers (no NaN, no Inf)
is_finite = all(isfinite(surf(:)));

% Invariant 2: Frame 0 is ambient
Tamb_0 = surf(1, 1, 1);
frame0_err = max(abs(surf(1, :, :) - Tamb_0), [], 'all');

% Invariant 3: Mean temperature rises during heating
mean_T_t = squeeze(mean(surf, [2, 3]));
max_mean_rise = max(mean_T_t) - Tamb_0;

% Peak surface Delta-T
delta_T = surf - Tamb_0;
peak_delta_T = max(delta_T(:));

diag = struct(...
    'is_finite', is_finite, ...
    'frame0_error_k', frame0_err, ...
    'ambient_temp_k', Tamb_0, ...
    'max_mean_rise_k', max_mean_rise, ...
    'peak_delta_T_k', peak_delta_T, ...
    'runtime_s', sim_result.runtime_s ...
);
end
