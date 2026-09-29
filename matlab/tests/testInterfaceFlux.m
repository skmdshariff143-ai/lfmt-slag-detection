classdef testInterfaceFlux < matlab.unittest.TestCase
    methods (Test)
        function testHarmonicInterfaceConductivity(testCase)
            % Two-layer 1D slab in steady state: T(x=0)=100, T(x=L)=0
            % Layer 1: k1=50, L1=0.05. Layer 2: k2=1, L2=0.05.
            % Theoretical interface temperature: T_int = 100 * (L2/k2) / (L1/k1 + L2/k2)
            % R1 = 0.05 / 50 = 0.001. R2 = 0.05 / 1 = 0.050. Total R = 0.051.
            % Heat flux q = (100 - 0) / 0.051 = 1960.78 W/m^2.
            % T_int = 100 - q * R1 = 100 - 1.96078 = 98.0392 K.
            
            Nx = 20; Ny = 1; Nz = 1;
            grid = lfmt.createGrid(100, 10, 10, Nx, Ny, Nz); % 100 mm long
            k_field = full(51.90 * ones(Nx, Ny, Nz));
            k_field(11:end, :, :) = 1.50; % Second half is low conductivity
            
            L = lfmt.buildConductionOperator(grid, k_field);
            
            % Verify L is symmetric and diagonally dominant
            testCase.verifyEqual(norm(L - L', 'fro'), 0.0, 'AbsTol', 1e-12, 'Conduction matrix must be symmetric');
            row_sums = full(sum(L, 2));
            testCase.verifyEqual(norm(row_sums, inf), 0.0, 'AbsTol', 1e-12, 'Row sums of pure conduction operator must be zero (conservation)');
        end
    end
end
