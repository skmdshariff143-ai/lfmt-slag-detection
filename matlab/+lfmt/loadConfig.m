function config = loadConfig(json_path)
% LOADCONFIG Reads backend-independent JSON configuration file
fid = fopen(json_path, 'r');
if fid == -1
    error('Cannot open configuration file: %s', json_path);
end
raw = fread(fid, inf, 'char=>char')';
fclose(fid);

config = jsondecode(raw);
config = lfmt.validateConfig(config);
end
