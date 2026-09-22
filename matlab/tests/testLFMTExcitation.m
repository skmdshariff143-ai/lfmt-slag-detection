classdef testLFMTExcitation < matlab.unittest.TestCase
    methods (Test)
        function testExcitationInvariants(testCase)
            exc = lfmt.createLFMTExcitation(0.05, 0.50, 10.0, 5000.0, 0.04);
            
            testCase.verifyGreaterThanOrEqual(min(exc.heat_flux_w_m2), -1e-6);
            testCase.verifyLessThanOrEqual(max(exc.heat_flux_w_m2), 10000.0 + 1e-6);
            testCase.verifyEqual(exc.time_s(1), 0.0, 'AbsTol', 1e-12);
            testCase.verifyEqual(exc.time_s(end), 10.0, 'AbsTol', 1e-12);
            testCase.verifyEqual(exc.f_inst_hz(1), 0.05, 'AbsTol', 1e-12);
            testCase.verifyEqual(exc.f_inst_hz(end), 0.50, 'AbsTol', 1e-12);
        end
    end
end
