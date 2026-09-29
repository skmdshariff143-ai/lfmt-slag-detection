function cfg = literature_config()
% LITERATURE_CONFIG Returns benchmark configuration matching classical NDT literature.

cfg = default_config();

% Standard thermal wave literature benchmark
cfg.excitation.f0_hz = 0.02;
cfg.excitation.f1_hz = 0.40;
cfg.excitation.duration_s = 15.0;
cfg.excitation.q0_w_m2 = 4000.0;
cfg.simulation.total_time_s = 15.0;
end
