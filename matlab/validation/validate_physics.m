function phys_report = validate_physics(quick)
% VALIDATE_PHYSICS Comprehensive physics sanity and conservation verification.
%
% Checks:
%   1. Zero Heat Flux: Temperature remains exactly constant at Tamb
%   2. Linearity: Temperature rise Delta T scales linearly with q0
%   3. Material Contrast: Slag defect induces positive differential surface contrast
%   4. Depth Attenuation: Deeper inclusions exhibit reduced surface contrast
%   5. Physical Bounds: Temperature is finite, non-negative, and bounded

if nargin < 1 || isempty(quick), quick = true; end

fprintf('================================================================================\n');
fprintf('                 3-D FEM PHYSICAL SANITY & CONSERVATION AUDIT                   \n');
fprintf('================================================================================\n');

checks_passed = 0;
total_checks = 5;

cfg_base = default_config();
if quick
    cfg_base.simulation.total_time_s = 3.0;
    cfg_base.excitation.duration_s = 3.0;
    cfg_base.simulation.Nx = 20;
    cfg_base.simulation.Ny = 14;
    cfg_base.simulation.Nz = 6;
end

% Check 1: Zero Flux Equilibrium
fprintf('Check 1: Zero Heat Flux Thermal Equilibrium...\n');
cfg_zero = cfg_base;
cfg_zero.excitation.q0_w_m2 = 0.0;
res_zero = lfmt_simulate_fem(cfg_zero);
max_dev_zero = max(abs(res_zero.surface_temperature(:) - cfg_zero.excitation.ambient_temp_k));
pass_1 = max_dev_zero < 1e-4;
if pass_1
    fprintf('  [PASS] Zero-flux temperature deviation = %.2e K (< 1e-4 K)\n', max_dev_zero);
    checks_passed = checks_passed + 1;
else
    fprintf('  [FAIL] Zero-flux temperature deviation = %.2e K\n', max_dev_zero);
end

% Check 2: Excitation Linearity (q0 vs 2*q0)
fprintf('Check 2: Heat Flux Scaling Linearity...\n');
cfg_q1 = cfg_base;
cfg_q1.excitation.q0_w_m2 = 2500.0;
res_q1 = lfmt_simulate_fem(cfg_q1);

cfg_q2 = cfg_base;
cfg_q2.excitation.q0_w_m2 = 5000.0;
res_q2 = lfmt_simulate_fem(cfg_q2);

delta_T1 = res_q1.surface_temperature - cfg_base.excitation.ambient_temp_k;
delta_T2 = res_q2.surface_temperature - cfg_base.excitation.ambient_temp_k;
linearity_err = max(abs(delta_T2(:) - 2.0 * delta_T1(:))) / (max(abs(delta_T2(:))) + 1e-12);
pass_2 = linearity_err < 1e-3;
if pass_2
    fprintf('  [PASS] Scaling linearity relative error = %.2e (< 1e-3)\n', linearity_err);
    checks_passed = checks_passed + 1;
else
    fprintf('  [FAIL] Scaling linearity relative error = %.2e\n', linearity_err);
end

% Check 3: Material Contrast Signature
fprintf('Check 3: Slag Inclusion Thermal Contrast Generation...\n');
cfg_slag = cfg_base;
cfg_slag.defects(1).diameter_mm = 8.0;
cfg_slag.defects(1).depth_mm = 0.4;
res_slag = lfmt_simulate_fem(cfg_slag);

% Center pixel (over defect) vs corner pixel (sound plate)
[~, ny, nx] = size(res_slag.surface_temperature);
T_center = squeeze(res_slag.surface_temperature(:, round(ny/2), round(nx/2)));
T_sound = squeeze(res_slag.surface_temperature(:, 2, 2));
max_contrast = max(T_center - T_sound);
pass_3 = max_contrast > 0.005; % Positive thermal accumulation over low-conductivity slag
if pass_3
    fprintf('  [PASS] Defect peak thermal contrast = +%.4f K (> 0)\n', max_contrast);
    checks_passed = checks_passed + 1;
else
    fprintf('  [FAIL] Defect peak thermal contrast = %.4f K\n', max_contrast);
end

% Check 4: Depth Attenuation
fprintf('Check 4: Depth Signature Attenuation (z = 0.2 mm vs z = 0.8 mm)...\n');
cfg_shallow = cfg_base;
cfg_shallow.defects(1).depth_mm = 0.2;
res_shallow = lfmt_simulate_fem(cfg_shallow);
c_shallow = max(squeeze(res_shallow.surface_temperature(:, round(ny/2), round(nx/2))) - squeeze(res_shallow.surface_temperature(:, 2, 2)));

cfg_deep = cfg_base;
cfg_deep.defects(1).depth_mm = 0.8;
res_deep = lfmt_simulate_fem(cfg_deep);
c_deep = max(squeeze(res_deep.surface_temperature(:, round(ny/2), round(nx/2))) - squeeze(res_deep.surface_temperature(:, 2, 2)));

pass_4 = c_shallow > c_deep;
if pass_4
    fprintf('  [PASS] Shallow contrast (%.4f K) > Deep contrast (%.4f K)\n', c_shallow, c_deep);
    checks_passed = checks_passed + 1;
else
    fprintf('  [FAIL] Shallow contrast (%.4f K) <= Deep contrast (%.4f K)\n', c_shallow, c_deep);
end

% Check 5: Physical Bounds and Finiteness
fprintf('Check 5: Non-negative and Finite Temperature Fields...\n');
all_finite = all(isfinite(res_slag.surface_temperature(:)));
all_positive = all(res_slag.surface_temperature(:) > 0.0);
pass_5 = all_finite && all_positive;
if pass_5
    fprintf('  [PASS] Temperature is finite and strictly positive (> 0 K)\n');
    checks_passed = checks_passed + 1;
else
    fprintf('  [FAIL] Non-finite or negative temperatures encountered\n');
end

fprintf('--------------------------------------------------------------------------------\n');
fprintf('Physics Sanity Summary: %d / %d checks passed.\n', checks_passed, total_checks);
fprintf('================================================================================\n');

phys_report = struct(...
    'total_checks', total_checks, ...
    'checks_passed', checks_passed, ...
    'all_passed', (checks_passed == total_checks), ...
    'check_1_zero_flux', pass_1, ...
    'check_2_linearity', pass_2, ...
    'check_3_material_contrast', pass_3, ...
    'check_4_depth_attenuation', pass_4, ...
    'check_5_bounds', pass_5 ...
);

% Save summary
matlab_dir = fileparts(fileparts(mfilename('fullpath')));
out_json = fullfile(matlab_dir, 'results', 'validation', 'physics_validation.json');
fid = fopen(out_json, 'w');
if fid ~= -1
    fprintf(fid, '%s\n', jsonencode(phys_report));
    fclose(fid);
end
end
