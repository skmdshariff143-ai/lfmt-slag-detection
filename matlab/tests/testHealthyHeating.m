classdef testHealthyHeating < matlab.unittest.TestCase
    methods (Test)
        function testHealthyPositiveDeltaT(testCase)
            cfg = struct();
            cfg.simulation = struct('Nx', 20, 'Ny', 14, 'Nz', 6, 'dt_s', 0.1, 'total_time_s', 1.0);
            cfg.excitation = struct('f0_hz', 0.05, 'f1_hz', 0.50, 'q0_w_m2', 5000.0, 'duration_s', 10.0, 'h_conv_w_m2k', 10.0, 'ambient_temp_k', 293.15);
            cfg.plate = struct('length_mm', 100.0, 'width_mm', 70.0, 'thickness_mm', 2.3);
            cfg.camera = struct('cam_nx', 40, 'cam_ny', 28);
            
            res = lfmt.solveTransientThermal(cfg);
            diag = lfmt.computeDiagnostics(res);
            
            testCase.verifyTrue(diag.is_finite, 'All thermal values must be finite');
            testCase.verifyGreaterThan(diag.peak_delta_T_k, 0.0, 'Peak delta-T must be positive under positive heating');
        end
    end
end
