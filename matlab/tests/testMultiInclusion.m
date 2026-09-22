classdef testMultiInclusion < matlab.unittest.TestCase
    methods (Test)
        function testMultipleDefectsAssigned(testCase)
            grid = lfmt.createGrid(100, 70, 2.3, 40, 28, 12);
            defs = [
                struct('diameter_mm', 6.0, 'depth_mm', 0.4, 'thickness_mm', 0.4, 'center_x_mm', 42.5, 'center_y_mm', 35.0), ...
                struct('diameter_mm', 4.8, 'depth_mm', 0.4, 'thickness_mm', 0.4, 'center_x_mm', 57.5, 'center_y_mm', 35.0)
            ];
            [k_f, rhoCp_f, mask] = lfmt.assignMaterials(grid, defs);
            testCase.verifyTrue(sum(mask(:)) > 0, 'Multiple inclusions must occupy grid cells');
        end
    end
end
