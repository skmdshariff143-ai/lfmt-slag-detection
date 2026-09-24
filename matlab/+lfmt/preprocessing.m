function [T_processed, temporal_mean] = preprocessing(T_raw, method)
% PREPROCESSING Preprocesses thermogram sequence without GT dependency.
%
% Methods:
%   'mean_center' (default) - Subtracts temporal mean per pixel
%   'detrend_linear'        - Removes linear temporal trend per pixel
%   'none'                  - Validates finite numbers without modification

if nargin < 2 || isempty(method)
    method = 'mean_center';
end

% Validate finite numbers
if any(~isfinite(T_raw(:)))
    error('LFMT:NonFiniteData', 'Thermogram sequence contains NaN or Inf values.');
end

[n_frames, ny, nx] = size(T_raw);
A = reshape(T_raw, n_frames, ny * nx);

switch lower(method)
    case 'mean_center'
        temporal_mean = mean(A, 1);
        A_proc = A - temporal_mean;
        T_processed = reshape(A_proc, n_frames, ny, nx);
        
    case 'detrend_linear'
        temporal_mean = mean(A, 1);
        t_vec = (0:(n_frames-1))';
        t_centered = t_vec - mean(t_vec);
        % Vectorized linear regression detrend
        slope = (t_centered' * A) / (t_centered' * t_centered);
        A_trend = t_centered * slope + temporal_mean;
        A_proc = A - A_trend;
        T_processed = reshape(A_proc, n_frames, ny, nx);
        
    case 'none'
        temporal_mean = zeros(1, ny * nx);
        T_processed = T_raw;
        
    otherwise
        error('LFMT:UnknownPreprocessingMethod', 'Unknown preprocessing method: %s', method);
end
end
