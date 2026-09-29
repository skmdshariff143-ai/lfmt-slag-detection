function project_outputs = run_project(mode)
% RUN_PROJECT Master entry point for the entire LFMT MATLAB scientific system.
%
% Modes:
%   'demo'       (default) - Quick single-case demonstration & publication figure generation
%   'validate'             - Runs the full numerical and physical validation suite
%   'test'                 - Runs all unit and integration tests
%   'study_quick'          - Runs a quick 5-case study grid
%   'study_full'           - Runs the complete 4,030 evaluation scientific study

if nargin < 1 || isempty(mode)
    mode = 'demo';
end

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

switch lower(mode)
    case 'demo'
        project_outputs = run_demo();
        
    case 'validate'
        project_outputs = run_validation_suite('Quick', false);
        
    case 'test'
        project_outputs = run_tests();
        
    case 'study_quick'
        project_outputs = run_full_study('Quick', true, 'SaveFigures', true);
        
    case 'study_full'
        project_outputs = run_full_study('Quick', false, 'SaveFigures', true);
        
    otherwise
        error('LFMT:InvalidProjectMode', 'Unknown mode "%s". Valid modes: demo, validate, test, study_quick, study_full.', mode);
end
end
