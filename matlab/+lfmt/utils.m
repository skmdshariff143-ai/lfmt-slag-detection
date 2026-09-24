function out = utils(action, varargin)
% UTILS Miscellaneous helper utilities for LFMT MATLAB pipeline.

switch lower(action)
    case 'ensure_dir'
        dir_path = varargin{1};
        if ~exist(dir_path, 'dir')
            mkdir(dir_path);
        end
        out = dir_path;
        
    case 'normalize_min_max'
        arr = varargin{1};
        min_v = min(arr(:));
        max_v = max(arr(:));
        if (max_v - min_v) > 1e-12
            out = (arr - min_v) / (max_v - min_v);
        else
            out = zeros(size(arr));
        end
        
    case 'format_time'
        seconds = varargin{1};
        if seconds < 60
            out = sprintf('%.2f s', seconds);
        elseif seconds < 3600
            out = sprintf('%.1f min', seconds / 60.0);
        else
            out = sprintf('%.2f hr', seconds / 3600.0);
        end
        
    otherwise
        error('LFMT:InvalidUtilsAction', 'Unknown action "%s".', action);
end
end
