function out = cache(action, key_or_cfg, data)
% CACHE Manages deterministic hashing and caching of simulation results.
%
% Usage:
%   hash_str = lfmt.cache('hash', config_struct)
%   lfmt.cache('save', hash_str, result_data)
%   [loaded_data, exists] = lfmt.cache('load', hash_str)

cache_dir = fullfile(fileparts(mfilename('fullpath')), '..', 'results', 'cache');
if ~exist(cache_dir, 'dir')
    mkdir(cache_dir);
end

switch lower(action)
    case 'hash'
        cfg = key_or_cfg;
        json_str = jsonencode(cfg);
        
        % Compute deterministic hash in pure MATLAB
        md = java.security.MessageDigest.getInstance('SHA-256');
        bytes = md.digest(double(json_str));
        hash_str = sprintf('%02x', typecast(bytes, 'uint8'));
        out = hash_str;
        
    case 'save'
        hash_str = key_or_cfg;
        cache_file = fullfile(cache_dir, [hash_str, '.mat']);
        cached_payload = data; %#ok<NASGU>
        save(cache_file, 'cached_payload', '-v7.3');
        out = cache_file;
        
    case 'load'
        hash_str = key_or_cfg;
        cache_file = fullfile(cache_dir, [hash_str, '.mat']);
        if exist(cache_file, 'file')
            s = load(cache_file, 'cached_payload');
            out = s.cached_payload;
        else
            out = [];
        end
        
    case 'exists'
        hash_str = key_or_cfg;
        cache_file = fullfile(cache_dir, [hash_str, '.mat']);
        out = (exist(cache_file, 'file') == 2);
        
    otherwise
        error('LFMT:InvalidCacheAction', 'Unknown cache action: %s', action);
end
end
