function exc = createLFMTExcitation(f0, f1, duration, q0, dt)
% CREATELFMTEXCITATION Constructs linear frequency-modulated thermal excitation
%
% Parameters:
%   f0:       Initial frequency [Hz] (e.g. 0.05)
%   f1:       Final sweep frequency [Hz] (e.g. 0.50)
%   duration: Sweep duration [s] (e.g. 10.0)
%   q0:       Baseline / amplitude scale [W/m^2] (e.g. 5000.0)
%   dt:       Time step [s] (e.g. 0.04)
%
% Returns:
%   exc: struct with time, phase, frequency, and heat flux vectors

if nargin < 5, dt = 0.04; end
if nargin < 4, q0 = 5000.0; end
if nargin < 3, duration = 10.0; end
if nargin < 2, f1 = 0.50; end
if nargin < 1, f0 = 0.05; end

beta = (f1 - f0) / duration; % Sweep rate [Hz/s]
t = (0:dt:duration)';

% Instantaneous phase: phi(t) = 2*pi*(f0*t + 0.5*beta*t^2)
phase = 2 * pi * (f0 * t + 0.5 * beta * t.^2);

% Heat flux: q(t) = q0 * (1 + sin(phi(t)))
% Note: q0 is the baseline/amplitude scale. Maximum flux is 2*q0.
q = q0 * (1.0 + sin(phase));

% Instantaneous frequency: f_inst(t) = f0 + beta*t
f_inst = f0 + beta * t;

exc = struct(...
    'f0_hz', f0, ...
    'f1_hz', f1, ...
    'duration_s', duration, ...
    'q0_w_m2', q0, ...
    'q_max_w_m2', 2.0 * q0, ...
    'beta_hz_s', beta, ...
    'dt_s', dt, ...
    'time_s', t, ...
    'phase_rad', phase, ...
    'f_inst_hz', f_inst, ...
    'heat_flux_w_m2', q ...
);
end
