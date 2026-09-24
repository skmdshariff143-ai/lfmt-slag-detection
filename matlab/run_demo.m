function results = run_demo()
% RUN_DEMO Runs a quick, publication-grade interactive demonstration of LFMT MATLAB.
%
% Executes:
%   1. Environment & Capability check
%   2. Single benchmark case (D=8mm, z=0.4mm)
%   3. 5 Blind signal processing methods
%   4. Plotting thermogram evolution and method comparison

matlab_root = fileparts(mfilename('fullpath'));
addpath(matlab_root);
addpath(fullfile(matlab_root, 'config'));
addpath(fullfile(matlab_root, 'simulation'));
addpath(fullfile(matlab_root, 'processing'));
addpath(fullfile(matlab_root, 'detection'));
addpath(fullfile(matlab_root, 'evaluation'));
addpath(fullfile(matlab_root, 'validation'));
addpath(fullfile(matlab_root, 'visualization'));
addpath(fullfile(matlab_root, 'tests'));

fprintf('================================================================================\n');
fprintf('                LFMT SLAG DETECTION MATLAB FLAGSHIP DEMONSTRATION                \n');
fprintf('================================================================================\n');

% 1. Check environment
lfmt_check_environment('SaveReport', true);

% 2. Run benchmark case
cfg = conference_config();
results = run_single_case(cfg, 'Plot', true, 'SaveFigures', true, 'Verbose', true);

fprintf('\nDemo completed successfully. Figures generated in matlab/results/figures/\n');
end
