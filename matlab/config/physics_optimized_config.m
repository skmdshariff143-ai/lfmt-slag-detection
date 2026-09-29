function cfg = physics_optimized_config()
% PHYSICS_OPTIMIZED_CONFIG Configuration optimized based on thermal diffusion length analysis.
%
% For mild steel (alpha = 1.359e-5 m^2/s):
%   mu(f) = sqrt(alpha / (pi * f))
% At depth z = 1.0 mm, optimal probing frequency corresponds to mu(f) approx 1.0 - 2.3 mm:
%   f_opt in [0.03 Hz, 0.45 Hz]

cfg = conference_config();
cfg.excitation.f0_hz = 0.03;
cfg.excitation.f1_hz = 0.45;
cfg.excitation.duration_s = 12.0;
cfg.simulation.total_time_s = 12.0;
end
