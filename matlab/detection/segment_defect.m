function det_result = segment_defect(score_map, fov_mm, min_area_px)
% SEGMENT_DEFECT Blind Defect Segmentation and Candidate Isolation Pipeline.
%
% Complete Pipeline:
%   Score map -> Robust [0,1] normalization -> Otsu threshold ->
%   Binary opening -> Binary closing -> 8-connected components ->
%   Candidate isolation (area >= min_area_px) -> Physical characterization.
%
% CRITICAL: Ground truth is STRICTLY forbidden and not passed as input.

t_start = tic;

if nargin < 2 || isempty(fov_mm), fov_mm = [100.0, 70.0]; end
if nargin < 3 || isempty(min_area_px), min_area_px = 3; end

[ny, nx] = size(score_map);
fov_x_mm = fov_mm(1);
fov_y_mm = fov_mm(2);

dx_mm_px = fov_x_mm / max(1, nx - 1);
dy_mm_px = fov_y_mm / max(1, ny - 1);
pixel_area_mm2 = dx_mm_px * dy_mm_px;

% 1. Robust normalization
norm_map = normalize_score_map(score_map);

% 2. Otsu thresholding
thresh = compute_otsu_threshold(norm_map);
binary_raw = norm_map >= thresh;

% 3. Morphological filtering: 8-connected opening and closing (3x3 kernel)
struct_elem = ones(3, 3);
if exist('imopen', 'file') == 2 && exist('imclose', 'file') == 2
    binary_clean = imclose(imopen(binary_raw, struct_elem), struct_elem);
else
    % Pure MATLAB fallback morphological opening and closing
    binary_open = conv2(double(binary_raw), struct_elem, 'same') >= 9;
    binary_open = conv2(double(binary_open), struct_elem, 'same') >= 1;
    binary_close = conv2(double(binary_open), struct_elem, 'same') >= 1;
    binary_clean = conv2(double(binary_close), struct_elem, 'same') >= 9;
end

% 4. 8-Connected Component Analysis
if exist('bwlabel', 'file') == 2
    [labeled_matrix, num_features] = bwlabel(binary_clean, 8);
else
    % Pure MATLAB BFS connected components
    [labeled_matrix, num_features] = pure_matlab_bwlabel(binary_clean);
end

% 5. Candidate Extraction
candidates = [];
for comp_id = 1:num_features
    comp_mask = (labeled_matrix == comp_id);
    area_px = sum(comp_mask(:));
    
    if area_px >= min_area_px
        [rows, cols] = find(comp_mask);
        
        % Centroid in pixel coordinates (0-indexed or 1-indexed; using 1-indexed center of mass)
        cy_px = mean(rows) - 1.0;
        cx_px = mean(cols) - 1.0;
        
        % Centroid in physical mm
        cx_mm = cx_px * dx_mm_px;
        cy_mm = cy_px * dy_mm_px;
        
        area_mm2 = area_px * pixel_area_mm2;
        equiv_diam_mm = 2.0 * sqrt(area_mm2 / pi);
        
        bbox = [min(rows), min(cols), max(rows), max(cols)];
        
        mu_in = mean(norm_map(comp_mask));
        mu_out = mean(norm_map(~comp_mask));
        conf = max(0.0, (mu_in - mu_out) / (mu_out + 1e-6));
        
        cand = struct(...
            'id', comp_id, ...
            'mask', comp_mask, ...
            'area_px', area_px, ...
            'area_mm2', area_mm2, ...
            'centroid_px', [cx_px, cy_px], ...
            'centroid_mm', [cx_mm, cy_mm], ...
            'equivalent_diameter_mm', equiv_diam_mm, ...
            'bounding_box', bbox, ...
            'confidence_score', conf, ...
            'ranking_score', conf * sqrt(double(area_px)) ...
        );
        candidates = [candidates; cand]; %#ok<AGROW>
    end
end

% 6. Primary Candidate Selection
if ~isempty(candidates)
    % Sort by ranking score descending
    [~, sort_idx] = sort([candidates.ranking_score], 'descend');
    top_cand = candidates(sort_idx(1));
    
    is_detected = true;
    pred_mask = top_cand.mask;
    centroid_px = top_cand.centroid_px;
    centroid_mm = top_cand.centroid_mm;
    equiv_diam_mm = top_cand.equivalent_diameter_mm;
    area_px = top_cand.area_px;
    area_mm2 = top_cand.area_mm2;
    bbox = top_cand.bounding_box;
    conf_score = top_cand.confidence_score;
else
    is_detected = false;
    pred_mask = false(ny, nx);
    centroid_px = [NaN, NaN];
    centroid_mm = [NaN, NaN];
    equiv_diam_mm = NaN;
    area_px = 0;
    area_mm2 = 0.0;
    bbox = [0, 0, 0, 0];
    conf_score = 0.0;
end

runtime_s = toc(t_start);

det_result = struct(...
    'is_detected', is_detected, ...
    'predicted_mask', pred_mask, ...
    'centroid_px', centroid_px, ...
    'centroid_mm', centroid_mm, ...
    'equivalent_diameter_mm', equiv_diam_mm, ...
    'area_px', area_px, ...
    'area_mm2', area_mm2, ...
    'bounding_box', bbox, ...
    'confidence_score', conf_score, ...
    'threshold_value', thresh, ...
    'threshold_method', 'otsu', ...
    'num_candidates', length(candidates), ...
    'all_candidates', candidates, ...
    'runtime_s', runtime_s ...
);
end

function [labeled_matrix, num_features] = pure_matlab_bwlabel(binary_img)
[ny, nx] = size(binary_img);
labeled_matrix = zeros(ny, nx);
num_features = 0;

for r = 1:ny
    for c = 1:nx
        if binary_img(r, c) && labeled_matrix(r, c) == 0
            num_features = num_features + 1;
            % BFS Queue
            queue = [r, c];
            labeled_matrix(r, c) = num_features;
            head = 1;
            
            while head <= size(queue, 1)
                curr_r = queue(head, 1);
                curr_c = queue(head, 2);
                head = head + 1;
                
                % 8 neighbors
                for dr = -1:1
                    for dc = -1:1
                        nr = curr_r + dr;
                        nc = curr_c + dc;
                        if nr >= 1 && nr <= ny && nc >= 1 && nc <= nx
                            if binary_img(nr, nc) && labeled_matrix(nr, nc) == 0
                                labeled_matrix(nr, nc) = num_features;
                                queue(end+1, :) = [nr, nc]; %#ok<AGROW>
                            end
                        end
                    end
                end
            end
        end
    end
end
end
