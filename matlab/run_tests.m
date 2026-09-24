function test_results = run_tests()
% RUN_TESTS Master test runner for the LFMT MATLAB scientific test suite.
%
% Runs all unit and validation tests using matlab.unittest.TestSuite.

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
fprintf('                 LFMT MATLAB COMPREHENSIVE TEST SUITE                           \n');
fprintf('================================================================================\n');

suite = matlab.unittest.TestSuite.fromFolder(fullfile(matlab_root, 'tests'));
runner = matlab.unittest.TestRunner.withTextOutput;

test_results = runner.run(suite);

fprintf('\n======================= TEST RUN SUMMARY =======================\n');
n_passed = sum([test_results.Passed]);
n_failed = sum([test_results.Failed]);
n_total = length(test_results);

fprintf('Passed: %d / %d\n', n_passed, n_total);
if n_failed > 0
    fprintf('FAILED: %d\n', n_failed);
    error('LFMT:TestFailures', '%d unit tests failed.', n_failed);
else
    fprintf('ALL TESTS PASSED SUCCESSFULLY (100%% GREEN).\n');
end
fprintf('================================================================\n');
end
