classdef testFrameZero < matlab.unittest.TestCase
    methods (Test)
        function testFrameZeroAmbient(testCase)
            cfg = struct();
            cfg.simulation = struct('Nx', 20, 'Ny', 14, 'Nz', 6, 'dt_s', 0.1, 'total_time_s', 0.5);
            cfg.excitation = struct('f0_hz', 0.05, 'f1_hz', 0.50, 'q0_w_m2', 5000.0, 'duration_s', 10.0, 'h_conv_w_m2k', 10.0, 'ambient_temp_k', 293.15);
            cfg.plate = struct('length_mm', 100.0, 'width_mm', 70.0, 'thickness_mm', 2.3);
            cfg.camera = struct('cam_nx', 40, 'cam_ny', 28);
            
            res = lfmt.solveTransientThermal(cfg);
            f0_err = max(abs(res.surface_temperature(1, :, :) - 293.15), [], 'all');
            testCase.verifyEqual(f0_err, 0.0, 'AbsTol', 1e-10, 'Frame 0 must be strictly ambient equilibrium');
        end
    end
end
