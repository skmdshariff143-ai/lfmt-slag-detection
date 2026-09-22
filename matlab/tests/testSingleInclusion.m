classdef testSingleInclusion < matlab.unittest.TestCase
    methods (Test)
        function testDefectIncreasesSurfaceDeltaT(testCase)
            cfg_h = struct();
            cfg_h.simulation = struct('Nx', 24, 'Ny', 18, 'Nz', 8, 'dt_s', 0.1, 'total_time_s', 1.0);
            cfg_h.excitation = struct('f0_hz', 0.05, 'f1_hz', 0.50, 'q0_w_m2', 5000.0, 'duration_s', 10.0, 'h_conv_w_m2k', 10.0, 'ambient_temp_k', 293.15);
            cfg_h.plate = struct('length_mm', 100.0, 'width_mm', 70.0, 'thickness_mm', 2.3);
            cfg_h.camera = struct('cam_nx', 40, 'cam_ny', 28);
            
            res_h = lfmt.solveTransientThermal(cfg_h);
            
            cfg_d = cfg_h;
            cfg_d.defects = [struct('diameter_mm', 8.0, 'depth_mm', 0.4, 'thickness_mm', 0.4, 'center_x_mm', 50.0, 'center_y_mm', 35.0)];
            res_d = lfmt.solveTransientThermal(cfg_d);
            
            % Slag thermal conductivity (1.5 W/mK) is lower than steel (51.9 W/mK),
            % causing heat accumulation and higher surface temperature over defect.
            peak_h = max(res_h.surface_temperature(:)) - 293.15;
            peak_d = max(res_d.surface_temperature(:)) - 293.15;
            
            testCase.verifyGreaterThan(peak_d, peak_h, 'Low-conductivity slag must produce thermal contrast');
        end
    end
end
