classdef TestLFMTLiveLab < matlab.unittest.TestCase
    % TESTLFMTLIVELAB Unit & Integration tests for LFMTLiveLab application
    
    properties
        App
    end
    
    methods (TestMethodSetup)
        function createLabApp(testCase)
            root_dir = fileparts(fileparts(mfilename('fullpath')));
            addpath(root_dir);
            testCase.App = LFMTLiveLab();
        end
    end
    
    methods (TestMethodTeardown)
        function closeLabApp(testCase)
            if ~isempty(testCase.App) && isvalid(testCase.App)
                delete(testCase.App);
            end
        end
    end
    
    methods (Test)
        function testAppInitialization(testCase)
            % Verify that app starts up with valid figures and defaults
            testCase.verifyTrue(isvalid(testCase.App.UIFigure));
            testCase.verifyEqual(testCase.App.DiamEdit.Value, 8.0);
            testCase.verifyEqual(testCase.App.DepthEdit.Value, 0.4);
            testCase.verifyFalse(testCase.App.HealthyCheck.Value);
            testCase.verifyEqual(testCase.App.F0Edit.Value, 0.05);
            testCase.verifyEqual(testCase.App.F1Edit.Value, 0.50);
        end
        
        function testCaseA_CleanStandardDefect(testCase)
            % CASE A: D = 8 mm, depth = 0.4 mm, clean
            app = testCase.App;
            app.DiamEdit.Value = 8.0;
            app.DepthEdit.Value = 0.4;
            app.NoiseModeDrop.Value = 'Clean (Inf dB)';
            app.ModeDrop.Value = 'Quick Demo';
            
            app.runInspection();
            
            % Verify inspection outputs
            res = app.CurrentResults;
            testCase.verifyNotEmpty(res);
            testCase.verifyTrue(isfield(res, 'processed'));
            testCase.verifyTrue(res.processed.MF.metrics.is_detected);
            testCase.verifyTrue(res.processed.PCT.metrics.is_detected);
            testCase.verifyGreaterThan(res.processed.MF.metrics.iou, 0.5);
            testCase.verifyEqual(app.DetectionText.Text, 'DEFECT DETECTED: YES');
        end
        
        function testCaseB_DeepsDefect25dB(testCase)
            % CASE B: D = 8 mm, depth = 0.8 mm, 25 dB SNR
            app = testCase.App;
            app.DiamEdit.Value = 8.0;
            app.DepthEdit.Value = 0.8;
            app.NoiseModeDrop.Value = '25 dB SNR';
            app.SNREdit.Value = 25.0;
            app.ModeDrop.Value = 'Quick Demo';
            
            app.runInspection();
            
            res = app.CurrentResults;
            testCase.verifyNotEmpty(res);
            testCase.verifyTrue(res.processed.MF.metrics.is_detected);
            % Matched Filter should detect at 0.8mm depth
            testCase.verifyGreaterThan(res.processed.MF.metrics.cnr, 1.0);
        end
        
        function testCaseC_DeepSmallDefect20dB(testCase)
            % CASE C: D = 4 mm, depth = 1.0 mm, 20 dB SNR
            app = testCase.App;
            app.DiamEdit.Value = 4.0;
            app.DepthEdit.Value = 1.0;
            app.NoiseModeDrop.Value = '20 dB SNR';
            app.SNREdit.Value = 20.0;
            app.ModeDrop.Value = 'Quick Demo';
            
            app.runInspection();
            
            res = app.CurrentResults;
            testCase.verifyNotEmpty(res);
            testCase.verifyTrue(isfield(res, 'summary_table'));
            testCase.verifyEqual(height(res.summary_table), 5);
        end
        
        function testCaseD_HealthyPlate(testCase)
            % CASE D: Healthy plate / No Inclusion
            app = testCase.App;
            app.HealthyCheck.Value = true;
            app.onHealthyCheckChanged();
            app.ModeDrop.Value = 'Quick Demo';
            
            app.runInspection();
            
            res = app.CurrentResults;
            testCase.verifyNotEmpty(res);
            testCase.verifyTrue(isfield(res, 'summary_table'));
            testCase.verifyEqual(height(res.summary_table), 5);
        end
        
        function testSaveAndExportRoutines(testCase)
            app = testCase.App;
            app.ModeDrop.Value = 'Quick Demo';
            app.runInspection();
            
            % Test programmatic export
            app.saveResults();
            app.exportReport();
            
            root_dir = fileparts(fileparts(mfilename('fullpath')));
            export_dir = fullfile(root_dir, 'results', 'exports');
            testCase.verifyTrue(exist(export_dir, 'dir') > 0);
        end
    end
end
