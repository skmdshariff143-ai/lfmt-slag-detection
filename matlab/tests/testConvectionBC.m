classdef testConvectionBC < matlab.unittest.TestCase
    methods (Test)
        function testConvectionOperator(testCase)
            grid = lfmt.createGrid(100, 70, 2.3, 20, 14, 6);
            k_field = full(51.90 * ones(20, 14, 6));
            h_conv = 10.0;
            Tamb = 293.15;
            
            [H_diag, h_amb_vec] = lfmt.buildConvectionOperator(grid, k_field, h_conv, Tamb);
            
            testCase.verifyTrue(all(H_diag >= 0), 'Convection conductance must be non-negative');
            testCase.verifyTrue(any(H_diag > 0), 'Boundary faces must have positive convection conductance');
            testCase.verifyEqual(h_amb_vec, H_diag * Tamb, 'AbsTol', 1e-10);
        end
    end
end
