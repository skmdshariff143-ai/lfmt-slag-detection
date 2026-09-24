function cfg = conference_config()
% CONFERENCE_CONFIG Returns the frozen conference benchmark configuration.

cfg = default_config();

% Frozen conference parameters
cfg.excitation.f0_hz = 0.05;
cfg.excitation.f1_hz = 0.50;
cfg.excitation.duration_s = 10.0;
cfg.excitation.q0_w_m2 = 5000.0;
cfg.excitation.h_conv_w_m2k = 10.0;
cfg.excitation.ambient_temp_k = 293.15;

cfg.plate.length_mm = 100.0;
cfg.plate.width_mm = 70.0;
cfg.plate.thickness_mm = 2.3;

cfg.simulation.solver_type = 'fem';
cfg.simulation.Nx = 40;
cfg.simulation.Ny = 28;
cfg.simulation.Nz = 12;
cfg.simulation.dt_s = 0.02;
cfg.simulation.total_time_s = 10.0;

cfg.camera.cam_nx = 64;
cfg.camera.cam_ny = 64;
cfg.camera.sampling_rate_hz = 25.0;
cfg.camera.frame_rate_hz = 25.0;
end
