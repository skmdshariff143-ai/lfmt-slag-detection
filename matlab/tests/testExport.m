classdef testExport < matlab.unittest.TestCase
    methods (Test)
        function testMatAndJsonExport(testCase)
            cfg = struct();
            cfg.simulation = struct('Nx', 20, 'Ny', 14, 'Nz', 6, 'dt_s', 0.1, 'total_time_s', 0.2);
            cfg.excitation = struct('f0_hz', 0.05, 'f1_hz', 0.50, 'q0_w_m2', 5000.0, 'duration_s', 10.0, 'h_conv_w_m2k', 10.0, 'ambient_temp_k', 293.15);
            cfg.plate = struct('length_mm', 100.0, 'width_mm', 70.0, 'thickness_mm', 2.3);
            cfg.camera = struct('cam_nx', 40, 'cam_ny', 28);
            
            res = lfmt.solveTransientThermal(cfg);
            
            tmp_mat = fullfile(tempdir, 'lfmt_test_out.mat');
            lfmt.exportSimulation(res, tmp_mat, cfg);
            
            testCase.verifyTrue(exist(tmp_mat, 'file') == 2, 'MAT file must be created');
            manifest_file = strrep(tmp_mat, '.mat', '_manifest.json');
            testCase.verifyTrue(exist(manifest_file, 'file') == 2, 'JSON manifest must be created');
            
            % Clean up
            delete(tmp_mat);
            delete(manifest_file);
        end
    end
end
