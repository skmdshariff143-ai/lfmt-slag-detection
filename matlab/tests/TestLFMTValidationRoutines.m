classdef TestLFMTValidationRoutines < matlab.unittest.TestCase
    % TESTLFMTVALIDATIONROUTINES Unit tests for validation functions.

    methods (Test)
        function testPhysicsSanityValidation(testCase)
            phys_rep = validate_physics(true);
            testCase.verifyTrue(phys_rep.all_passed);
            testCase.verifyEqual(phys_rep.checks_passed, 5);
        end

        function testMeshConvergenceSmoke(testCase)
            mesh_rep = validate_mesh(true);
            testCase.verifyGreaterThanOrEqual(height(mesh_rep.table), 3);
            testCase.verifyLessThan(mesh_rep.table.relative_l2_error(1), 0.15);
        end

        function testTimestepConvergenceSmoke(testCase)
            dt_rep = validate_timestep(true);
            testCase.verifyGreaterThanOrEqual(height(dt_rep.table), 3);
            testCase.verifyLessThan(dt_rep.table.relative_l2_error(1), 0.10);
        end
    end
end
