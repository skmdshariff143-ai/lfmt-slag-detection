classdef TestLFMTCameraAndNoise < matlab.unittest.TestCase
    % TESTLFTMCAMERAANDNOISE Unit tests for camera acquisition and reproducible AWGN.

    methods (Test)
        function testCameraDimensions(testCase)
            T_dummy = ones(101, 15, 20);
            t_dummy = linspace(0, 10, 101);
            x_m = linspace(0, 0.1, 20);
            y_m = linspace(0, 0.07, 15);
            
            [T_cam, t_cam, x_mm, y_mm] = lfmt.camera(T_dummy, t_dummy, x_m, y_m, 64, 64, 25.0, 10.0);
            
            testCase.verifyEqual(size(T_cam), [251, 64, 64]);
            testCase.verifyEqual(length(t_cam), 251);
            testCase.verifyEqual(length(x_mm), 64);
            testCase.verifyEqual(length(y_mm), 64);
        end

        function testNoiseDeterminismAndSNR(testCase)
            T_clean = 300 + 5 * rand(100, 32, 32);
            [T_n1, sigma1] = lfmt.noise(T_clean, 30, 1001);
            [T_n2, sigma2] = lfmt.noise(T_clean, 30, 1001);
            [T_n3, ~] = lfmt.noise(T_clean, 30, 1002);
            
            testCase.verifyEqual(T_n1, T_n2);
            testCase.verifyNotEqual(T_n1, T_n3);
            testCase.verifyGreaterThan(sigma1, 0.0);
            testCase.verifyEqual(sigma1, sigma2);
        end
    end
end
