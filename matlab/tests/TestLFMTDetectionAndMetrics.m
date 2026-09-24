classdef TestLFMTDetectionAndMetrics < matlab.unittest.TestCase
    % TESTLFMTDETECTIONANDMETRICS Unit tests for segmentation pipeline and evaluation metrics.

    methods (Test)
        function testSegmentationSyntheticDisc(testCase)
            [ny, nx] = deal(64, 64);
            [X, Y] = meshgrid(1:nx, 1:ny);
            disc = ((X - 32).^2 + (Y - 32).^2) <= (6^2);
            
            score_map = double(disc) * 10.0 + randn(ny, nx) * 0.1;
            det = segment_defect(score_map, [100.0, 70.0], 3);
            
            testCase.verifyTrue(det.is_detected);
            testCase.verifyGreaterThan(det.area_px, 50);
            testCase.verifyEqual(det.centroid_px(1), 31.0, 'AbsTol', 1.0);
            testCase.verifyEqual(det.centroid_px(2), 31.0, 'AbsTol', 1.0);
        end

        function testMetricsEvaluation(testCase)
            [ny, nx] = deal(64, 64);
            [X, Y] = meshgrid(linspace(0, 100, nx), linspace(0, 70, ny));
            gt_mask = ((X - 50).^2 + (Y - 35).^2) <= (4^2);
            
            % Perfect detection
            det_perfect = struct(...
                'is_detected', true, ...
                'predicted_mask', gt_mask, ...
                'centroid_px', [31.5, 31.5], ...
                'centroid_mm', [50.0, 35.0], ...
                'equivalent_diameter_mm', 8.0, ...
                'area_px', sum(gt_mask(:)), ...
                'area_mm2', pi * 4^2 ...
            );
            
            geom = struct(...
                'has_defect', true, ...
                'defect', struct('center_x_mm', 50.0, 'center_y_mm', 35.0, 'diameter_mm', 8.0, 'area_mm2', pi*16, 'radius_m', 0.004) ...
            );
            
            score_map = double(gt_mask);
            m = compute_metrics('Perfect', det_perfect, geom, gt_mask, score_map, 0.1, [100.0, 70.0]);
            
            testCase.verifyEqual(m.iou, 1.0, 'AbsTol', 1e-4);
            testCase.verifyEqual(m.dice, 1.0, 'AbsTol', 1e-4);
            testCase.verifyEqual(m.localization_error_mm, 0.0, 'AbsTol', 1e-4);
            testCase.verifyTrue(m.is_detected);
        end

        function testHealthyPlateSpecificity(testCase)
            [ny, nx] = deal(64, 64);
            gt_mask_clean = false(ny, nx);
            
            det_clean = struct(...
                'is_detected', false, ...
                'predicted_mask', false(ny, nx), ...
                'centroid_px', [NaN, NaN], ...
                'centroid_mm', [NaN, NaN], ...
                'equivalent_diameter_mm', NaN, ...
                'area_px', 0, ...
                'area_mm2', 0.0 ...
            );
            
            geom_healthy = struct('has_defect', false, 'defect', struct('diameter_mm', 0, 'area_mm2', 0));
            score_map = zeros(ny, nx);
            
            m_healthy = compute_metrics('Healthy', det_clean, geom_healthy, gt_mask_clean, score_map, 0.1, [100.0, 70.0]);
            
            testCase.verifyFalse(m_healthy.is_false_positive);
            testCase.verifyEqual(m_healthy.specificity, 1.0);
            testCase.verifyTrue(isnan(m_healthy.localization_error_mm));
        end
    end
end
