classdef TestLFMTProcessingBlindness < matlab.unittest.TestCase
    % TESTLFMTPROCESSINGBLINDNESS Verifies zero ground-truth dependency and algorithm properties.

    methods (Test)
        function testPCTZeroGTLossless(testCase)
            % Synthetic thermogram with centered Gaussian anomaly
            [ny, nx, nt] = deal(32, 32, 50);
            [X, Y] = meshgrid(1:nx, 1:ny);
            defect_spot = exp(-((X - 16).^2 + (Y - 16).^2) / (2 * 3^2));
            
            T_synth = zeros(nt, ny, nx);
            for t = 1:nt
                T_synth(t, :, :) = 300 + 0.1 * t + (sin(t * 0.2) + 1.0) * defect_spot;
            end
            
            % Must execute with NO ground truth input
            res_pct = lfmt_pct(T_synth, 6);
            testCase.verifyEqual(size(res_pct.score_map), [ny, nx]);
            testCase.verifyEqual(res_pct.selection_method, 'blind_excess_kurtosis');
            testCase.verifyGreaterThan(max(res_pct.normalized_map(:)), 0.0);
        end

        function testSPCTSparsity(testCase)
            [ny, nx, nt] = deal(32, 32, 50);
            [X, Y] = meshgrid(1:nx, 1:ny);
            defect_spot = exp(-((X - 16).^2 + (Y - 16).^2) / (2 * 3^2));
            
            T_synth = zeros(nt, ny, nx);
            for t = 1:nt
                T_synth(t, :, :) = 300 + 0.1 * t + (sin(t * 0.2) + 1.0) * defect_spot;
            end
            
            res_spct = lfmt_spct(T_synth, 6, 0.20);
            testCase.verifyEqual(size(res_spct.score_map), [ny, nx]);
            testCase.verifyLessThan(min(res_spct.non_zero_ratios), 1.0); % Sparsity enforced
        end

        function testRPTDistancePreservation(testCase)
            % Test Johnson-Lindenstrauss approximate distance preservation
            nt = 100;
            np = 50;
            X_data = randn(np, nt);
            
            % Pairwise distances in original space
            d_orig = zeros(np, np);
            for i = 1:np
                for j = 1:np
                    d_orig(i, j) = norm(X_data(i, :) - X_data(j, :));
                end
            end
            
            k_dim = 40;
            rng(42);
            Phi = randn(k_dim, nt) / sqrt(double(k_dim));
            Y_proj = (Phi * X_data')'; % (np, k_dim)
            
            d_proj = zeros(np, np);
            for i = 1:np
                for j = 1:np
                    d_proj(i, j) = norm(Y_proj(i, :) - Y_proj(j, :));
                end
            end
            
            % Check correlation of pairwise distances
            d_orig_vec = d_orig(:);
            d_proj_vec = d_proj(:);
            r = corrcoef(d_orig_vec, d_proj_vec);
            testCase.verifyGreaterThan(r(1, 2), 0.70); % High distance preservation
        end
    end
end
