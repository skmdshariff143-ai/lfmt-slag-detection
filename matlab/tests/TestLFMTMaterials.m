classdef TestLFMTMaterials < matlab.unittest.TestCase
    % TESTLFTMMATERIALS Unit tests for material properties and derived quantities.

    methods (Test)
        function testMildSteelProperties(testCase)
            mat = lfmt.materials('mild_steel');
            testCase.verifyEqual(mat.thermal_conductivity, 51.9, 'AbsTol', 1e-3);
            testCase.verifyEqual(mat.density, 7850.0, 'AbsTol', 1e-3);
            testCase.verifyEqual(mat.specific_heat, 486.0, 'AbsTol', 1e-3);
            
            % Derived
            expected_alpha = 51.9 / (7850 * 486);
            testCase.verifyEqual(mat.thermal_diffusivity, expected_alpha, 'AbsTol', 1e-8);
        end

        function testSlagProperties(testCase)
            mat = lfmt.materials('slag');
            testCase.verifyEqual(mat.thermal_conductivity, 1.20, 'AbsTol', 1e-3);
            testCase.verifyEqual(mat.density, 2800.0, 'AbsTol', 1e-3);
            testCase.verifyEqual(mat.specific_heat, 850.0, 'AbsTol', 1e-3);
        end

        function testUnknownMaterialError(testCase)
            testCase.verifyError(@() lfmt.materials('unobtanium'), 'LFMT:UnknownMaterial');
        end
    end
end
