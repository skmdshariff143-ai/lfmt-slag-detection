classdef TestLFMTExcitation < matlab.unittest.TestCase
    % TESTLFMTEXCITATION Unit tests for LFMT chirp excitation and diffusion length.

    methods (Test)
        function testWaveformBounds(testCase)
            t = linspace(0, 10, 501);
            q0 = 5000;
            q = lfmt.excitation('heat_flux', t, 0.05, 0.50, 10.0, q0);
            
            testCase.verifyGreaterThanOrEqual(min(q), 0.0);
            testCase.verifyLessThanOrEqual(max(q), 2.0 * q0 + 1e-6);
            testCase.verifyEqual(q(1), q0, 'AbsTol', 1e-4);
        end

        function testReferenceSignalZeroMean(testCase)
            t = linspace(0, 10, 501);
            ref = lfmt.excitation('reference_signal', t, 0.05, 0.50, 10.0, true);
            
            testCase.verifyEqual(mean(ref), 0.0, 'AbsTol', 1e-4);
            testCase.verifyEqual(norm(ref), 1.0, 'AbsTol', 1e-6);
        end

        function testDiffusionLengthFormula(testCase)
            alpha = 1.359e-5; % m^2/s for mild steel
            f0 = 0.05;
            mu = lfmt.excitation('diffusion_length', f0, alpha);
            
            expected_mu = sqrt(alpha / (pi * f0));
            testCase.verifyEqual(mu, expected_mu, 'AbsTol', 1e-9);
            testCase.verifyGreaterThan(mu * 1e3, 2.3); % Penetrates plate thickness
        end
    end
end
