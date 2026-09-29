classdef TestLFMTFEMSimulation < matlab.unittest.TestCase
    % TESTLFMTFEMSIMULATION Unit tests for 3-D Hex8 FEM forward simulation.

    methods (Test)
        function testZeroFluxEquilibrium(testCase)
            cfg = default_config();
            cfg.excitation.q0_w_m2 = 0.0;
            cfg.simulation.total_time_s = 2.0;
            cfg.excitation.duration_s = 2.0;
            cfg.simulation.Nx = 15;
            cfg.simulation.Ny = 10;
            cfg.simulation.Nz = 4;
            
            res = lfmt_simulate_fem(cfg);
            max_dev = max(abs(res.surface_temperature(:) - cfg.excitation.ambient_temp_k));
            testCase.verifyLessThan(max_dev, 1e-4);
        end

        function testPositiveHeatingRise(testCase)
            cfg = default_config();
            cfg.simulation.total_time_s = 2.0;
            cfg.excitation.duration_s = 2.0;
            cfg.simulation.Nx = 15;
            cfg.simulation.Ny = 10;
            cfg.simulation.Nz = 4;
            
            res = lfmt_simulate_fem(cfg);
            peak_T = max(res.surface_temperature(:));
            testCase.verifyGreaterThan(peak_T, cfg.excitation.ambient_temp_k);
        end

        function testFEMvsFDMAgreement(testCase)
            cfg = default_config();
            cfg.simulation.total_time_s = 2.0;
            cfg.excitation.duration_s = 2.0;
            cfg.simulation.Nx = 15;
            cfg.simulation.Ny = 10;
            cfg.simulation.Nz = 4;
            
            res_fem = lfmt_simulate_fem(cfg);
            res_fdm = lfmt_simulate_fdm(cfg);
            
            diff_T = res_fem.surface_temperature - res_fdm.surface_temperature;
            rel_l2 = norm(diff_T(:)) / (norm(res_fem.surface_temperature(:)) + 1e-12);
            testCase.verifyLessThan(rel_l2, 0.05);
        end
    end
end
