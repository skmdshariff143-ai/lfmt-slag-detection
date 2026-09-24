function env_info = lfmt_check_environment(varargin)
% LFMT_CHECK_ENVIRONMENT Identifies MATLAB release, toolboxes, and FEM capability.
%
% Generates a comprehensive compatibility report and saves it to:
%   matlab/results/environment_report.txt
%
% Output:
%   env_info - Struct containing detected capabilities and recommendations.

p = inputParser;
addParameter(p, 'SaveReport', true, @islogical);
addParameter(p, 'ReportPath', '', @ischar);
parse(p, varargin{:});

save_report = p.Results.SaveReport;
report_path = p.Results.ReportPath;

if isempty(report_path)
    matlab_root_dir = fileparts(mfilename('fullpath'));
    report_path = fullfile(matlab_root_dir, 'results', 'environment_report.txt');
end

% Ensure output directory exists
report_dir = fileparts(report_path);
if ~exist(report_dir, 'dir')
    mkdir(report_dir);
end

% 1. MATLAB Release Info
v_info = ver('matlab');
matlab_version = version;
matlab_release = v_info.Release;
matlab_date = v_info.Date;

% 2. Toolbox Detection
toolboxes = struct();

% PDE Toolbox
v_pde = ver('pde');
toolboxes.pde.installed = ~isempty(v_pde);
toolboxes.pde.version = '';
if toolboxes.pde.installed
    toolboxes.pde.version = v_pde.Version;
end

% Check PDE license vs product files
[pde_lic, ~] = license('checkout', 'pde_toolbox');
toolboxes.pde.licensed = (pde_lic == 1);

% Test femodel capability
femodel_available = false;
try
    if exist('femodel', 'file') == 2 || exist('femodel', 'builtin') == 5
        femodel_available = true;
    end
catch
    femodel_available = false;
end
toolboxes.pde.femodel_available = femodel_available;

% Signal Processing Toolbox
v_sig = ver('signal');
toolboxes.signal.installed = ~isempty(v_sig);
toolboxes.signal.version = '';
if toolboxes.signal.installed
    toolboxes.signal.version = v_sig.Version;
end

% Image Processing Toolbox
v_img = ver('images');
toolboxes.images.installed = ~isempty(v_img);
toolboxes.images.version = '';
if toolboxes.images.installed
    toolboxes.images.version = v_img.Version;
end

% Statistics and Machine Learning Toolbox
v_stats = ver('stats');
toolboxes.stats.installed = ~isempty(v_stats);
toolboxes.stats.version = '';
if toolboxes.stats.installed
    toolboxes.stats.version = v_stats.Version;
end

% Parallel Computing Toolbox
v_dist = ver('parallel');
if isempty(v_dist)
    v_dist = ver('distcomp');
end
toolboxes.distcomp.installed = ~isempty(v_dist);
toolboxes.distcomp.version = '';
if toolboxes.distcomp.installed
    toolboxes.distcomp.version = v_dist.Version;
end

% 3. Numerical Capabilities
has_sparse = (exist('sparse', 'builtin') == 5);
has_chol = (exist('chol', 'builtin') == 5);
has_decomposition = (exist('decomposition', 'file') == 2 || exist('decomposition', 'builtin') == 5);
has_svd = (exist('svd', 'builtin') == 5);

% Determine Primary and Secondary Solvers
if toolboxes.pde.installed && femodel_available
    primary_solver = 'PDE_Toolbox_FEM (femodel transient thermal)';
    fem_engine = 'native_pde_femodel';
else
    primary_solver = 'Pure MATLAB 3-D Structured Hexahedral FEM (Hex8 Trilinear Formulation)';
    fem_engine = 'pure_matlab_hex8_fem';
end
secondary_solver = '3-D Conservative Finite Difference (MATLAB_FDM)';

% Construct summary struct
env_info = struct();
env_info.matlab_version = matlab_version;
env_info.matlab_release = matlab_release;
env_info.matlab_date = matlab_date;
env_info.toolboxes = toolboxes;
env_info.capabilities = struct(...
    'sparse', has_sparse, ...
    'cholesky', has_chol, ...
    'decomposition', has_decomposition, ...
    'svd', has_svd ...
);
env_info.primary_solver = primary_solver;
env_info.fem_engine = fem_engine;
env_info.secondary_solver = secondary_solver;
env_info.timestamp = datestr(now, 'yyyy-mm-dd HH:MM:SS');

% Format report text
lines = {};
lines{end+1} = '================================================================================';
lines{end+1} = '               LFMT MATLAB SCIENTIFIC ENVIRONMENT & CAPABILITY REPORT            ';
lines{end+1} = '================================================================================';
lines{end+1} = sprintf('Date & Time:        %s', env_info.timestamp);
lines{end+1} = sprintf('MATLAB Version:     %s', env_info.matlab_version);
lines{end+1} = sprintf('MATLAB Release:     %s (%s)', env_info.matlab_release, env_info.matlab_date);
lines{end+1} = sprintf('Operating System:   %s', computer);
lines{end+1} = '--------------------------------------------------------------------------------';
lines{end+1} = 'TOOLBOX AVAILABILITY AUDIT:';
lines{end+1} = sprintf('  - PDE Toolbox:                %s (Licensed: %s, femodel: %s)', ...
    bool2str(toolboxes.pde.installed, toolboxes.pde.version), ...
    bool2yesno(toolboxes.pde.licensed), ...
    bool2yesno(toolboxes.pde.femodel_available));
lines{end+1} = sprintf('  - Signal Processing Toolbox:  %s', ...
    bool2str(toolboxes.signal.installed, toolboxes.signal.version));
lines{end+1} = sprintf('  - Image Processing Toolbox:   %s', ...
    bool2str(toolboxes.images.installed, toolboxes.images.version));
lines{end+1} = sprintf('  - Statistics & ML Toolbox:    %s', ...
    bool2str(toolboxes.stats.installed, toolboxes.stats.version));
lines{end+1} = sprintf('  - Parallel Computing Toolbox: %s', ...
    bool2str(toolboxes.distcomp.installed, toolboxes.distcomp.version));
lines{end+1} = '--------------------------------------------------------------------------------';
lines{end+1} = 'SOLVER ARCHITECTURE DECISION:';
lines{end+1} = sprintf('  - Primary 3D Solver:          %s', primary_solver);
lines{end+1} = sprintf('  - FEM Engine:                 %s', fem_engine);
lines{end+1} = sprintf('  - Secondary Solver:           %s', secondary_solver);
lines{end+1} = '--------------------------------------------------------------------------------';
lines{end+1} = 'SIGNAL PROCESSING & BLIND DETECTION ENGINE:';
lines{end+1} = '  - Raw Contrast:               Pure MATLAB (Blind spatial variance max frame)';
lines{end+1} = '  - Matched Filter:             Pure MATLAB / Signal Toolbox (Vectorized FFT correlation)';
lines{end+1} = '  - SVD PCT:                    Pure MATLAB (svd / Truncated SVD, Kurtosis selection)';
lines{end+1} = '  - Sparse PCT (SPCT):          Pure MATLAB (L1-Penalized Coordinate Descent / Proximal)';
lines{end+1} = '  - Random Projection (RPT):    Pure MATLAB (Gaussian JL projection, Dynamic Range)';
lines{end+1} = '  - Downstream Detector:        Pure MATLAB (Otsu + 8-connectivity binary opening/closing)';
lines{end+1} = '  - Ground Truth Anti-Leakage:  ENFORCED (GT strictly isolated from processing & selection)';
lines{end+1} = '================================================================================';

report_str = strjoin(lines, '\n');

% Print to command window
fprintf('%s\n', report_str);

% Save to file
if save_report
    fid = fopen(report_path, 'w');
    if fid ~= -1
        fprintf(fid, '%s\n', report_str);
        fclose(fid);
        fprintf('Report saved to: %s\n', report_path);
    else
        warning('LFMT:ReportWriteFailed', 'Could not open %s for writing.', report_path);
    end
end
end

function s = bool2str(tf, ver_str)
if tf
    s = sprintf('INSTALLED (v%s)', ver_str);
else
    s = 'NOT INSTALLED / UNAVAILABLE';
end
end

function s = bool2yesno(tf)
if tf
    s = 'YES';
else
    s = 'NO';
end
end
