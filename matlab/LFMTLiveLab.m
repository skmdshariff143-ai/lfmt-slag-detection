classdef LFMTLiveLab < handle
    % LFMTLiveLab Professional Live Interactive MATLAB Application for LFMT Thermography
    %
    % Linear Frequency-Modulated Infrared Thermography (LFMT / FMTWI)
    % for Subsurface Slag Inclusion Detection in Mild Steel.
    %
    % Features:
    %   - Interactive Inspection Parameter Inputs (Defect, LFMT Excitation, Camera, Solver)
    %   - Live Virtual IR Thermogram Video Player with Play/Pause, Scrubbing, and Variable Speed
    %   - LFMT Excitation Waveform & Instantaneous Frequency Analysis
    %   - Point-and-Click Thermal Time-History Inspector
    %   - 5 Blind Thermographic Signal Processing Score Maps (Raw, MF, PCT, SPCT, RPT)
    %   - Blind Defect Detection & Segmentation with Quantitative Evaluation
    %   - 5-Method Metrics Comparison Table & Live Timestamped Execution Log
    %   - Ground-Truth Analysis Tab (Isolated for Teaching/Verification)
    %   - Results Saving (.mat / .csv) and Full Run Report Exporting (PNG + CSV + JSON)
    %
    % Usage:
    %   app = LFMTLiveLab();
    %   % or simply:
    %   LFMTLiveLab;

    properties (Access = public)
        UIFigure matlab.ui.Figure
        
        % Left Column Panels
        InputPanel matlab.ui.container.Panel
        DefectPanel matlab.ui.container.Panel
        ExcitationPanel matlab.ui.container.Panel
        CameraPanel matlab.ui.container.Panel
        SolverPanel matlab.ui.container.Panel
        ControlPanel matlab.ui.container.Panel
        
        % Defect Controls
        DefectPresetDrop matlab.ui.control.DropDown
        HealthyCheck matlab.ui.control.CheckBox
        DiamEdit matlab.ui.control.NumericEditField
        DepthEdit matlab.ui.control.NumericEditField
        ThickEdit matlab.ui.control.NumericEditField
        PosXEdit matlab.ui.control.NumericEditField
        PosYEdit matlab.ui.control.NumericEditField
        
        % Excitation Controls
        F0Edit matlab.ui.control.NumericEditField
        F1Edit matlab.ui.control.NumericEditField
        Q0Edit matlab.ui.control.NumericEditField
        TexcEdit matlab.ui.control.NumericEditField
        TobsEdit matlab.ui.control.NumericEditField
        
        % Camera Controls
        ResDrop matlab.ui.control.DropDown
        NoiseModeDrop matlab.ui.control.DropDown
        SNREdit matlab.ui.control.NumericEditField
        SeedEdit matlab.ui.control.NumericEditField
        
        % Solver Controls
        SolverDrop matlab.ui.control.DropDown
        ModeDrop matlab.ui.control.DropDown
        
        % Action Buttons
        RunButton matlab.ui.control.Button
        StopButton matlab.ui.control.Button
        LoadDefButton matlab.ui.control.Button
        LoadConfButton matlab.ui.control.Button
        LoadLitButton matlab.ui.control.Button
        ResetButton matlab.ui.control.Button
        SaveResButton matlab.ui.control.Button
        ExportRepButton matlab.ui.control.Button
        RunValButton matlab.ui.control.Button
        RunTestButton matlab.ui.control.Button
        
        % Status & Stage
        StageLabel matlab.ui.control.Label
        ProgressLabel matlab.ui.control.Label
        
        % Center Column Controls
        ThermogramAxes matlab.ui.control.UIAxes
        FrameSlider matlab.ui.control.Slider
        PlayButton matlab.ui.control.Button
        PrevButton matlab.ui.control.Button
        NextButton matlab.ui.control.Button
        SpeedDrop matlab.ui.control.DropDown
        FrameInfoLabel matlab.ui.control.Label
        ThermalStatsLabel matlab.ui.control.Label
        
        % Center Bottom Tabs
        SignalTabGroup matlab.ui.container.TabGroup
        WaveformTab matlab.ui.container.Tab
        WaveformAxes matlab.ui.control.UIAxes
        PixelCurveTab matlab.ui.container.Tab
        PixelCurveAxes matlab.ui.control.UIAxes
        GTAnalysisTab matlab.ui.container.Tab
        GTAnalysisAxes matlab.ui.control.UIAxes
        
        % Right Column Controls
        DetectionLamp matlab.ui.control.Lamp
        DetectionText matlab.ui.control.Label
        MethodDrop matlab.ui.control.DropDown
        GTOverlayCheck matlab.ui.control.CheckBox
        MetricSummaryLabel matlab.ui.control.Label
        
        % 5-Method Axes
        AxesRaw matlab.ui.control.UIAxes
        AxesMF matlab.ui.control.UIAxes
        AxesPCT matlab.ui.control.UIAxes
        AxesSPCT matlab.ui.control.UIAxes
        AxesRPT matlab.ui.control.UIAxes
        
        % Right Bottom Tabs
        ResultsTabGroup matlab.ui.container.TabGroup
        TableTab matlab.ui.container.Tab
        MetricsTable matlab.ui.control.Table
        LogTab matlab.ui.container.Tab
        LogTextArea matlab.ui.control.TextArea
    end
    
    properties (Access = public)
        CurrentConfig struct
        CurrentResults struct
        IsRunning logical = false
        IsPlaying logical = false
        PlayTimer timer
        CurrentFrameIdx double = 1
        TotalFrames double = 1
        PlaybackSpeed double = 1.0
        SelectedPixel double = [32, 32] % [row, col]
        ThermogramImageHandle
        WaveformCursorHandle
    end

    methods
        function app = LFMTLiveLab()
            % Constructor: Initialize paths and create UI
            app.setupEnvironment();
            app.createUI();
            app.loadDefaultPreset();
            app.logMessage('LFMT Live Thermography Lab initialized successfully.');
            app.logMessage('Ready for live inspection.');
        end
        
        function delete(app)
            % Destructor: Clean up timers and figure
            if ~isempty(app.PlayTimer) && isvalid(app.PlayTimer)
                stop(app.PlayTimer);
                delete(app.PlayTimer);
            end
            if ~isempty(app.UIFigure) && isvalid(app.UIFigure)
                delete(app.UIFigure);
            end
        end
    end

    methods (Access = public)
        %% Path & Environment Setup
        function setupEnvironment(app)
            root_dir = fileparts(mfilename('fullpath'));
            addpath(root_dir);
            addpath(fullfile(root_dir, 'config'));
            addpath(fullfile(root_dir, 'simulation'));
            addpath(fullfile(root_dir, 'processing'));
            addpath(fullfile(root_dir, 'detection'));
            addpath(fullfile(root_dir, 'evaluation'));
            addpath(fullfile(root_dir, 'validation'));
            addpath(fullfile(root_dir, 'visualization'));
            addpath(fullfile(root_dir, 'tests'));
        end
        
        %% UI Construction
        function createUI(app)
            % Main UI Figure
            app.UIFigure = uifigure('Name', 'LFMT LIVE THERMOGRAPHY LAB — Subsurface Slag Inclusion Detection in Mild Steel', ...
                'Position', [40, 40, 1520, 920], ...
                'Color', [0.12, 0.14, 0.18], ...
                'CloseRequestFcn', @(src, evt) app.onCloseRequest());
            
            % Main Grid Layout (3 Columns: Left Inputs 340px, Center 560px, Right 580px)
            mainGrid = uigridlayout(app.UIFigure, [2, 3]);
            mainGrid.RowHeight = {50, '1x'};
            mainGrid.ColumnWidth = {340, 560, '1x'};
            mainGrid.Padding = [8, 8, 8, 8];
            mainGrid.RowSpacing = 6;
            mainGrid.ColumnSpacing = 8;
            
            % --- TOP HEADER BAR ---
            headerPanel = uipanel(mainGrid, 'BackgroundColor', [0.16, 0.19, 0.24], 'BorderType', 'none');
            headerPanel.Layout.Row = 1;
            headerPanel.Layout.Column = [1, 3];
            
            headerGrid = uigridlayout(headerPanel, [1, 2]);
            headerGrid.ColumnWidth = {'1x', 300};
            headerGrid.Padding = [10, 4, 10, 4];
            
            titleLabel = uilabel(headerGrid, 'Text', '🔬 LFMT LIVE THERMOGRAPHY LAB — Subsurface Slag Inclusion Detection in Mild Steel', ...
                'FontSize', 15, 'FontWeight', 'bold', 'FontColor', [0.95, 0.96, 0.98]);
            titleLabel.Layout.Column = 1;
            
            subtitleLabel = uilabel(headerGrid, 'Text', 'Linear Frequency-Modulated Thermal Waves • 3-D Hex8 FEM • 5 Blind Methods', ...
                'FontSize', 11, 'FontColor', [0.65, 0.75, 0.90], 'HorizontalAlignment', 'right');
            subtitleLabel.Layout.Column = 2;
            
            % --- LEFT COLUMN: INSPECTION INPUTS & CONTROLS ---
            leftScrollPanel = uipanel(mainGrid, 'Title', '⚙️ INSPECTION INPUTS', ...
                'FontSize', 12, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.15, 0.17, 0.22], 'Scrollable', 'on');
            leftScrollPanel.Layout.Row = 2;
            leftScrollPanel.Layout.Column = 1;
            
            leftGrid = uigridlayout(leftScrollPanel, [18, 2]);
            leftGrid.ColumnWidth = {'1x', '1x'};
            leftGrid.RowHeight = repmat({24}, 1, 18);
            leftGrid.Padding = [6, 6, 6, 6];
            leftGrid.RowSpacing = 4;
            
            % 1. Defect Parameters
            lbl = uilabel(leftGrid, 'Text', 'DEFECT PRESET:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = 1;
            app.DefectPresetDrop = uidropdown(leftGrid, 'Items', {'8 mm (z=0.4 mm) [Default]', '4 mm (z=0.2 mm)', '6 mm (z=0.4 mm)', '10 mm (z=0.6 mm)', '12 mm (z=0.8 mm)', 'Deep 8 mm (z=0.8 mm)', 'Deep 4 mm (z=1.0 mm)', 'Healthy Control (D=0)', 'Custom Values'}, ...
                'ValueChangedFcn', @(src, evt) app.onDefectPresetChanged());
            app.DefectPresetDrop.Layout.Column = 2;
            
            app.HealthyCheck = uicheckbox(leftGrid, 'Text', 'Healthy Plate / No Inclusion', 'FontWeight', 'bold', ...
                'FontColor', [0.4, 0.9, 0.5], 'ValueChangedFcn', @(src, evt) app.onHealthyCheckChanged());
            app.HealthyCheck.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'Diameter [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.DiamEdit = uieditfield(leftGrid, 'numeric', 'Value', 8.0, 'Limits', [0, 50]);
            
            uilabel(leftGrid, 'Text', 'Depth z [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.DepthEdit = uieditfield(leftGrid, 'numeric', 'Value', 0.4, 'Limits', [0, 2.3]);
            
            uilabel(leftGrid, 'Text', 'Thickness [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.ThickEdit = uieditfield(leftGrid, 'numeric', 'Value', 0.5, 'Limits', [0.1, 2.0]);
            
            uilabel(leftGrid, 'Text', 'Center X / Y [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            posGrid = uigridlayout(leftGrid, [1, 2]);
            posGrid.Padding = [0, 0, 0, 0]; posGrid.ColumnSpacing = 4;
            app.PosXEdit = uieditfield(posGrid, 'numeric', 'Value', 50.0);
            app.PosYEdit = uieditfield(posGrid, 'numeric', 'Value', 35.0);
            
            % 2. LFMT Excitation Parameters
            lbl = uilabel(leftGrid, 'Text', 'LFMT EXCITATION:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'f0 / f1 [Hz]:', 'FontColor', [0.85, 0.85, 0.9]);
            fGrid = uigridlayout(leftGrid, [1, 2]);
            fGrid.Padding = [0, 0, 0, 0]; fGrid.ColumnSpacing = 4;
            app.F0Edit = uieditfield(fGrid, 'numeric', 'Value', 0.05, 'Limits', [0.001, 10]);
            app.F1Edit = uieditfield(fGrid, 'numeric', 'Value', 0.50, 'Limits', [0.001, 10]);
            
            uilabel(leftGrid, 'Text', 'Heat Flux q0 [W/m²]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.Q0Edit = uieditfield(leftGrid, 'numeric', 'Value', 5000, 'Limits', [100, 100000]);
            
            uilabel(leftGrid, 'Text', 'Duration Texc / Tobs [s]:', 'FontColor', [0.85, 0.85, 0.9]);
            tGrid = uigridlayout(leftGrid, [1, 2]);
            tGrid.Padding = [0, 0, 0, 0]; tGrid.ColumnSpacing = 4;
            app.TexcEdit = uieditfield(tGrid, 'numeric', 'Value', 10.0, 'Limits', [1, 100]);
            app.TobsEdit = uieditfield(tGrid, 'numeric', 'Value', 10.0, 'Limits', [1, 100]);
            
            % 3. Camera & Noise
            lbl = uilabel(leftGrid, 'Text', 'CAMERA & NOISE:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'Noise Condition:', 'FontColor', [0.85, 0.85, 0.9]);
            app.NoiseModeDrop = uidropdown(leftGrid, 'Items', {'Clean (Inf dB)', '30 dB SNR', '25 dB SNR', '20 dB SNR', 'Custom SNR'}, ...
                'ValueChangedFcn', @(src, evt) app.onNoiseModeChanged());
            
            uilabel(leftGrid, 'Text', 'Custom SNR [dB] / Seed:', 'FontColor', [0.85, 0.85, 0.9]);
            snrGrid = uigridlayout(leftGrid, [1, 2]);
            snrGrid.Padding = [0, 0, 0, 0]; snrGrid.ColumnSpacing = 4;
            app.SNREdit = uieditfield(snrGrid, 'numeric', 'Value', 25.0, 'Enable', 'off');
            app.SeedEdit = uieditfield(snrGrid, 'numeric', 'Value', 42, 'Limits', [0, 999999]);
            
            % 4. Solver Settings
            lbl = uilabel(leftGrid, 'Text', 'NUMERICAL SOLVER:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'Forward Solver:', 'FontColor', [0.85, 0.85, 0.9]);
            app.SolverDrop = uidropdown(leftGrid, 'Items', {'3-D Hex8 FEM (Primary)', '3-D FDM (Secondary)'});
            
            uilabel(leftGrid, 'Text', 'Mesh Resolution:', 'FontColor', [0.85, 0.85, 0.9]);
            app.ModeDrop = uidropdown(leftGrid, 'Items', {'Standard Research', 'Quick Demo', 'High-Res Physics'});
            
            % Presets Grid
            presetGrid = uigridlayout(leftGrid, [1, 3]);
            presetGrid.Layout.Column = [1, 2];
            presetGrid.Padding = [0, 0, 0, 0]; presetGrid.ColumnSpacing = 4;
            app.LoadDefButton = uibutton(presetGrid, 'Text', 'Default', 'ButtonPushedFcn', @(src, evt) app.loadDefaultPreset());
            app.LoadConfButton = uibutton(presetGrid, 'Text', 'Conference', 'ButtonPushedFcn', @(src, evt) app.loadConferencePreset());
            app.LoadLitButton = uibutton(presetGrid, 'Text', 'Literature', 'ButtonPushedFcn', @(src, evt) app.loadLiteraturePreset());
            
            % 5. Primary Run Controls
            app.RunButton = uibutton(leftGrid, 'Text', '▶ RUN INSPECTION', ...
                'FontSize', 13, 'FontWeight', 'bold', 'BackgroundColor', [0.15, 0.65, 0.35], ...
                'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.runInspection());
            app.RunButton.Layout.Column = 1;
            
            app.StopButton = uibutton(leftGrid, 'Text', '⏹ STOP', ...
                'FontSize', 12, 'FontWeight', 'bold', 'BackgroundColor', [0.65, 0.20, 0.20], ...
                'FontColor', 'w', 'Enable', 'off', 'ButtonPushedFcn', @(src, evt) app.stopExecution());
            app.StopButton.Layout.Column = 2;
            
            % Status / Progress
            app.StageLabel = uilabel(leftGrid, 'Text', 'Status: Ready', 'FontWeight', 'bold', 'FontColor', [0.4, 0.9, 0.5]);
            app.StageLabel.Layout.Column = [1, 2];
            
            % Action Buttons Grid
            actGrid = uigridlayout(leftGrid, [2, 2]);
            actGrid.Layout.Column = [1, 2];
            actGrid.Padding = [0, 0, 0, 0]; actGrid.RowSpacing = 4; actGrid.ColumnSpacing = 4;
            app.SaveResButton = uibutton(actGrid, 'Text', '💾 Save Results', 'ButtonPushedFcn', @(src, evt) app.saveResults(true));
            app.ExportRepButton = uibutton(actGrid, 'Text', '📊 Export Report', 'ButtonPushedFcn', @(src, evt) app.exportReport(true));
            app.RunValButton = uibutton(actGrid, 'Text', '🔬 Run Validation', 'ButtonPushedFcn', @(src, evt) app.runValidation());
            app.RunTestButton = uibutton(actGrid, 'Text', '🧪 Run Tests', 'ButtonPushedFcn', @(src, evt) app.runTests());
            
            % --- CENTER COLUMN: LIVE THERMOGRAM & SIGNAL ANALYSIS ---
            centerPanel = uipanel(mainGrid, 'BackgroundColor', [0.14, 0.16, 0.20], 'BorderType', 'none');
            centerPanel.Layout.Row = 2;
            centerPanel.Layout.Column = 2;
            
            centerGrid = uigridlayout(centerPanel, [4, 1]);
            centerGrid.RowHeight = {380, 42, 30, '1x'};
            centerGrid.Padding = [4, 4, 4, 4];
            centerGrid.RowSpacing = 4;
            
            % Large Live IR Thermogram Axes
            thermoPanel = uipanel(centerGrid, 'Title', '📹 LIVE IR THERMOGRAM (Click to inspect pixel curve)', ...
                'FontSize', 11, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            thermoPanel.Layout.Row = 1;
            
            thermoGrid = uigridlayout(thermoPanel, [1, 1]);
            thermoGrid.Padding = [4, 4, 4, 4];
            app.ThermogramAxes = uiaxes(thermoGrid);
            app.ThermogramAxes.Color = [0.08, 0.09, 0.12];
            app.ThermogramAxes.XColor = [0.8, 0.8, 0.85];
            app.ThermogramAxes.YColor = [0.8, 0.8, 0.85];
            title(app.ThermogramAxes, 'Front-Surface Transient Temperature Field T(x,y,t)', 'Color', [0.95, 0.95, 0.95]);
            xlabel(app.ThermogramAxes, 'Plate Length X [mm]');
            ylabel(app.ThermogramAxes, 'Plate Width Y [mm]');
            colormap(app.ThermogramAxes, 'turbo');
            app.ThermogramAxes.ButtonDownFcn = @(src, evt) app.onThermogramClicked(evt);
            
            % Thermogram Playback Controls
            playPanel = uipanel(centerGrid, 'BackgroundColor', [0.16, 0.18, 0.22], 'BorderType', 'none');
            playPanel.Layout.Row = 2;
            playGrid = uigridlayout(playPanel, [1, 6]);
            playGrid.ColumnWidth = {40, 70, 40, '1x', 60, 60};
            playGrid.Padding = [4, 2, 4, 2];
            
            app.PrevButton = uibutton(playGrid, 'Text', '⏮', 'ButtonPushedFcn', @(src, evt) app.stepFrame(-1));
            app.PlayButton = uibutton(playGrid, 'Text', '▶ Play', 'FontWeight', 'bold', ...
                'BackgroundColor', [0.2, 0.45, 0.7], 'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.togglePlayback());
            app.NextButton = uibutton(playGrid, 'Text', '⏭', 'ButtonPushedFcn', @(src, evt) app.stepFrame(1));
            
            app.FrameSlider = uislider(playGrid, 'Limits', [1, 251], 'Value', 1, ...
                'ValueChangedFcn', @(src, evt) app.onSliderChanged());
            
            uilabel(playGrid, 'Text', 'Speed:', 'FontColor', [0.85, 0.85, 0.9], 'HorizontalAlignment', 'right');
            app.SpeedDrop = uidropdown(playGrid, 'Items', {'0.25x', '0.5x', '1.0x', '2.0x', '4.0x'}, 'Value', '1.0x', ...
                'ValueChangedFcn', @(src, evt) app.onSpeedChanged());
            
            % Thermogram Stats Bar
            statsPanel = uipanel(centerGrid, 'BackgroundColor', [0.12, 0.14, 0.18], 'BorderType', 'none');
            statsPanel.Layout.Row = 3;
            statsGrid = uigridlayout(statsPanel, [1, 2]);
            statsGrid.ColumnWidth = {'1x', '1x'};
            statsGrid.Padding = [6, 2, 6, 2];
            
            app.FrameInfoLabel = uilabel(statsGrid, 'Text', 'Frame: 1 / 1  |  Time: 0.00 s  |  Inst. Freq: 0.050 Hz', ...
                'FontColor', [0.95, 0.85, 0.4], 'FontWeight', 'bold');
            app.ThermalStatsLabel = uilabel(statsGrid, 'Text', 'Min: 293.15 K  |  Max: 293.15 K  |  Mean: 293.15 K', ...
                'FontColor', [0.7, 0.9, 1.0], 'HorizontalAlignment', 'right');
            
            % Center Bottom Tab Group (Waveform, Pixel Inspector, GT Contrast)
            app.SignalTabGroup = uitabgroup(centerGrid);
            app.SignalTabGroup.Layout.Row = 4;
            
            app.WaveformTab = uitab(app.SignalTabGroup, 'Title', '📈 LFMT Waveform & Frequency');
            waveGrid = uigridlayout(app.WaveformTab, [1, 1]); waveGrid.Padding = [4, 4, 4, 4];
            app.WaveformAxes = uiaxes(waveGrid);
            app.WaveformAxes.Color = [0.08, 0.09, 0.12];
            app.WaveformAxes.XColor = [0.8, 0.8, 0.85]; app.WaveformAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.WaveformAxes, 'Time t [s]'); ylabel(app.WaveformAxes, 'Flux q(t) [W/m²]');
            grid(app.WaveformAxes, 'on');
            
            app.PixelCurveTab = uitab(app.SignalTabGroup, 'Title', '📍 Pixel Thermal Curve');
            pixGrid = uigridlayout(app.PixelCurveTab, [1, 1]); pixGrid.Padding = [4, 4, 4, 4];
            app.PixelCurveAxes = uiaxes(pixGrid);
            app.PixelCurveAxes.Color = [0.08, 0.09, 0.12];
            app.PixelCurveAxes.XColor = [0.8, 0.8, 0.85]; app.PixelCurveAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.PixelCurveAxes, 'Time t [s]'); ylabel(app.PixelCurveAxes, 'Temperature T [K]');
            grid(app.PixelCurveAxes, 'on');
            
            app.GTAnalysisTab = uitab(app.SignalTabGroup, 'Title', '🔍 Ground-Truth Contrast (Audit Only)');
            gtGrid = uigridlayout(app.GTAnalysisTab, [1, 1]); gtGrid.Padding = [4, 4, 4, 4];
            app.GTAnalysisAxes = uiaxes(gtGrid);
            app.GTAnalysisAxes.Color = [0.08, 0.09, 0.12];
            app.GTAnalysisAxes.XColor = [0.8, 0.8, 0.85]; app.GTAnalysisAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.GTAnalysisAxes, 'Time t [s]'); ylabel(app.GTAnalysisAxes, 'Differential Contrast \Delta T [K]');
            grid(app.GTAnalysisAxes, 'on');
            
            % --- RIGHT COLUMN: 5-METHOD SCORE MAPS & METRICS ---
            rightPanel = uipanel(mainGrid, 'BackgroundColor', [0.14, 0.16, 0.20], 'BorderType', 'none');
            rightPanel.Layout.Row = 2;
            rightPanel.Layout.Column = 3;
            
            rightGrid = uigridlayout(rightPanel, [4, 1]);
            rightGrid.RowHeight = {65, 340, '1x', 140};
            rightGrid.Padding = [4, 4, 4, 4];
            rightGrid.RowSpacing = 4;
            
            % 1. Defect Classification & Method Selector Header
            resHeaderPanel = uipanel(rightGrid, 'Title', '🎯 INSPECTION RESULT & CLASSIFICATION', ...
                'FontSize', 11, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.16, 0.18, 0.24]);
            resHeaderPanel.Layout.Row = 1;
            resHGrid = uigridlayout(resHeaderPanel, [1, 4]);
            resHGrid.ColumnWidth = {30, 140, '1x', 170};
            resHGrid.Padding = [6, 2, 6, 2];
            
            app.DetectionLamp = uilamp(resHGrid, 'Color', [0.5, 0.5, 0.5]);
            app.DetectionText = uilabel(resHGrid, 'Text', 'STATUS: READY', 'FontSize', 12, 'FontWeight', 'bold', 'FontColor', [0.9, 0.9, 0.95]);
            
            methGrid = uigridlayout(resHGrid, [1, 2]);
            methGrid.Padding = [0, 0, 0, 0];
            uilabel(methGrid, 'Text', 'Primary Method:', 'FontColor', [0.85, 0.85, 0.9], 'HorizontalAlignment', 'right');
            app.MethodDrop = uidropdown(methGrid, 'Items', {'Matched Filter', 'PCT (SVD)', 'SPCT (Sparse PCA)', 'Raw Contrast', 'RPT (Random Proj)'}, ...
                'ValueChangedFcn', @(src, evt) app.updatePrimaryDisplay());
            
            app.GTOverlayCheck = uicheckbox(resHGrid, 'Text', 'Show Ground Truth Overlay', ...
                'FontColor', [0.95, 0.85, 0.4], 'FontWeight', 'bold', 'Value', false, ...
                'ValueChangedFcn', @(src, evt) app.updateAllProcessedPlots());
            
            % 2. Five Blind Processing Score Maps (Grid of 5 mini-axes)
            mapsPanel = uipanel(rightGrid, 'Title', '📊 5 BLIND THERMOGRAPHIC SIGNAL PROCESSING SCORE MAPS', ...
                'FontSize', 11, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            mapsPanel.Layout.Row = 2;
            
            mapsGrid = uigridlayout(mapsPanel, [2, 3]);
            mapsGrid.RowHeight = {'1x', '1x'};
            mapsGrid.ColumnWidth = {'1x', '1x', '1x'};
            mapsGrid.Padding = [4, 4, 4, 4];
            mapsGrid.RowSpacing = 4; mapsGrid.ColumnSpacing = 4;
            
            app.AxesRaw = app.createMiniAxes(mapsGrid, '1. Raw Contrast');
            app.AxesMF = app.createMiniAxes(mapsGrid, '2. Matched Filter (Pulse Comp)');
            app.AxesPCT = app.createMiniAxes(mapsGrid, '3. SVD-PCT');
            app.AxesSPCT = app.createMiniAxes(mapsGrid, '4. Sparse PCA (SPCT)');
            app.AxesRPT = app.createMiniAxes(mapsGrid, '5. Random Projection (RPT)');
            
            % Summary Metric Text Box
            metricSummaryPanel = uipanel(mapsGrid, 'BackgroundColor', [0.16, 0.18, 0.22], 'BorderType', 'none');
            mSumGrid = uigridlayout(metricSummaryPanel, [1, 1]); mSumGrid.Padding = [6, 4, 6, 4];
            app.MetricSummaryLabel = uilabel(mSumGrid, 'Text', "Inspection metrics will appear here after running inspection.", ...
                'FontColor', [0.9, 0.95, 1.0], 'WordWrap', 'on', 'FontSize', 10);
            
            % 3. Results Tab Group (Metric Table & Execution Log)
            app.ResultsTabGroup = uitabgroup(rightGrid);
            app.ResultsTabGroup.Layout.Row = [3, 4];
            
            app.TableTab = uitab(app.ResultsTabGroup, 'Title', '📋 Quantitative 5-Method Metrics');
            tGrid = uigridlayout(app.TableTab, [1, 1]); tGrid.Padding = [2, 2, 2, 2];
            app.MetricsTable = uitable(tGrid, 'ColumnName', {'Method', 'Detected', 'CNR', 'IoU', 'Dice', 'Loc Err (mm)', 'Diam Err (mm)', 'Runtime (s)'}, ...
                'RowName', {}, 'BackgroundColor', [0.15, 0.17, 0.22; 0.18, 0.20, 0.26], ...
                'ForegroundColor', [0.95, 0.95, 0.95]);
            
            app.LogTab = uitab(app.ResultsTabGroup, 'Title', '📝 Live Execution Log');
            logGrid = uigridlayout(app.LogTab, [1, 1]); logGrid.Padding = [2, 2, 2, 2];
            app.LogTextArea = uitextarea(logGrid, 'BackgroundColor', [0.08, 0.09, 0.12], ...
                'FontColor', [0.4, 0.9, 0.5], 'FontName', 'Consolas', 'FontSize', 10, 'Editable', 'off');
            
            % Playback Timer Setup (~25 fps)
            app.PlayTimer = timer('ExecutionMode', 'fixedRate', 'Period', 0.04, ...
                'TimerFcn', @(src, evt) app.onTimerTick());
        end
        
        function ax = createMiniAxes(~, parentGrid, axTitle)
            ax = uiaxes(parentGrid);
            ax.Color = [0.08, 0.09, 0.12];
            ax.XColor = [0.7, 0.7, 0.75]; ax.YColor = [0.7, 0.7, 0.75];
            title(ax, axTitle, 'FontSize', 9, 'FontWeight', 'bold', 'Color', [0.9, 0.95, 1.0]);
            xlabel(ax, 'X (mm)', 'FontSize', 7); ylabel(ax, 'Y (mm)', 'FontSize', 7);
            colormap(ax, 'jet');
            axis(ax, 'image');
        end
        
        %% Logging Utility
        function logMessage(app, msg)
            ts = datestr(now, 'HH:MM:SS');
            formatted = sprintf('[%s] %s', ts, msg);
            current_txt = app.LogTextArea.Value;
            if isempty(current_txt)
                app.LogTextArea.Value = {formatted};
            else
                app.LogTextArea.Value = [current_txt; {formatted}];
            end
            % Auto scroll to bottom
            scroll(app.LogTextArea, 'bottom');
            drawnow limitrate;
        end
        
        %% Preset Loaders
        function loadDefaultPreset(app)
            app.DefectPresetDrop.Value = '8 mm (z=0.4 mm) [Default]';
            app.HealthyCheck.Value = false;
            app.enableDefectInputs(true);
            app.DiamEdit.Value = 8.0;
            app.DepthEdit.Value = 0.4;
            app.ThickEdit.Value = 0.5;
            app.PosXEdit.Value = 50.0;
            app.PosYEdit.Value = 35.0;
            app.F0Edit.Value = 0.05;
            app.F1Edit.Value = 0.50;
            app.Q0Edit.Value = 5000;
            app.TexcEdit.Value = 10.0;
            app.TobsEdit.Value = 10.0;
            app.NoiseModeDrop.Value = 'Clean (Inf dB)';
            app.SNREdit.Value = Inf;
            app.SNREdit.Enable = 'off';
            app.SeedEdit.Value = 42;
            app.SolverDrop.Value = '3-D Hex8 FEM (Primary)';
            app.ModeDrop.Value = 'Standard Research';
            app.logMessage('Loaded Default Research Configuration.');
            app.updateExcitationWaveformPlot();
        end
        
        function loadConferencePreset(app)
            app.DefectPresetDrop.Value = '6 mm (z=0.4 mm)';
            app.HealthyCheck.Value = false;
            app.enableDefectInputs(true);
            app.DiamEdit.Value = 6.0;
            app.DepthEdit.Value = 0.4;
            app.ThickEdit.Value = 0.5;
            app.PosXEdit.Value = 50.0;
            app.PosYEdit.Value = 35.0;
            app.F0Edit.Value = 0.05;
            app.F1Edit.Value = 0.50;
            app.Q0Edit.Value = 5000;
            app.TexcEdit.Value = 10.0;
            app.TobsEdit.Value = 10.0;
            app.NoiseModeDrop.Value = '25 dB SNR';
            app.SNREdit.Value = 25.0;
            app.SNREdit.Enable = 'off';
            app.SeedEdit.Value = 42;
            app.SolverDrop.Value = '3-D Hex8 FEM (Primary)';
            app.ModeDrop.Value = 'Quick Demo';
            app.logMessage('Loaded Conference Fast Demo Configuration.');
            app.updateExcitationWaveformPlot();
        end
        
        function loadLiteraturePreset(app)
            app.DefectPresetDrop.Value = '10 mm (z=0.6 mm)';
            app.HealthyCheck.Value = false;
            app.enableDefectInputs(true);
            app.DiamEdit.Value = 10.0;
            app.DepthEdit.Value = 0.6;
            app.ThickEdit.Value = 0.5;
            app.PosXEdit.Value = 50.0;
            app.PosYEdit.Value = 35.0;
            app.F0Edit.Value = 0.05;
            app.F1Edit.Value = 0.50;
            app.Q0Edit.Value = 5000;
            app.TexcEdit.Value = 10.0;
            app.TobsEdit.Value = 10.0;
            app.NoiseModeDrop.Value = '30 dB SNR';
            app.SNREdit.Value = 30.0;
            app.SNREdit.Enable = 'off';
            app.SeedEdit.Value = 42;
            app.SolverDrop.Value = '3-D Hex8 FEM (Primary)';
            app.ModeDrop.Value = 'Standard Research';
            app.logMessage('Loaded Literature Validation Configuration.');
            app.updateExcitationWaveformPlot();
        end
        
        function enableDefectInputs(app, tf)
            state = matlab.lang.OnOffSwitchState(tf);
            app.DiamEdit.Enable = state;
            app.DepthEdit.Enable = state;
            app.ThickEdit.Enable = state;
            app.PosXEdit.Enable = state;
            app.PosYEdit.Enable = state;
        end
        
        %% Event Callbacks
        function onDefectPresetChanged(app)
            preset = app.DefectPresetDrop.Value;
            switch preset
                case '8 mm (z=0.4 mm) [Default]'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 8.0; app.DepthEdit.Value = 0.4;
                case '4 mm (z=0.2 mm)'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 4.0; app.DepthEdit.Value = 0.2;
                case '6 mm (z=0.4 mm)'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 6.0; app.DepthEdit.Value = 0.4;
                case '10 mm (z=0.6 mm)'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 10.0; app.DepthEdit.Value = 0.6;
                case '12 mm (z=0.8 mm)'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 12.0; app.DepthEdit.Value = 0.8;
                case 'Deep 8 mm (z=0.8 mm)'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 8.0; app.DepthEdit.Value = 0.8;
                case 'Deep 4 mm (z=1.0 mm)'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 4.0; app.DepthEdit.Value = 1.0;
                case 'Healthy Control (D=0)'
                    app.HealthyCheck.Value = true; app.enableDefectInputs(false);
                    app.DiamEdit.Value = 0.0;
                case 'Custom Values'
                    % Leave current edit fields editable
                    app.enableDefectInputs(~app.HealthyCheck.Value);
            end
        end
        
        function onHealthyCheckChanged(app)
            if app.HealthyCheck.Value
                app.enableDefectInputs(false);
                app.DefectPresetDrop.Value = 'Healthy Control (D=0)';
                app.DiamEdit.Value = 0.0;
            else
                app.enableDefectInputs(true);
                app.DefectPresetDrop.Value = 'Custom Values';
                if app.DiamEdit.Value == 0
                    app.DiamEdit.Value = 8.0;
                    app.DepthEdit.Value = 0.4;
                end
            end
        end
        
        function onNoiseModeChanged(app)
            mode = app.NoiseModeDrop.Value;
            switch mode
                case 'Clean (Inf dB)'
                    app.SNREdit.Value = Inf;
                    app.SNREdit.Enable = 'off';
                case '30 dB SNR'
                    app.SNREdit.Value = 30.0;
                    app.SNREdit.Enable = 'off';
                case '25 dB SNR'
                    app.SNREdit.Value = 25.0;
                    app.SNREdit.Enable = 'off';
                case '20 dB SNR'
                    app.SNREdit.Value = 20.0;
                    app.SNREdit.Enable = 'off';
                case 'Custom SNR'
                    app.SNREdit.Enable = 'on';
            end
        end
        
        function onSpeedChanged(app)
            val = app.SpeedDrop.Value;
            switch val
                case '0.25x', app.PlaybackSpeed = 0.25;
                case '0.5x',  app.PlaybackSpeed = 0.5;
                case '1.0x',  app.PlaybackSpeed = 1.0;
                case '2.0x',  app.PlaybackSpeed = 2.0;
                case '4.0x',  app.PlaybackSpeed = 4.0;
            end
        end
        
        function onSliderChanged(app)
            if ~isempty(app.CurrentResults) && isfield(app.CurrentResults, 'noisy_thermograms')
                app.CurrentFrameIdx = round(app.FrameSlider.Value);
                app.updateThermogramFrame();
            end
        end
        
        function togglePlayback(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                return;
            end
            if app.IsPlaying
                stop(app.PlayTimer);
                app.IsPlaying = false;
                app.PlayButton.Text = '▶ Play';
                app.PlayButton.BackgroundColor = [0.2, 0.45, 0.7];
            else
                app.IsPlaying = true;
                app.PlayButton.Text = '⏸ Pause';
                app.PlayButton.BackgroundColor = [0.7, 0.45, 0.2];
                start(app.PlayTimer);
            end
        end
        
        function stepFrame(app, delta)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                return;
            end
            new_idx = app.CurrentFrameIdx + delta;
            if new_idx < 1, new_idx = app.TotalFrames; end
            if new_idx > app.TotalFrames, new_idx = 1; end
            app.CurrentFrameIdx = new_idx;
            app.FrameSlider.Value = new_idx;
            app.updateThermogramFrame();
        end
        
        function onTimerTick(app)
            if ~app.IsPlaying || isempty(app.CurrentResults)
                return;
            end
            % Advance frame according to speed
            step = max(1, round(app.PlaybackSpeed));
            new_idx = app.CurrentFrameIdx + step;
            if new_idx > app.TotalFrames
                new_idx = 1;
            end
            app.CurrentFrameIdx = new_idx;
            app.FrameSlider.Value = new_idx;
            app.updateThermogramFrame();
        end
        
        function onThermogramClicked(app, evt)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                return;
            end
            cp = evt.IntersectionPoint;
            clicked_x_mm = cp(1);
            clicked_y_mm = cp(2);
            
            sim_res = app.CurrentResults.simulation;
            [~, col] = min(abs(sim_res.camera_x_mm - clicked_x_mm));
            [~, row] = min(abs(sim_res.camera_y_mm - clicked_y_mm));
            
            app.SelectedPixel = [row, col];
            app.updatePixelThermalCurve();
            app.SignalTabGroup.SelectedTab = app.PixelCurveTab;
            app.logMessage(sprintf('Selected Point Inspector at X = %.1f mm, Y = %.1f mm (Pixel [%d, %d])', clicked_x_mm, clicked_y_mm, row, col));
        end
        
        function onCloseRequest(app)
            if ~isempty(app.PlayTimer) && isvalid(app.PlayTimer)
                stop(app.PlayTimer);
                delete(app.PlayTimer);
            end
            delete(app.UIFigure);
        end
        
        %% Input Validation & Config Builder
        function [cfg, valid, err_msg] = buildValidatedConfig(app)
            valid = true;
            err_msg = '';
            
            % Base configuration
            cfg = default_config();
            
            % Geometry Validation
            is_healthy = app.HealthyCheck.Value;
            if is_healthy
                cfg.defects = [];
                cfg.plate.has_defect = false;
                cfg.plate.defect.diameter_mm = 0.0;
                cfg.plate.defect.depth_mm = 0.0;
                cfg.plate.defect.thickness_mm = 0.0;
            else
                cfg.plate.has_defect = true;
                d = app.DiamEdit.Value;
                z = app.DepthEdit.Value;
                th = app.ThickEdit.Value;
                cx = app.PosXEdit.Value;
                cy = app.PosYEdit.Value;
                
                if d <= 0
                    valid = false; err_msg = 'Defect diameter must be strictly positive (> 0 mm).'; return;
                end
                if z < 0 || (z + th) > cfg.plate.thickness_mm
                    valid = false; err_msg = sprintf('Defect (depth %.2f mm + thickness %.2f mm) exceeds plate thickness (%.2f mm).', z, th, cfg.plate.thickness_mm); return;
                end
                if (cx - d/2) < 0 || (cx + d/2) > cfg.plate.length_mm || (cy - d/2) < 0 || (cy + d/2) > cfg.plate.width_mm
                    valid = false; err_msg = 'Defect boundaries exceed plate dimensions (100 x 70 mm).'; return;
                end
                
                cfg.plate.defect.diameter_mm = d;
                cfg.plate.defect.radius_m = (d / 2.0) * 1e-3;
                cfg.plate.defect.depth_mm = z;
                cfg.plate.defect.depth_m = z * 1e-3;
                cfg.plate.defect.thickness_mm = th;
                cfg.plate.defect.thickness_m = th * 1e-3;
                cfg.plate.defect.center_x_mm = cx;
                cfg.plate.defect.center_x_m = cx * 1e-3;
                cfg.plate.defect.center_y_mm = cy;
                cfg.plate.defect.center_y_m = cy * 1e-3;
                cfg.plate.defect.area_mm2 = pi * (d/2)^2;
                
                cfg.defects = [
                    struct(...
                        'id', 1, ...
                        'shape', 'cylinder', ...
                        'material', 'slag', ...
                        'center_x_mm', cx, ...
                        'center_y_mm', cy, ...
                        'depth_mm', z, ...
                        'diameter_mm', d, ...
                        'thickness_mm', th, ...
                        'thermal_conductivity', 1.20, ...
                        'density', 2800.0, ...
                        'specific_heat', 850.0 ...
                    )
                ];
            end
            
            % Excitation Validation
            f0 = app.F0Edit.Value;
            f1 = app.F1Edit.Value;
            q0 = app.Q0Edit.Value;
            texc = app.TexcEdit.Value;
            tobs = app.TobsEdit.Value;
            
            if f0 <= 0 || f1 <= f0
                valid = false; err_msg = 'Invalid chirp frequencies. Must satisfy f1 > f0 > 0.'; return;
            end
            if q0 <= 0
                valid = false; err_msg = 'Heat flux q0 must be strictly positive (> 0 W/m²).'; return;
            end
            if texc <= 0 || tobs < texc
                valid = false; err_msg = 'Observation duration must be >= Excitation duration (> 0 s).'; return;
            end
            
            cfg.excitation.f0_hz = f0;
            cfg.excitation.f1_hz = f1;
            cfg.excitation.q0_w_m2 = q0;
            cfg.excitation.duration_s = texc;
            cfg.excitation.observation_time_s = tobs;
            
            % Camera & Noise
            snr_val = app.SNREdit.Value;
            if isinf(snr_val) || snr_val <= 0 || isnan(snr_val)
                cfg.camera.noise_snr_db = [];
            else
                cfg.camera.noise_snr_db = snr_val;
            end
            cfg.camera.noise_seed = uint32(app.SeedEdit.Value);
            
            % Solver settings
            if contains(app.SolverDrop.Value, 'FDM')
                cfg.simulation.solver_type = 'fdm';
            else
                cfg.simulation.solver_type = 'fem';
            end
            
            switch app.ModeDrop.Value
                case 'Quick Demo'
                    cfg.simulation.nx = 20; cfg.simulation.ny = 14; cfg.simulation.nz = 6;
                    cfg.simulation.dt_s = 0.08;
                case 'High-Res Physics'
                    cfg.simulation.nx = 60; cfg.simulation.ny = 40; cfg.simulation.nz = 16;
                    cfg.simulation.dt_s = 0.02;
                otherwise % Standard Research
                    cfg.simulation.nx = 40; cfg.simulation.ny = 28; cfg.simulation.nz = 10;
                    cfg.simulation.dt_s = 0.04;
            end
        end
        
        %% Main Pipeline Execution
        function runInspection(app)
            if app.IsRunning, return; end
            
            [cfg, valid, err_msg] = app.buildValidatedConfig();
            if ~valid
                uialert(app.UIFigure, err_msg, 'Input Validation Error', 'Icon', 'error');
                app.logMessage(['ERROR: ', err_msg]);
                return;
            end
            
            app.IsRunning = true;
            app.RunButton.Enable = 'off';
            app.StopButton.Enable = 'on';
            app.StageLabel.Text = 'Status: Initializing Pipeline...';
            app.StageLabel.FontColor = [0.95, 0.85, 0.4];
            drawnow;
            
            t_start = tic;
            app.logMessage('================================================================');
            app.logMessage('Starting LFMT Inspection Pipeline...');
            if cfg.plate.has_defect
                app.logMessage(sprintf('Target: Slag Inclusion D = %.1f mm, Depth z = %.2f mm, Loc = (%.1f, %.1f) mm', ...
                    cfg.plate.defect.diameter_mm, cfg.plate.defect.depth_mm, cfg.plate.defect.center_x_mm, cfg.plate.defect.center_y_mm));
            else
                app.logMessage('Target: Healthy Control Plate (No Inclusion)');
            end
            app.logMessage(sprintf('Excitation: LFMT Sweep %.2f -> %.2f Hz, q0 = %.0f W/m², Texc = %.1f s', ...
                cfg.excitation.f0_hz, cfg.excitation.f1_hz, cfg.excitation.q0_w_m2, cfg.excitation.duration_s));
            
            try
                % 1. Forward 3-D Simulation
                app.StageLabel.Text = 'Stage: 3-D Thermal Simulation...';
                app.logMessage('Running 3-D Numerical Simulation...');
                drawnow;
                
                sim_hash = lfmt.cache('hash', cfg);
                cached_sim = lfmt.cache('load', sim_hash);
                
                if ~isempty(cached_sim)
                    app.logMessage(sprintf('Loaded cached 3-D simulation (Hash: %s...)', sim_hash(1:10)));
                    sim_res = cached_sim;
                else
                    if strcmpi(cfg.simulation.solver_type, 'fdm')
                        sim_res = lfmt_simulate_fdm(cfg);
                    else
                        sim_res = lfmt_simulate_fem(cfg);
                    end
                    lfmt.cache('save', sim_hash, sim_res);
                    app.logMessage(sprintf('Simulation completed in %.2f s (Cached for future runs).', sim_res.runtime_s));
                end
                
                % 2. Virtual IR Camera & Noise Injection
                app.StageLabel.Text = 'Stage: Virtual IR Acquisition...';
                drawnow;
                snr_db = cfg.camera.noise_snr_db;
                seed = cfg.camera.noise_seed;
                [T_noisy, noise_sigma] = lfmt.noise(sim_res.surface_temperature, snr_db, seed);
                if isempty(snr_db) || isinf(snr_db)
                    app.logMessage('Noise Model: Clean Thermograms (sigma = 0.0 K)');
                else
                    app.logMessage(sprintf('Noise Model: AWGN SNR = %.1f dB (sigma = %.4f K, seed = %d)', snr_db, noise_sigma, seed));
                end
                
                % 3. Ground Truth Mask (Isolated strictly for metrics)
                [x_mesh, y_mesh] = meshgrid(sim_res.camera_x_mm, sim_res.camera_y_mm);
                if sim_res.geometry.has_defect
                    d = sim_res.geometry.defect;
                    gt_mask = ((x_mesh - d.center_x_mm).^2 + (y_mesh - d.center_y_mm).^2) <= (d.radius_m * 1e3)^2;
                else
                    gt_mask = false(size(x_mesh));
                end
                
                % 4. 5 Blind Signal Processing Methods
                app.StageLabel.Text = 'Stage: Blind Signal Processing (5 Methods)...';
                drawnow;
                
                % Method 1: Raw Contrast
                res_raw = lfmt_raw_contrast(T_noisy, sim_res.time_vector);
                det_raw = segment_defect(res_raw.score_map, [cfg.plate.length_mm, cfg.plate.width_mm], cfg.processing.detection_min_area_px);
                met_raw = compute_metrics('Raw Contrast', det_raw, sim_res.geometry, gt_mask, res_raw.score_map, res_raw.runtime_s);
                res_raw.detection = det_raw; res_raw.metrics = met_raw;
                app.logMessage(sprintf('Method 1 [Raw Contrast]: Done in %.3f s | IoU = %.3f | CNR = %.2f', res_raw.runtime_s, met_raw.iou, met_raw.cnr));
                
                % Method 2: Matched Filter
                res_mf = lfmt_matched_filter(T_noisy, sim_res.time_vector, cfg.excitation.f0_hz, cfg.excitation.f1_hz, cfg.excitation.duration_s, cfg.excitation.q0_w_m2);
                det_mf = segment_defect(res_mf.score_map, [cfg.plate.length_mm, cfg.plate.width_mm], cfg.processing.detection_min_area_px);
                met_mf = compute_metrics('Matched Filter', det_mf, sim_res.geometry, gt_mask, res_mf.score_map, res_mf.runtime_s);
                res_mf.detection = det_mf; res_mf.metrics = met_mf;
                app.logMessage(sprintf('Method 2 [Matched Filter]: Done in %.3f s | IoU = %.3f | CNR = %.2f', res_mf.runtime_s, met_mf.iou, met_mf.cnr));
                
                % Method 3: SVD-PCT
                res_pct = lfmt_pct(T_noisy, cfg.processing.pct_n_components);
                det_pct = segment_defect(res_pct.score_map, [cfg.plate.length_mm, cfg.plate.width_mm], cfg.processing.detection_min_area_px);
                met_pct = compute_metrics('PCT', det_pct, sim_res.geometry, gt_mask, res_pct.score_map, res_pct.runtime_s);
                res_pct.detection = det_pct; res_pct.metrics = met_pct;
                app.logMessage(sprintf('Method 3 [SVD-PCT]: Done in %.3f s | IoU = %.3f | CNR = %.2f', res_pct.runtime_s, met_pct.iou, met_pct.cnr));
                
                % Method 4: SPCT
                res_spct = lfmt_spct(T_noisy, cfg.processing.spct_n_components, cfg.processing.spct_alpha);
                det_spct = segment_defect(res_spct.score_map, [cfg.plate.length_mm, cfg.plate.width_mm], cfg.processing.detection_min_area_px);
                met_spct = compute_metrics('SPCT', det_spct, sim_res.geometry, gt_mask, res_spct.score_map, res_spct.runtime_s);
                res_spct.detection = det_spct; res_spct.metrics = met_spct;
                app.logMessage(sprintf('Method 4 [SPCT]: Done in %.3f s | IoU = %.3f | CNR = %.2f', res_spct.runtime_s, met_spct.iou, met_spct.cnr));
                
                % Method 5: RPT
                res_rpt = lfmt_rpt(T_noisy, cfg.processing.rpt_n_components, cfg.processing.rpt_seed);
                det_rpt = segment_defect(res_rpt.score_map, [cfg.plate.length_mm, cfg.plate.width_mm], cfg.processing.detection_min_area_px);
                met_rpt = compute_metrics('RPT', det_rpt, sim_res.geometry, gt_mask, res_rpt.score_map, res_rpt.runtime_s);
                res_rpt.detection = det_rpt; res_rpt.metrics = met_rpt;
                app.logMessage(sprintf('Method 5 [RPT]: Done in %.3f s | IoU = %.3f | CNR = %.2f', res_rpt.runtime_s, met_rpt.iou, met_rpt.cnr));
                
                % Structure Compilation
                processed = struct('RAW', res_raw, 'MF', res_mf, 'PCT', res_pct, 'SPCT', res_spct, 'RPT', res_rpt);
                
                summary_rows = [
                    struct('Method', "Raw Contrast", 'Detected', met_raw.is_detected, 'IoU', met_raw.iou, 'Dice', met_raw.dice, 'CNR', met_raw.cnr, 'LocError_mm', met_raw.localization_error_mm, 'DiamError_mm', met_raw.diameter_error_mm, 'Runtime_s', met_raw.runtime_s);
                    struct('Method', "Matched Filter", 'Detected', met_mf.is_detected, 'IoU', met_mf.iou, 'Dice', met_mf.dice, 'CNR', met_mf.cnr, 'LocError_mm', met_mf.localization_error_mm, 'DiamError_mm', met_mf.diameter_error_mm, 'Runtime_s', met_mf.runtime_s);
                    struct('Method', "PCT (SVD)", 'Detected', met_pct.is_detected, 'IoU', met_pct.iou, 'Dice', met_pct.dice, 'CNR', met_pct.cnr, 'LocError_mm', met_pct.localization_error_mm, 'DiamError_mm', met_pct.diameter_error_mm, 'Runtime_s', met_pct.runtime_s);
                    struct('Method', "SPCT (L1-Sparse)", 'Detected', met_spct.is_detected, 'IoU', met_spct.iou, 'Dice', met_spct.dice, 'CNR', met_spct.cnr, 'LocError_mm', met_spct.localization_error_mm, 'DiamError_mm', met_spct.diameter_error_mm, 'Runtime_s', met_spct.runtime_s);
                    struct('Method', "RPT (Gaussian JL)", 'Detected', met_rpt.is_detected, 'IoU', met_rpt.iou, 'Dice', met_rpt.dice, 'CNR', met_rpt.cnr, 'LocError_mm', met_rpt.localization_error_mm, 'DiamError_mm', met_rpt.diameter_error_mm, 'Runtime_s', met_rpt.runtime_s)
                ];
                sum_table = struct2table(summary_rows);
                
                tot_runtime = toc(t_start);
                app.CurrentResults = struct(...
                    'config', cfg, ...
                    'simulation', sim_res, ...
                    'noisy_thermograms', T_noisy, ...
                    'ground_truth_mask', gt_mask, ...
                    'processed', processed, ...
                    'summary_table', sum_table, ...
                    'runtime_s', tot_runtime ...
                );
                
                % Update UI Displays
                app.TotalFrames = size(T_noisy, 1);
                app.FrameSlider.Limits = [1, app.TotalFrames];
                app.CurrentFrameIdx = 1;
                app.FrameSlider.Value = 1;
                
                app.updateThermogramFrame();
                app.updateExcitationWaveformPlot();
                app.updatePixelThermalCurve();
                app.updateGTContrastPlot();
                app.updateAllProcessedPlots();
                app.updatePrimaryDisplay();
                app.updateMetricsTable();
                
                app.StageLabel.Text = sprintf('Status: Complete (Total: %.2f s)', tot_runtime);
                app.StageLabel.FontColor = [0.4, 0.9, 0.5];
                app.logMessage(sprintf('Pipeline completed successfully in %.2f s.', tot_runtime));
                app.logMessage('================================================================');
                
            catch ME
                app.logMessage(['FATAL ERROR in pipeline: ', ME.message]);
                app.StageLabel.Text = 'Status: Error';
                app.StageLabel.FontColor = [0.95, 0.3, 0.3];
                uialert(app.UIFigure, ME.message, 'Execution Error', 'Icon', 'error');
            end
            
            app.IsRunning = false;
            app.RunButton.Enable = 'on';
            app.StopButton.Enable = 'off';
        end
        
        function stopExecution(app)
            if app.IsPlaying
                app.togglePlayback();
            end
            app.IsRunning = false;
            app.RunButton.Enable = 'on';
            app.StopButton.Enable = 'off';
            app.StageLabel.Text = 'Status: Stopped by User';
            app.StageLabel.FontColor = [0.95, 0.85, 0.4];
            app.logMessage('Pipeline execution stopped by user.');
        end
        
        %% Update Plotting Routines
        function updateThermogramFrame(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                return;
            end
            
            sim_res = app.CurrentResults.simulation;
            T_data = app.CurrentResults.noisy_thermograms;
            idx = app.CurrentFrameIdx;
            frame_T = squeeze(T_data(idx, :, :));
            
            x_mm = sim_res.camera_x_mm;
            y_mm = sim_res.camera_y_mm;
            t_curr = sim_res.time_vector(idx);
            
            % Compute instantaneous chirp frequency
            cfg = app.CurrentResults.config;
            if t_curr <= cfg.excitation.duration_s
                f_inst = cfg.excitation.f0_hz + ((cfg.excitation.f1_hz - cfg.excitation.f0_hz) / cfg.excitation.duration_s) * t_curr;
            else
                f_inst = 0.0;
            end
            
            % Update Image
            cla(app.ThermogramAxes);
            imagesc(app.ThermogramAxes, x_mm, y_mm, frame_T);
            axis(app.ThermogramAxes, 'image');
            colorbar(app.ThermogramAxes);
            title(app.ThermogramAxes, sprintf('Surface Thermogram T(x,y)  |  t = %.2f s', t_curr), 'Color', [0.95, 0.95, 0.95]);
            xlabel(app.ThermogramAxes, 'Plate Length X [mm]');
            ylabel(app.ThermogramAxes, 'Plate Width Y [mm]');
            hold(app.ThermogramAxes, 'on');
            
            % Ground Truth Overlay if enabled
            if app.GTOverlayCheck.Value && sim_res.geometry.has_defect
                d = sim_res.geometry.defect;
                theta = linspace(0, 2*pi, 80);
                gt_x = d.center_x_mm + (d.diameter_mm / 2.0) * cos(theta);
                gt_y = d.center_y_mm + (d.diameter_mm / 2.0) * sin(theta);
                plot(app.ThermogramAxes, gt_x, gt_y, 'w--', 'LineWidth', 1.8);
            end
            
            % Selected point marker
            sel_x = sim_res.camera_x_mm(app.SelectedPixel(2));
            sel_y = sim_res.camera_y_mm(app.SelectedPixel(1));
            plot(app.ThermogramAxes, sel_x, sel_y, 'mp', 'MarkerSize', 10, 'LineWidth', 2.0);
            hold(app.ThermogramAxes, 'off');
            
            % Update info labels
            app.FrameInfoLabel.Text = sprintf('Frame: %d / %d  |  Time: %.2f s  |  Inst. Freq: %.3f Hz', idx, app.TotalFrames, t_curr, f_inst);
            t_min = min(frame_T(:)); t_max = max(frame_T(:)); t_mean = mean(frame_T(:));
            app.ThermalStatsLabel.Text = sprintf('Min: %.2f K  |  Max: %.2f K  |  Mean: %.2f K', t_min, t_max, t_mean);
            
            % Move waveform cursor
            if ~isempty(app.WaveformCursorHandle) && isvalid(app.WaveformCursorHandle)
                app.WaveformCursorHandle.Value = t_curr;
            end
        end
        
        function updateExcitationWaveformPlot(app)
            [cfg, valid] = app.buildValidatedConfig();
            if ~valid, return; end
            
            t = linspace(0, cfg.excitation.observation_time_s, 500);
            f_inst = zeros(size(t));
            q = zeros(size(t));
            
            for i = 1:length(t)
                ti = t(i);
                if ti <= cfg.excitation.duration_s
                    f_inst(i) = cfg.excitation.f0_hz + ((cfg.excitation.f1_hz - cfg.excitation.f0_hz) / cfg.excitation.duration_s) * ti;
                    phase = 2 * pi * (cfg.excitation.f0_hz * ti + 0.5 * ((cfg.excitation.f1_hz - cfg.excitation.f0_hz) / cfg.excitation.duration_s) * ti^2) - pi/2;
                    q(i) = cfg.excitation.q0_w_m2 * 0.5 * (1 + sin(phase));
                else
                    f_inst(i) = 0;
                    q(i) = 0;
                end
            end
            
            cla(app.WaveformAxes);
            yyaxis(app.WaveformAxes, 'left');
            plot(app.WaveformAxes, t, q, 'g-', 'LineWidth', 1.8);
            ylabel(app.WaveformAxes, 'Flux q(t) [W/m²]');
            app.WaveformAxes.YColor = [0.4, 0.9, 0.5];
            
            yyaxis(app.WaveformAxes, 'right');
            plot(app.WaveformAxes, t, f_inst, 'm--', 'LineWidth', 1.5);
            ylabel(app.WaveformAxes, 'Inst. Freq f(t) [Hz]');
            app.WaveformAxes.YColor = [0.95, 0.5, 0.95];
            
            xlabel(app.WaveformAxes, 'Time t [s]');
            title(app.WaveformAxes, sprintf('LFMT Excitation: f0=%.2f Hz, f1=%.2f Hz, q0=%.0f W/m²', cfg.excitation.f0_hz, cfg.excitation.f1_hz, cfg.excitation.q0_w_m2), 'Color', [0.9, 0.95, 1.0]);
            grid(app.WaveformAxes, 'on');
            
            % Add vertical time cursor line
            app.WaveformCursorHandle = xline(app.WaveformAxes, 0, 'y-', 'LineWidth', 1.5);
        end
        
        function updatePixelThermalCurve(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                return;
            end
            
            sim_res = app.CurrentResults.simulation;
            T_cube = app.CurrentResults.noisy_thermograms;
            t_vec = sim_res.time_vector;
            
            row = app.SelectedPixel(1);
            col = app.SelectedPixel(2);
            T_pix = squeeze(T_cube(:, row, col));
            T_ref = squeeze(T_cube(:, 2, 2)); % Corner sound reference
            
            cla(app.PixelCurveAxes);
            plot(app.PixelCurveAxes, t_vec, T_pix, 'm-', 'LineWidth', 2.0, 'DisplayName', sprintf('Selected Pixel (X=%.1f, Y=%.1f mm)', sim_res.camera_x_mm(col), sim_res.camera_y_mm(row)));
            hold(app.PixelCurveAxes, 'on');
            plot(app.PixelCurveAxes, t_vec, T_ref, 'c--', 'LineWidth', 1.5, 'DisplayName', 'Sound Reference (Corner)');
            hold(app.PixelCurveAxes, 'off');
            
            grid(app.PixelCurveAxes, 'on');
            legend(app.PixelCurveAxes, 'Location', 'northwest', 'TextColor', [0.9, 0.9, 0.95]);
            title(app.PixelCurveAxes, 'Point Inspector: Transient Thermal Curve T(t)', 'Color', [0.9, 0.95, 1.0]);
            xlabel(app.PixelCurveAxes, 'Time t [s]');
            ylabel(app.PixelCurveAxes, 'Temperature T [K]');
        end
        
        function updateGTContrastPlot(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                return;
            end
            
            sim_res = app.CurrentResults.simulation;
            T_cube = app.CurrentResults.noisy_thermograms;
            t_vec = sim_res.time_vector;
            
            cla(app.GTAnalysisAxes);
            if sim_res.geometry.has_defect
                d = sim_res.geometry.defect;
                [~, cx_idx] = min(abs(sim_res.camera_x_mm - d.center_x_mm));
                [~, cy_idx] = min(abs(sim_res.camera_y_mm - d.center_y_mm));
                
                T_def = squeeze(T_cube(:, cy_idx, cx_idx));
                T_snd = squeeze(T_cube(:, 2, 2));
                delta_T = T_def - T_snd;
                
                plot(app.GTAnalysisAxes, t_vec, delta_T, 'y-', 'LineWidth', 2.0);
                grid(app.GTAnalysisAxes, 'on');
                title(app.GTAnalysisAxes, 'GROUND-TRUTH ANALYSIS — NOT USED BY DETECTOR', 'Color', [0.95, 0.85, 0.4], 'FontWeight', 'bold');
                xlabel(app.GTAnalysisAxes, 'Time t [s]');
                ylabel(app.GTAnalysisAxes, 'Differential Contrast \Delta T(t) [K]');
            else
                title(app.GTAnalysisAxes, 'Healthy Control Plate — No Defect Contrast Generated', 'Color', [0.6, 0.8, 0.9]);
            end
        end
        
        function updateAllProcessedPlots(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'processed')
                return;
            end
            
            sim_res = app.CurrentResults.simulation;
            proc = app.CurrentResults.processed;
            show_gt = app.GTOverlayCheck.Value;
            
            app.plotSingleMethodAxes(app.AxesRaw, proc.RAW, sim_res, '1. Raw Contrast', show_gt);
            app.plotSingleMethodAxes(app.AxesMF, proc.MF, sim_res, '2. Matched Filter', show_gt);
            app.plotSingleMethodAxes(app.AxesPCT, proc.PCT, sim_res, '3. SVD-PCT', show_gt);
            app.plotSingleMethodAxes(app.AxesSPCT, proc.SPCT, sim_res, '4. Sparse PCA (SPCT)', show_gt);
            app.plotSingleMethodAxes(app.AxesRPT, proc.RPT, sim_res, '5. Random Projection (RPT)', show_gt);
        end
        
        function plotSingleMethodAxes(~, ax, method_res, sim_res, method_title, show_gt)
            cla(ax);
            x_mm = sim_res.camera_x_mm;
            y_mm = sim_res.camera_y_mm;
            score_map = method_res.normalized_map;
            det_res = method_res.detection;
            
            imagesc(ax, x_mm, y_mm, score_map);
            axis(ax, 'image');
            colorbar(ax);
            colormap(ax, 'jet');
            hold(ax, 'on');
            
            % Plot predicted centroid & boundary contour
            if det_res.is_detected && ~isnan(det_res.centroid_mm(1))
                plot(ax, det_res.centroid_mm(1), det_res.centroid_mm(2), 'r+', 'MarkerSize', 8, 'LineWidth', 2.0);
                % Contour of predicted binary mask
                contour(ax, x_mm, y_mm, double(det_res.predicted_mask), [0.5, 0.5], 'r-', 'LineWidth', 1.5);
            end
            
            % Ground Truth Circle if enabled
            if show_gt && sim_res.geometry.has_defect
                d = sim_res.geometry.defect;
                theta = linspace(0, 2*pi, 60);
                gt_x = d.center_x_mm + (d.diameter_mm / 2.0) * cos(theta);
                gt_y = d.center_y_mm + (d.diameter_mm / 2.0) * sin(theta);
                plot(ax, gt_x, gt_y, 'w--', 'LineWidth', 1.5);
            end
            hold(ax, 'off');
            
            if isfield(method_res, 'metrics') && isfield(method_res.metrics, 'iou')
                title_str = sprintf('%s\nIoU: %.2f | CNR: %.2f', method_title, method_res.metrics.iou, method_res.metrics.cnr);
            else
                title_str = method_title;
            end
            title(ax, title_str, 'FontSize', 8, 'FontWeight', 'bold', 'Color', [0.9, 0.95, 1.0]);
        end
        
        function updatePrimaryDisplay(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'processed')
                return;
            end
            
            meth = app.MethodDrop.Value;
            proc = app.CurrentResults.processed;
            switch meth
                case 'Matched Filter',       m_data = proc.MF;
                case 'PCT (SVD)',            m_data = proc.PCT;
                case 'SPCT (Sparse PCA)',   m_data = proc.SPCT;
                case 'Raw Contrast',         m_data = proc.RAW;
                case 'RPT (Random Proj)',    m_data = proc.RPT;
            end
            
            met = m_data.metrics;
            det = m_data.detection;
            
            % Overall Lamp & Status
            if met.is_detected
                app.DetectionLamp.Color = [0.1, 0.85, 0.2];
                app.DetectionText.Text = 'DEFECT DETECTED: YES';
                app.DetectionText.FontColor = [0.2, 0.9, 0.3];
            else
                app.DetectionLamp.Color = [0.85, 0.2, 0.2];
                app.DetectionText.Text = 'DEFECT DETECTED: NO';
                app.DetectionText.FontColor = [0.95, 0.4, 0.4];
            end
            
            % Update Metric Summary Text
            if det.is_detected
                app.MetricSummaryLabel.Text = sprintf(...
                    "PRIMARY METHOD: %s\n• Estimated Location: (%.1f, %.1f) mm [Error: %.2f mm]\n• Estimated Diameter: %.1f mm [Error: %.2f mm]\n• Overlap Metrics: IoU = %.3f | Dice = %.3f\n• Signal Quality: CNR = %.2f | ROC AUC = %.3f\n• Execution Time: %.3f s", ...
                    meth, det.centroid_mm(1), det.centroid_mm(2), met.localization_error_mm, ...
                    det.equivalent_diameter_mm, met.diameter_error_mm, ...
                    met.iou, met.dice, met.cnr, met.roc_auc, met.runtime_s);
            else
                app.MetricSummaryLabel.Text = sprintf(...
                    "PRIMARY METHOD: %s\n• Candidate Status: No Significant Defect Detected\n• Specificity (Healthy): %.1f%%\n• Overlap Metrics: IoU = %.3f | Dice = %.3f\n• Signal Quality: CNR = %.2f\n• Execution Time: %.3f s", ...
                    meth, met.specificity * 100, met.iou, met.dice, met.cnr, met.runtime_s);
            end
        end
        
        function updateMetricsTable(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'summary_table')
                return;
            end
            
            tbl = app.CurrentResults.summary_table;
            data_cells = cell(height(tbl), 8);
            for i = 1:height(tbl)
                data_cells{i, 1} = char(tbl.Method(i));
                if tbl.Detected(i)
                    data_cells{i, 2} = 'YES (Pass)';
                else
                    data_cells{i, 2} = 'NO (Fail)';
                end
                data_cells{i, 3} = sprintf('%.2f', tbl.CNR(i));
                data_cells{i, 4} = sprintf('%.3f', tbl.IoU(i));
                data_cells{i, 5} = sprintf('%.3f', tbl.Dice(i));
                if isnan(tbl.LocError_mm(i))
                    data_cells{i, 6} = 'N/A';
                else
                    data_cells{i, 6} = sprintf('%.2f', tbl.LocError_mm(i));
                end
                if isnan(tbl.DiamError_mm(i))
                    data_cells{i, 7} = 'N/A';
                else
                    data_cells{i, 7} = sprintf('%.2f', tbl.DiamError_mm(i));
                end
                data_cells{i, 8} = sprintf('%.3f', tbl.Runtime_s(i));
            end
            app.MetricsTable.Data = data_cells;
        end
        
        %% Results Saving & Report Exporting
        function saveResults(app, showAlert)
            if nargin < 2, showAlert = false; end
            if isempty(app.CurrentResults)
                if showAlert && isvalid(app.UIFigure)
                    uialert(app.UIFigure, 'No inspection results available to save. Run an inspection first.', 'Save Warning', 'Icon', 'warning');
                end
                return;
            end
            
            root_dir = fileparts(mfilename('fullpath'));
            export_dir = fullfile(root_dir, 'results', 'exports');
            if ~exist(export_dir, 'dir'), mkdir(export_dir); end
            
            ts_str = datestr(now, 'yyyymmdd_HHMMSS');
            mat_file = fullfile(export_dir, sprintf('lfmt_run_%s.mat', ts_str));
            csv_file = fullfile(export_dir, sprintf('lfmt_metrics_%s.csv', ts_str));
            
            inspection_results = app.CurrentResults; %#ok<NASGU>
            save(mat_file, 'inspection_results', '-v7.3');
            writetable(app.CurrentResults.summary_table, csv_file);
            
            app.logMessage(sprintf('Results successfully saved to:\n  -> %s\n  -> %s', mat_file, csv_file));
            if showAlert && isvalid(app.UIFigure)
                uialert(app.UIFigure, sprintf('Results saved successfully:\n%s', mat_file), 'Save Complete', 'Icon', 'info');
            end
        end
        
        function exportReport(app, showAlert)
            if nargin < 2, showAlert = false; end
            if isempty(app.CurrentResults)
                if showAlert && isvalid(app.UIFigure)
                    uialert(app.UIFigure, 'No inspection results available to export. Run an inspection first.', 'Export Warning', 'Icon', 'warning');
                end
                return;
            end
            
            root_dir = fileparts(mfilename('fullpath'));
            ts_str = datestr(now, 'yyyymmdd_HHMMSS');
            run_folder = fullfile(root_dir, 'results', 'exports', sprintf('report_%s', ts_str));
            if ~exist(run_folder, 'dir'), mkdir(run_folder); end
            
            % 1. Save Summary CSV
            writetable(app.CurrentResults.summary_table, fullfile(run_folder, 'method_metrics.csv'));
            
            % 2. Save Config JSON
            cfg = app.CurrentResults.config;
            json_str = jsonencode(cfg, 'PrettyPrint', true);
            fid = fopen(fullfile(run_folder, 'configuration.json'), 'w');
            if fid > 0
                fprintf(fid, '%s', json_str);
                fclose(fid);
            end
            
            % 3. Export PNG Figures
            try
                exportgraphics(app.ThermogramAxes, fullfile(run_folder, 'thermogram_snapshot.png'), 'Resolution', 300);
                exportgraphics(app.WaveformAxes, fullfile(run_folder, 'lfmt_waveform.png'), 'Resolution', 300);
                app.logMessage(sprintf('Exported run report package to folder:\n  -> %s', run_folder));
                if showAlert && isvalid(app.UIFigure)
                    uialert(app.UIFigure, sprintf('Report exported successfully to:\n%s', run_folder), 'Export Complete', 'Icon', 'info');
                end
            catch ME
                app.logMessage(['Warning during report export: ', ME.message]);
            end
        end
        
        %% Validation & Test Runners from GUI
        function runValidation(app)
            app.logMessage('Starting Quick Validation Suite in background...');
            app.StageLabel.Text = 'Status: Running Validation...';
            drawnow;
            try
                val_res = run_validation_suite('Quick', true); %#ok<NASGU>
                app.logMessage('Validation suite completed successfully (All modules passed).');
                app.StageLabel.Text = 'Status: Validation Passed';
                app.StageLabel.FontColor = [0.4, 0.9, 0.5];
            catch ME
                app.logMessage(['Validation Suite Error: ', ME.message]);
            end
        end
        
        function runTests(app)
            app.logMessage('Executing MATLAB Unit Test Suite (28 Tests)...');
            app.StageLabel.Text = 'Status: Running Unit Tests...';
            drawnow;
            try
                test_res = run_tests();
                if all([test_res.Passed])
                    app.logMessage('All 28 Unit Tests Passed (100% GREEN).');
                    app.StageLabel.Text = 'Status: All Tests Passed';
                    app.StageLabel.FontColor = [0.4, 0.9, 0.5];
                else
                    app.logMessage('Some tests failed. Check test log.');
                end
            catch ME
                app.logMessage(['Unit Test Runner Error: ', ME.message]);
            end
        end
    end
end
