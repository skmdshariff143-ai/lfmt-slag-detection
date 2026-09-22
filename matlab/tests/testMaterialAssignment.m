classdef testMaterialAssignment < matlab.unittest.TestCase
    methods (Test)
        function testSlagAssignment(testCase)
            grid = lfmt.createGrid(100, 70, 2.3, 40, 28, 12);
            def = struct('diameter_mm', 8.0, 'depth_mm', 0.4, 'thickness_mm', 0.4, 'center_x_mm', 50.0, 'center_y_mm', 35.0);
            [k_f, rhoCp_f, mask] = lfmt.assignMaterials(grid, def);
            
            testCase.verifyTrue(any(mask(:)), 'Defect mask must contain cells');
            testCase.verifyEqual(min(k_f(:)), 1.50, 'AbsTol', 1e-10);
            testCase.verifyEqual(max(k_f(:)), 51.90, 'AbsTol', 1e-10);
            testCase.verifyEqual(min(rhoCp_f(:)), 2800.0 * 800.0, 'AbsTol', 1e-10);
            testCase.verifyEqual(max(rhoCp_f(:)), 7860.0 * 486.0, 'AbsTol', 1e-10);
        end
    end
end
