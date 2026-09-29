function sim_result = run_lfmt_simulation(config)
% RUN_LFMT_SIMULATION Top-level entry point for MATLAB 3-D FDM simulation
if nargin < 1
    config = struct();
end
config = lfmt.validateConfig(config);
sim_result = lfmt.solveTransientThermal(config);
end
