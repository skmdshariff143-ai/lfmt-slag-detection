function run_lfmt_from_json(json_config_path, output_mat_path)
% RUN_LFMT_FROM_JSON Batch entry point for headless / CLI execution
config = lfmt.loadConfig(json_config_path);
sim_result = lfmt.solveTransientThermal(config);
lfmt.exportSimulation(sim_result, output_mat_path, config);
fprintf('Simulation complete. Output written to: %s\n', output_mat_path);
end
