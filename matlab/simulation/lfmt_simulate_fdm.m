function sim_result = lfmt_simulate_fdm(config)
% LFMT_SIMULATE_FDM 3-D Conservative Finite-Difference Transient Thermal Solver (MATLAB_FDM).
%
% Wraps the conservative finite-difference solver as a secondary backend
% and validation reference.

if ischar(config) || isstring(config)
    config = lfmt.loadConfig(config);
end

sim_result = lfmt.solveTransientThermal(config);
sim_result.solver_name = 'MATLAB_FDM';
sim_result.discretization = '3-D Conservative Finite Difference';
end
