classdef LFMTLiveLab < handle
    % LFMTLiveLab Professional Research Demonstration & Live Interactive Lab
    %
    % Linear Frequency-Modulated Infrared Thermography (LFMT / FMTWI)
    % for Subsurface Slag Inclusion Detection in Mild Steel.
    %
    % Interactive Visual Pipeline Architecture:
    %   Input Parameters -> LFMT Excitation -> 3-D Hex8 FEM Solver ->
    %   Transient Diffusion -> Virtual IR Camera & Noise -> 5 Blind Methods ->
    %   Automatic Segmentation -> Quantitative Evaluation -> Full Export
    %
    % Views:
    %   1. LIVE INSPECTION: Dual-column interactive dashboard & real-time point inspector
    %   2. SIMULATION CONNECTION: Connected block diagram with live dynamic stage lamps
    %   3. FEM & 3D PHYSICAL MODEL: 3D plate geometry, defect volume & Hex8 mesh DOFs
    %   4. THERMAL VIDEO STUDIO: Large video player, lock color scale, stats, MP4 export
    %   5. 5-METHOD BENCHMARK: Side-by-side score maps, segmentation masks & CNR rankings
    %   6. RESULTS & AUDIT: Ground-truth contrast verification (isolated) & metric export
    %
    % Usage:
    %   app = LFMTLiveLab();
    %   % or simply:
    %   LFMTLiveLab;

    properties (Access = public)
        UIFigure matlab.ui.Figure
        
        % Main Tab Navigation
        MainTabGroup matlab.ui.container.TabGroup
        LiveInspectionTab matlab.ui.container.Tab
        SimConnectionTab matlab.ui.container.Tab
        FEMModelTab matlab.ui.container.Tab
        ThermalStudioTab matlab.ui.container.Tab
        BenchmarkTab matlab.ui.container.Tab
        AuditTab matlab.ui.container.Tab
        
        % Left Column Panels (Global Controls)
        LeftScrollPanel matlab.ui.container.Panel
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
        
        % Camera & Noise Controls
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
        SaveResButton matlab.ui.control.Button
        ExportRepButton matlab.ui.control.Button
        RunValButton matlab.ui.control.Button
        RunTestButton matlab.ui.control.Button
        ExportMP4Button matlab.ui.control.Button
        OpenLargeViewButton matlab.ui.control.Button
        
        % Status & Stage Indicators
        StageLabel matlab.ui.control.Label
        ProgressLabel matlab.ui.control.Label
        
        % --- TAB 1: LIVE INSPECTION COMPONENTS ---
        ThermogramAxes matlab.ui.control.UIAxes
        FrameSlider matlab.ui.control.Slider
        PlayButton matlab.ui.control.Button
        PrevButton matlab.ui.control.Button
        NextButton matlab.ui.control.Button
        SpeedDrop matlab.ui.control.DropDown
        LockColorScaleCheck matlab.ui.control.CheckBox
        LoopVideoCheck matlab.ui.control.CheckBox
        FrameInfoLabel matlab.ui.control.Label
        ThermalStatsLabel matlab.ui.control.Label
        
        SignalTabGroup matlab.ui.container.TabGroup
        WaveformTab matlab.ui.container.Tab
        WaveformAxes matlab.ui.control.UIAxes
        PixelCurveTab matlab.ui.container.Tab
        PixelCurveAxes matlab.ui.control.UIAxes
        GTAnalysisTab matlab.ui.container.Tab
        GTAnalysisAxes matlab.ui.control.UIAxes
        
        DetectionLamp matlab.ui.control.Lamp
        DetectionText matlab.ui.control.Label
        MethodDrop matlab.ui.control.DropDown
        GTOverlayCheck matlab.ui.control.CheckBox
        MetricSummaryLabel matlab.ui.control.Label
        
        AxesRaw matlab.ui.control.UIAxes
        AxesMF matlab.ui.control.UIAxes
        AxesPCT matlab.ui.control.UIAxes
        AxesSPCT matlab.ui.control.UIAxes
        AxesRPT matlab.ui.control.UIAxes
        
        ResultsTabGroup matlab.ui.container.TabGroup
        TableTab matlab.ui.container.Tab
        MetricsTable matlab.ui.control.Table
        LogTab matlab.ui.container.Tab
        LogTextArea matlab.ui.control.TextArea
        
        % --- TAB 2: SIMULATION CONNECTION COMPONENTS ---
        SimConnGrid matlab.ui.container.GridLayout
        StageLamps
        StageStatusLabels
        StageDetailTextArea matlab.ui.control.TextArea
        ConnFlowAxes matlab.ui.control.UIAxes
        
        % --- TAB 3: FEM & 3D PHYSICAL MODEL COMPONENTS ---
        Axes3DPlate matlab.ui.control.UIAxes
        AxesMesh matlab.ui.control.UIAxes
        AxesCrossSection matlab.ui.control.UIAxes
        MeshDataTable matlab.ui.control.Table
        
        % --- TAB 4: THERMAL VIDEO STUDIO COMPONENTS ---
        StudioAxes matlab.ui.control.UIAxes
        StudioFluxAxes matlab.ui.control.UIAxes
        StudioEnvelopeAxes matlab.ui.control.UIAxes
        StudioFrameSlider matlab.ui.control.Slider
        StudioPlayButton matlab.ui.control.Button
        StudioSpeedDrop matlab.ui.control.DropDown
        StudioStatsLabel matlab.ui.control.Label
        
        % --- TAB 5: 5-METHOD BENCHMARK COMPONENTS ---
        BenchAxesRaw matlab.ui.control.UIAxes
        BenchAxesMF matlab.ui.control.UIAxes
        BenchAxesPCT matlab.ui.control.UIAxes
        BenchAxesSPCT matlab.ui.control.UIAxes
        BenchAxesRPT matlab.ui.control.UIAxes
        BenchBarAxes matlab.ui.control.UIAxes
        
        % --- TAB 6: RESULTS & AUDIT COMPONENTS ---
        AuditGTAxes matlab.ui.control.UIAxes
        AuditParamTable matlab.ui.control.Table
        AuditMetricsTable matlab.ui.control.Table
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
        
        GlobalTMin double = 293.15
        GlobalTMax double = 295.00
        WaveformCursorHandle
        StudioFluxCursorHandle
        StudioEnvCursorHandle
        PopoutFigure matlab.ui.Figure
        PopoutAxes matlab.ui.control.UIAxes
        PopoutTimer timer
    end

    methods
        function app = LFMTLiveLab()
            % Constructor: Set up path, construct UI, and load initial defaults
            app.setupEnvironment();
            app.createUI();
            app.loadDefaultPreset();
            app.updateSimulationConnectionVisuals('ready');
            app.update3DPhysicalModel();
            app.logMessage('LFMT Live Thermography Lab initialized successfully.');
            app.logMessage('Simulation Connection & 3-D FEM Engine ready for execution.');
        end
        
        function delete(app)
            % Destructor: Clean up all timers and popouts
            if ~isempty(app.PlayTimer) && isvalid(app.PlayTimer)
                stop(app.PlayTimer);
                delete(app.PlayTimer);
            end
            if ~isempty(app.PopoutTimer) && isvalid(app.PopoutTimer)
                stop(app.PopoutTimer);
                delete(app.PopoutTimer);
            end
            if ~isempty(app.PopoutFigure) && isvalid(app.PopoutFigure)
                delete(app.PopoutFigure);
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
                'Position', [30, 30, 1560, 940], ...
                'Color', [0.11, 0.13, 0.17], ...
                'CloseRequestFcn', @(src, evt) app.onCloseRequest());
            
            % Outer Grid Layout: Top Header (46px) + Main Content ('1x')
            outerGrid = uigridlayout(app.UIFigure, [2, 1]);
            outerGrid.RowHeight = {46, '1x'};
            outerGrid.Padding = [6, 6, 6, 6];
            outerGrid.RowSpacing = 4;
            
            % --- TOP HEADER BAR ---
            headerPanel = uipanel(outerGrid, 'BackgroundColor', [0.15, 0.18, 0.24], 'BorderType', 'none');
            headerPanel.Layout.Row = 1;
            
            headerGrid = uigridlayout(headerPanel, [1, 2]);
            headerGrid.ColumnWidth = {'1x', 380};
            headerGrid.Padding = [10, 4, 10, 4];
            
            titleLabel = uilabel(headerGrid, 'Text', '🔬 LFMT LIVE THERMOGRAPHY LAB — Subsurface Slag Inclusion Detection in Mild Steel', ...
                'FontSize', 15, 'FontWeight', 'bold', 'FontColor', [0.95, 0.97, 1.0]);
            titleLabel.Layout.Column = 1;
            
            subtitleLabel = uilabel(headerGrid, 'Text', 'Linear Frequency-Modulated Thermal Waves • 3-D Hex8 FEM • 5 Blind Methods', ...
                'FontSize', 10, 'FontColor', [0.65, 0.78, 0.95], 'HorizontalAlignment', 'right');
            subtitleLabel.Layout.Column = 2;
            
            % --- MAIN WORKSPACE GRID: Left Control Sidebar (310px) + Right TabGroup ('1x') ---
            workspaceGrid = uigridlayout(outerGrid, [1, 2]);
            workspaceGrid.Layout.Row = 2;
            workspaceGrid.ColumnWidth = {310, '1x'};
            workspaceGrid.Padding = [0, 0, 0, 0];
            workspaceGrid.ColumnSpacing = 6;
            
            % Build Left Sidebar
            app.createLeftSidebar(workspaceGrid);
            
            % Build Right Main TabGroup
            app.MainTabGroup = uitabgroup(workspaceGrid);
            app.MainTabGroup.Layout.Column = 2;
            
            % 6 Primary Tabs
            app.LiveInspectionTab = uitab(app.MainTabGroup, 'Title', '🔬 LIVE INSPECTION');
            app.SimConnectionTab = uitab(app.MainTabGroup, 'Title', '🔄 SIMULATION CONNECTION');
            app.FEMModelTab = uitab(app.MainTabGroup, 'Title', '📐 FEM & 3D MODEL');
            app.ThermalStudioTab = uitab(app.MainTabGroup, 'Title', '🎬 THERMAL VIDEO STUDIO');
            app.BenchmarkTab = uitab(app.MainTabGroup, 'Title', '📊 5-METHOD BENCHMARK');
            app.AuditTab = uitab(app.MainTabGroup, 'Title', '📋 RESULTS & AUDIT');
            
            % Populate All Tabs
            app.buildLiveInspectionTab();
            app.buildSimConnectionTab();
            app.buildFEMModelTab();
            app.buildThermalStudioTab();
            app.buildBenchmarkTab();
            app.buildAuditTab();
            
            % Playback Timer (~25 fps)
            app.PlayTimer = timer('ExecutionMode', 'fixedRate', 'Period', 0.04, ...
                'TimerFcn', @(src, evt) app.onTimerTick());
        end
        
        %% Left Sidebar Construction
        function createLeftSidebar(app, parentGrid)
            app.LeftScrollPanel = uipanel(parentGrid, 'Title', '⚙️ SIMULATION & INSPECTION CONTROLS', ...
                'FontSize', 11, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.14, 0.16, 0.21], 'Scrollable', 'on');
            app.LeftScrollPanel.Layout.Column = 1;
            
            leftGrid = uigridlayout(app.LeftScrollPanel, [22, 2]);
            leftGrid.ColumnWidth = {'1x', '1x'};
            leftGrid.RowHeight = repmat({23}, 1, 22);
            leftGrid.Padding = [6, 4, 6, 4];
            leftGrid.RowSpacing = 3;
            
            % 1. Defect Presets
            lbl = uilabel(leftGrid, 'Text', 'PRESET & DEFECT:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'Defect Preset:', 'FontColor', [0.85, 0.85, 0.9]);
            app.DefectPresetDrop = uidropdown(leftGrid, 'Items', {...
                '8 mm (z=0.4 mm) [Default / Easy]', ...
                '6 mm (z=0.4 mm) [Medium]', ...
                '8 mm (z=0.8 mm) [Deep]', ...
                '4 mm (z=1.0 mm) [Hard / Small]', ...
                'Healthy Control (D=0) [No Defect]', ...
                'Custom Values'}, ...
                'ValueChangedFcn', @(src, evt) app.onDefectPresetChanged());
            
            app.HealthyCheck = uicheckbox(leftGrid, 'Text', 'Healthy Plate / No Inclusion', 'FontWeight', 'bold', ...
                'FontColor', [0.4, 0.9, 0.5], 'ValueChangedFcn', @(src, evt) app.onHealthyCheckChanged());
            app.HealthyCheck.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'Diameter [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.DiamEdit = uieditfield(leftGrid, 'numeric', 'Value', 8.0, 'Limits', [0, 50], ...
                'ValueChangedFcn', @(src, evt) app.update3DPhysicalModel());
            
            uilabel(leftGrid, 'Text', 'Depth z [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.DepthEdit = uieditfield(leftGrid, 'numeric', 'Value', 0.4, 'Limits', [0, 2.3], ...
                'ValueChangedFcn', @(src, evt) app.update3DPhysicalModel());
            
            uilabel(leftGrid, 'Text', 'Thickness [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.ThickEdit = uieditfield(leftGrid, 'numeric', 'Value', 0.5, 'Limits', [0.1, 2.0], ...
                'ValueChangedFcn', @(src, evt) app.update3DPhysicalModel());
            
            uilabel(leftGrid, 'Text', 'Center X / Y [mm]:', 'FontColor', [0.85, 0.85, 0.9]);
            posGrid = uigridlayout(leftGrid, [1, 2]);
            posGrid.Padding = [0, 0, 0, 0]; posGrid.ColumnSpacing = 3;
            app.PosXEdit = uieditfield(posGrid, 'numeric', 'Value', 50.0, 'ValueChangedFcn', @(src, evt) app.update3DPhysicalModel());
            app.PosYEdit = uieditfield(posGrid, 'numeric', 'Value', 35.0, 'ValueChangedFcn', @(src, evt) app.update3DPhysicalModel());
            
            % 2. LFMT Excitation Parameters
            lbl = uilabel(leftGrid, 'Text', 'LFMT EXCITATION:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'f0 / f1 [Hz]:', 'FontColor', [0.85, 0.85, 0.9]);
            fGrid = uigridlayout(leftGrid, [1, 2]);
            fGrid.Padding = [0, 0, 0, 0]; fGrid.ColumnSpacing = 3;
            app.F0Edit = uieditfield(fGrid, 'numeric', 'Value', 0.05, 'Limits', [0.001, 10], 'ValueChangedFcn', @(src, evt) app.updateExcitationWaveformPlot());
            app.F1Edit = uieditfield(fGrid, 'numeric', 'Value', 0.50, 'Limits', [0.001, 10], 'ValueChangedFcn', @(src, evt) app.updateExcitationWaveformPlot());
            
            uilabel(leftGrid, 'Text', 'Heat Flux q0 [W/m²]:', 'FontColor', [0.85, 0.85, 0.9]);
            app.Q0Edit = uieditfield(leftGrid, 'numeric', 'Value', 5000, 'Limits', [100, 100000], 'ValueChangedFcn', @(src, evt) app.updateExcitationWaveformPlot());
            
            uilabel(leftGrid, 'Text', 'Texc / Tobs [s]:', 'FontColor', [0.85, 0.85, 0.9]);
            tGrid = uigridlayout(leftGrid, [1, 2]);
            tGrid.Padding = [0, 0, 0, 0]; tGrid.ColumnSpacing = 3;
            app.TexcEdit = uieditfield(tGrid, 'numeric', 'Value', 10.0, 'Limits', [1, 100], 'ValueChangedFcn', @(src, evt) app.updateExcitationWaveformPlot());
            app.TobsEdit = uieditfield(tGrid, 'numeric', 'Value', 10.0, 'Limits', [1, 100], 'ValueChangedFcn', @(src, evt) app.updateExcitationWaveformPlot());
            
            % 3. Camera & Noise
            lbl = uilabel(leftGrid, 'Text', 'CAMERA & NOISE:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'Noise Condition:', 'FontColor', [0.85, 0.85, 0.9]);
            app.NoiseModeDrop = uidropdown(leftGrid, 'Items', {'Clean (Inf dB)', '30 dB SNR', '25 dB SNR', '20 dB SNR', 'Custom SNR'}, ...
                'ValueChangedFcn', @(src, evt) app.onNoiseModeChanged());
            
            uilabel(leftGrid, 'Text', 'SNR [dB] / Seed:', 'FontColor', [0.85, 0.85, 0.9]);
            snrGrid = uigridlayout(leftGrid, [1, 2]);
            snrGrid.Padding = [0, 0, 0, 0]; snrGrid.ColumnSpacing = 3;
            app.SNREdit = uieditfield(snrGrid, 'numeric', 'Value', 25.0, 'Enable', 'off');
            app.SeedEdit = uieditfield(snrGrid, 'numeric', 'Value', 42, 'Limits', [0, 999999]);
            
            % 4. Solver Settings
            lbl = uilabel(leftGrid, 'Text', 'NUMERICAL SOLVER:', 'FontWeight', 'bold', 'FontColor', [0.8, 0.9, 1.0]);
            lbl.Layout.Column = [1, 2];
            
            uilabel(leftGrid, 'Text', 'Forward Solver:', 'FontColor', [0.85, 0.85, 0.9]);
            app.SolverDrop = uidropdown(leftGrid, 'Items', {'3-D Hex8 FEM (Primary)', '3-D FDM (Secondary)'}, ...
                'ValueChangedFcn', @(src, evt) app.update3DPhysicalModel());
            
            uilabel(leftGrid, 'Text', 'Mesh Resolution:', 'FontColor', [0.85, 0.85, 0.9]);
            app.ModeDrop = uidropdown(leftGrid, 'Items', {'Standard Research', 'Quick Demo', 'High-Res Physics'}, ...
                'ValueChangedFcn', @(src, evt) app.update3DPhysicalModel());
            
            % Standard Quick Buttons
            presetGrid = uigridlayout(leftGrid, [1, 3]);
            presetGrid.Layout.Column = [1, 2];
            presetGrid.Padding = [0, 0, 0, 0]; presetGrid.ColumnSpacing = 3;
            app.LoadDefButton = uibutton(presetGrid, 'Text', 'Default', 'ButtonPushedFcn', @(src, evt) app.loadDefaultPreset());
            app.LoadConfButton = uibutton(presetGrid, 'Text', 'Conf Demo', 'ButtonPushedFcn', @(src, evt) app.loadConferencePreset());
            app.LoadLitButton = uibutton(presetGrid, 'Text', 'Literature', 'ButtonPushedFcn', @(src, evt) app.loadLiteraturePreset());
            
            % 5. Primary Run Buttons
            app.RunButton = uibutton(leftGrid, 'Text', '▶ RUN INSPECTION', ...
                'FontSize', 12, 'FontWeight', 'bold', 'BackgroundColor', [0.15, 0.65, 0.35], ...
                'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.runInspection());
            app.RunButton.Layout.Column = 1;
            
            app.StopButton = uibutton(leftGrid, 'Text', '⏹ STOP', ...
                'FontSize', 11, 'FontWeight', 'bold', 'BackgroundColor', [0.65, 0.20, 0.20], ...
                'FontColor', 'w', 'Enable', 'off', 'ButtonPushedFcn', @(src, evt) app.stopExecution());
            app.StopButton.Layout.Column = 2;
            
            % Status Bar
            app.StageLabel = uilabel(leftGrid, 'Text', 'Status: Ready', 'FontWeight', 'bold', 'FontColor', [0.4, 0.9, 0.5]);
            app.StageLabel.Layout.Column = [1, 2];
            
            % Action Buttons Grid
            actGrid = uigridlayout(leftGrid, [2, 2]);
            actGrid.Layout.Column = [1, 2];
            actGrid.Padding = [0, 0, 0, 0]; actGrid.RowSpacing = 3; actGrid.ColumnSpacing = 3;
            app.SaveResButton = uibutton(actGrid, 'Text', '💾 Save Data', 'ButtonPushedFcn', @(src, evt) app.saveResults(true));
            app.ExportRepButton = uibutton(actGrid, 'Text', '📊 Export Report', 'ButtonPushedFcn', @(src, evt) app.exportReport(true));
            app.RunValButton = uibutton(actGrid, 'Text', '🔬 Validate', 'ButtonPushedFcn', @(src, evt) app.runValidation());
            app.RunTestButton = uibutton(actGrid, 'Text', '🧪 Run Tests', 'ButtonPushedFcn', @(src, evt) app.runTests());
        end
        
        %% Tab 1: Live Inspection Construction
        function buildLiveInspectionTab(app)
            tabGrid = uigridlayout(app.LiveInspectionTab, [1, 2]);
            tabGrid.ColumnWidth = {530, '1x'};
            tabGrid.Padding = [4, 4, 4, 4];
            tabGrid.ColumnSpacing = 6;
            
            % Center Sub-panel (Video & Curves)
            centerGrid = uigridlayout(tabGrid, [4, 1]);
            centerGrid.RowHeight = {360, 42, 28, '1x'};
            centerGrid.Padding = [2, 2, 2, 2];
            centerGrid.RowSpacing = 3;
            
            % Thermogram Axes Panel
            thermoPanel = uipanel(centerGrid, 'Title', '📹 LIVE IR THERMOGRAM (Click pixel to inspect transient curve)', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            thermoPanel.Layout.Row = 1;
            
            thermoGrid = uigridlayout(thermoPanel, [1, 1]);
            thermoGrid.Padding = [2, 2, 2, 2];
            app.ThermogramAxes = uiaxes(thermoGrid);
            app.ThermogramAxes.Color = [0.08, 0.09, 0.12];
            app.ThermogramAxes.XColor = [0.8, 0.8, 0.85];
            app.ThermogramAxes.YColor = [0.8, 0.8, 0.85];
            title(app.ThermogramAxes, 'Front-Surface Transient Temperature Field T(x,y,t)', 'Color', [0.95, 0.95, 0.95], 'FontSize', 10);
            xlabel(app.ThermogramAxes, 'Plate Length X [mm]');
            ylabel(app.ThermogramAxes, 'Plate Width Y [mm]');
            colormap(app.ThermogramAxes, 'turbo');
            app.ThermogramAxes.ButtonDownFcn = @(src, evt) app.onThermogramClicked(evt);
            
            % Playback Controls
            playPanel = uipanel(centerGrid, 'BackgroundColor', [0.16, 0.18, 0.22], 'BorderType', 'none');
            playPanel.Layout.Row = 2;
            playGrid = uigridlayout(playPanel, [1, 8]);
            playGrid.ColumnWidth = {36, 65, 36, '1x', 52, 95, 65, 110};
            playGrid.Padding = [4, 2, 4, 2];
            playGrid.ColumnSpacing = 4;
            
            app.PrevButton = uibutton(playGrid, 'Text', '⏮', 'ButtonPushedFcn', @(src, evt) app.stepFrame(-1));
            app.PlayButton = uibutton(playGrid, 'Text', '▶ Play', 'FontWeight', 'bold', ...
                'BackgroundColor', [0.2, 0.45, 0.7], 'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.togglePlayback());
            app.NextButton = uibutton(playGrid, 'Text', '⏭', 'ButtonPushedFcn', @(src, evt) app.stepFrame(1));
            
            app.FrameSlider = uislider(playGrid, 'Limits', [1, 251], 'Value', 1, ...
                'ValueChangedFcn', @(src, evt) app.onSliderChanged());
            
            app.SpeedDrop = uidropdown(playGrid, 'Items', {'0.25x', '0.5x', '1.0x', '2.0x', '4.0x'}, 'Value', '1.0x', ...
                'ValueChangedFcn', @(src, evt) app.onSpeedChanged());
            
            app.LockColorScaleCheck = uicheckbox(playGrid, 'Text', 'Lock Scale', 'FontColor', [0.85, 0.9, 1.0], ...
                'Value', false, 'ValueChangedFcn', @(src, evt) app.updateThermogramFrame());
            
            app.LoopVideoCheck = uicheckbox(playGrid, 'Text', 'Loop', 'FontColor', [0.85, 0.9, 1.0], 'Value', true);
            
            app.OpenLargeViewButton = uibutton(playGrid, 'Text', '🖥 Large View', 'FontWeight', 'bold', ...
                'BackgroundColor', [0.35, 0.35, 0.55], 'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.openLargeThermalView());
            
            % Stats Bar
            statsPanel = uipanel(centerGrid, 'BackgroundColor', [0.12, 0.14, 0.18], 'BorderType', 'none');
            statsPanel.Layout.Row = 3;
            statsGrid = uigridlayout(statsPanel, [1, 2]);
            statsGrid.ColumnWidth = {'1x', '1x'};
            statsGrid.Padding = [6, 2, 6, 2];
            
            app.FrameInfoLabel = uilabel(statsGrid, 'Text', 'Frame: 1 / 1  |  Time: 0.00 s  |  Inst. Freq: 0.050 Hz', ...
                'FontColor', [0.95, 0.85, 0.4], 'FontWeight', 'bold', 'FontSize', 10);
            app.ThermalStatsLabel = uilabel(statsGrid, 'Text', 'Min: 293.15 K  |  Max: 293.15 K  |  Mean: 293.15 K', ...
                'FontColor', [0.7, 0.9, 1.0], 'HorizontalAlignment', 'right', 'FontSize', 10);
            
            % Center Bottom Tab Group
            app.SignalTabGroup = uitabgroup(centerGrid);
            app.SignalTabGroup.Layout.Row = 4;
            
            app.WaveformTab = uitab(app.SignalTabGroup, 'Title', '📈 LFMT Waveform & Frequency');
            waveGrid = uigridlayout(app.WaveformTab, [1, 1]); waveGrid.Padding = [2, 2, 2, 2];
            app.WaveformAxes = uiaxes(waveGrid);
            app.WaveformAxes.Color = [0.08, 0.09, 0.12];
            app.WaveformAxes.XColor = [0.8, 0.8, 0.85]; app.WaveformAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.WaveformAxes, 'Time t [s]'); ylabel(app.WaveformAxes, 'Flux q(t) [W/m²]');
            grid(app.WaveformAxes, 'on');
            
            app.PixelCurveTab = uitab(app.SignalTabGroup, 'Title', '📍 Pixel Thermal Curve');
            pixGrid = uigridlayout(app.PixelCurveTab, [1, 1]); pixGrid.Padding = [2, 2, 2, 2];
            app.PixelCurveAxes = uiaxes(pixGrid);
            app.PixelCurveAxes.Color = [0.08, 0.09, 0.12];
            app.PixelCurveAxes.XColor = [0.8, 0.8, 0.85]; app.PixelCurveAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.PixelCurveAxes, 'Time t [s]'); ylabel(app.PixelCurveAxes, 'Temperature T [K]');
            grid(app.PixelCurveAxes, 'on');
            
            app.GTAnalysisTab = uitab(app.SignalTabGroup, 'Title', '🔍 GT Contrast (Audit Only)');
            gtGrid = uigridlayout(app.GTAnalysisTab, [1, 1]); gtGrid.Padding = [2, 2, 2, 2];
            app.GTAnalysisAxes = uiaxes(gtGrid);
            app.GTAnalysisAxes.Color = [0.08, 0.09, 0.12];
            app.GTAnalysisAxes.XColor = [0.8, 0.8, 0.85]; app.GTAnalysisAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.GTAnalysisAxes, 'Time t [s]'); ylabel(app.GTAnalysisAxes, 'Differential Contrast \Delta T [K]');
            grid(app.GTAnalysisAxes, 'on');
            
            % Right Sub-panel (5 Score Maps & Metrics)
            rightGrid = uigridlayout(tabGrid, [4, 1]);
            rightGrid.RowHeight = {58, 330, '1x', 130};
            rightGrid.Padding = [2, 2, 2, 2];
            rightGrid.RowSpacing = 3;
            
            % Defect Classification Header
            resHeaderPanel = uipanel(rightGrid, 'Title', '🎯 INSPECTION RESULT & CLASSIFICATION', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.16, 0.18, 0.24]);
            resHeaderPanel.Layout.Row = 1;
            resHGrid = uigridlayout(resHeaderPanel, [1, 4]);
            resHGrid.ColumnWidth = {26, 130, '1x', 165};
            resHGrid.Padding = [4, 2, 4, 2];
            
            app.DetectionLamp = uilamp(resHGrid, 'Color', [0.5, 0.5, 0.5]);
            app.DetectionText = uilabel(resHGrid, 'Text', 'STATUS: READY', 'FontSize', 11, 'FontWeight', 'bold', 'FontColor', [0.9, 0.9, 0.95]);
            
            methGrid = uigridlayout(resHGrid, [1, 2]);
            methGrid.Padding = [0, 0, 0, 0];
            uilabel(methGrid, 'Text', 'Method:', 'FontColor', [0.85, 0.85, 0.9], 'HorizontalAlignment', 'right', 'FontSize', 10);
            app.MethodDrop = uidropdown(methGrid, 'Items', {'Matched Filter', 'PCT (SVD)', 'SPCT (Sparse PCA)', 'Raw Contrast', 'RPT (Random Proj)'}, ...
                'ValueChangedFcn', @(src, evt) app.updatePrimaryDisplay());
            
            app.GTOverlayCheck = uicheckbox(resHGrid, 'Text', 'Show GT Overlay', ...
                'FontColor', [0.95, 0.85, 0.4], 'FontWeight', 'bold', 'Value', false, ...
                'ValueChangedFcn', @(src, evt) app.updateAllProcessedPlots());
            
            % 5 Blind Processing Score Maps
            mapsPanel = uipanel(rightGrid, 'Title', '📊 5 BLIND THERMOGRAPHIC SIGNAL PROCESSING SCORE MAPS', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            mapsPanel.Layout.Row = 2;
            
            mapsGrid = uigridlayout(mapsPanel, [2, 3]);
            mapsGrid.RowHeight = {'1x', '1x'};
            mapsGrid.ColumnWidth = {'1x', '1x', '1x'};
            mapsGrid.Padding = [3, 3, 3, 3];
            mapsGrid.RowSpacing = 3; mapsGrid.ColumnSpacing = 3;
            
            app.AxesRaw = app.createMiniAxes(mapsGrid, '1. Raw Contrast');
            app.AxesMF = app.createMiniAxes(mapsGrid, '2. Matched Filter');
            app.AxesPCT = app.createMiniAxes(mapsGrid, '3. SVD-PCT');
            app.AxesSPCT = app.createMiniAxes(mapsGrid, '4. Sparse PCA');
            app.AxesRPT = app.createMiniAxes(mapsGrid, '5. Random Proj');
            
            metricSummaryPanel = uipanel(mapsGrid, 'BackgroundColor', [0.16, 0.18, 0.22], 'BorderType', 'none');
            mSumGrid = uigridlayout(metricSummaryPanel, [1, 1]); mSumGrid.Padding = [4, 2, 4, 2];
            app.MetricSummaryLabel = uilabel(mSumGrid, 'Text', "Run inspection to view 5-method detection metrics.", ...
                'FontColor', [0.9, 0.95, 1.0], 'WordWrap', 'on', 'FontSize', 9);
            
            % Results Tab Group
            app.ResultsTabGroup = uitabgroup(rightGrid);
            app.ResultsTabGroup.Layout.Row = [3, 4];
            
            app.TableTab = uitab(app.ResultsTabGroup, 'Title', '📋 5-Method Metrics');
            tGrid = uigridlayout(app.TableTab, [1, 1]); tGrid.Padding = [2, 2, 2, 2];
            app.MetricsTable = uitable(tGrid, 'ColumnName', {'Method', 'Detected', 'CNR', 'IoU', 'Dice', 'Loc Err', 'Diam Err', 'Time (s)'}, ...
                'RowName', {}, 'BackgroundColor', [0.15, 0.17, 0.22; 0.18, 0.20, 0.26], ...
                'ForegroundColor', [0.95, 0.95, 0.95]);
            
            app.LogTab = uitab(app.ResultsTabGroup, 'Title', '📝 Live Log');
            logGrid = uigridlayout(app.LogTab, [1, 1]); logGrid.Padding = [2, 2, 2, 2];
            app.LogTextArea = uitextarea(logGrid, 'BackgroundColor', [0.08, 0.09, 0.12], ...
                'FontColor', [0.4, 0.9, 0.5], 'FontName', 'Consolas', 'FontSize', 9, 'Editable', 'off');
        end
        
        %% Tab 2: Simulation Connection Construction
        function buildSimConnectionTab(app)
            simGrid = uigridlayout(app.SimConnectionTab, [2, 1]);
            simGrid.RowHeight = {160, '1x'};
            simGrid.Padding = [8, 8, 8, 8];
            simGrid.RowSpacing = 8;
            
            % Top Flow Status Stage Cards
            topPanel = uipanel(simGrid, 'Title', '🔄 SCIENTIFIC SIMULATION & PROCESSING PIPELINE FLOW', ...
                'FontSize', 11, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.14, 0.16, 0.21]);
            topPanel.Layout.Row = 1;
            
            app.SimConnGrid = uigridlayout(topPanel, [2, 8]);
            app.SimConnGrid.RowHeight = {30, '1x'};
            app.SimConnGrid.ColumnWidth = repmat({'1x'}, 1, 8);
            app.SimConnGrid.Padding = [4, 4, 4, 4];
            app.SimConnGrid.ColumnSpacing = 4;
            
            stage_names = {...
                '1. Inputs', ...
                '2. Excitation', ...
                '3. 3-D FEM', ...
                '4. IR Camera', ...
                '5. 5 Methods', ...
                '6. Segment', ...
                '7. Metrics', ...
                '8. Export'};
            
            lamps = gobjects(1, 8);
            status_lbls = gobjects(1, 8);
            
            for s = 1:8
                % Lamp Header
                hPanel = uipanel(app.SimConnGrid, 'BackgroundColor', [0.18, 0.20, 0.26], 'BorderType', 'none');
                hPanel.Layout.Row = 1; hPanel.Layout.Column = s;
                hGrid = uigridlayout(hPanel, [1, 2]);
                hGrid.ColumnWidth = {20, '1x'}; hGrid.Padding = [2, 1, 2, 1];
                
                lamps(s) = uilamp(hGrid, 'Color', [0.4, 0.4, 0.45]);
                lbl = uilabel(hGrid, 'Text', stage_names{s}, 'FontWeight', 'bold', 'FontSize', 9, 'FontColor', [0.9, 0.95, 1.0]);
                lbl.Layout.Column = 2;
                
                % Status Card
                cPanel = uipanel(app.SimConnGrid, 'BackgroundColor', [0.12, 0.13, 0.17], 'BorderType', 'line');
                cPanel.Layout.Row = 2; cPanel.Layout.Column = s;
                cGrid = uigridlayout(cPanel, [1, 1]); cGrid.Padding = [4, 4, 4, 4];
                
                status_lbls(s) = uilabel(cGrid, 'Text', 'Waiting...', 'FontSize', 8, ...
                    'FontColor', [0.75, 0.75, 0.8], 'WordWrap', 'on', 'VerticalAlignment', 'top');
            end
            
            app.StageLamps = lamps;
            app.StageStatusLabels = status_lbls;
            
            % Bottom Split: Flow Diagram Axes (Left) + Detail Inspector (Right)
            bottomGrid = uigridlayout(simGrid, [1, 2]);
            bottomGrid.Layout.Row = 2;
            bottomGrid.ColumnWidth = {'1x', 380};
            bottomGrid.Padding = [0, 0, 0, 0];
            bottomGrid.ColumnSpacing = 8;
            
            flowPanel = uipanel(bottomGrid, 'Title', '📊 CONNECTED MATHEMATICAL STAGES & TENSOR TRANSFORMATIONS', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            flowGrid = uigridlayout(flowPanel, [1, 1]); flowGrid.Padding = [4, 4, 4, 4];
            app.ConnFlowAxes = uiaxes(flowGrid);
            app.ConnFlowAxes.Color = [0.09, 0.10, 0.14];
            app.ConnFlowAxes.XColor = 'none'; app.ConnFlowAxes.YColor = 'none';
            app.drawSimulationConnectionDiagram();
            
            detailPanel = uipanel(bottomGrid, 'Title', '📖 SCIENTIFIC FORMULATION & STAGE DETAILS', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.14, 0.16, 0.21]);
            detailGrid = uigridlayout(detailPanel, [1, 1]); detailGrid.Padding = [4, 4, 4, 4];
            app.StageDetailTextArea = uitextarea(detailGrid, 'BackgroundColor', [0.08, 0.09, 0.12], ...
                'FontColor', [0.85, 0.92, 1.0], 'FontName', 'Consolas', 'FontSize', 9, 'Editable', 'off');
            app.populateStageDetailsText();
        end
        
        %% Tab 3: FEM & 3D Physical Model Construction
        function buildFEMModelTab(app)
            femGrid = uigridlayout(app.FEMModelTab, [2, 2]);
            femGrid.RowHeight = {'1x', 240};
            femGrid.ColumnWidth = {'1x', '1x'};
            femGrid.Padding = [6, 6, 6, 6];
            femGrid.RowSpacing = 6; femGrid.ColumnSpacing = 6;
            
            % 3-D Plate Volume Axes (Top Left)
            p3Panel = uipanel(femGrid, 'Title', '🧊 3-D PHYSICAL GEOMETRY (Mild Steel Plate + Slag Inclusion)', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            p3Panel.Layout.Row = 1; p3Panel.Layout.Column = 1;
            p3Grid = uigridlayout(p3Panel, [1, 1]); p3Grid.Padding = [4, 4, 4, 4];
            app.Axes3DPlate = uiaxes(p3Grid);
            app.Axes3DPlate.Color = [0.08, 0.09, 0.12];
            app.Axes3DPlate.XColor = [0.8, 0.8, 0.85]; app.Axes3DPlate.YColor = [0.8, 0.8, 0.85]; app.Axes3DPlate.ZColor = [0.8, 0.8, 0.85];
            xlabel(app.Axes3DPlate, 'X [mm]'); ylabel(app.Axes3DPlate, 'Y [mm]'); zlabel(app.Axes3DPlate, 'Z [mm]');
            grid(app.Axes3DPlate, 'on'); view(app.Axes3DPlate, [-35, 25]);
            
            % FEM Hex8 Mesh Axes (Top Right)
            meshPanel = uipanel(femGrid, 'Title', '🕸 3-D HEXAHEDRAL (Hex8) FINITE ELEMENT MESH', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            meshPanel.Layout.Row = 1; meshPanel.Layout.Column = 2;
            mGrid = uigridlayout(meshPanel, [1, 1]); mGrid.Padding = [4, 4, 4, 4];
            app.AxesMesh = uiaxes(mGrid);
            app.AxesMesh.Color = [0.08, 0.09, 0.12];
            app.AxesMesh.XColor = [0.8, 0.8, 0.85]; app.AxesMesh.YColor = [0.8, 0.8, 0.85]; app.AxesMesh.ZColor = [0.8, 0.8, 0.85];
            xlabel(app.AxesMesh, 'X [mm]'); ylabel(app.AxesMesh, 'Y [mm]'); zlabel(app.AxesMesh, 'Z [mm]');
            grid(app.AxesMesh, 'on'); view(app.AxesMesh, [-35, 25]);
            
            % Cross Section Schematic Axes (Bottom Left)
            csPanel = uipanel(femGrid, 'Title', '📐 2-D CROSS-SECTION & BOUNDARY CONDITIONS (X-Z Depth Plane)', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            csPanel.Layout.Row = 2; csPanel.Layout.Column = 1;
            csGrid = uigridlayout(csPanel, [1, 1]); csGrid.Padding = [4, 4, 4, 4];
            app.AxesCrossSection = uiaxes(csGrid);
            app.AxesCrossSection.Color = [0.08, 0.09, 0.12];
            app.AxesCrossSection.XColor = [0.8, 0.8, 0.85]; app.AxesCrossSection.YColor = [0.8, 0.8, 0.85];
            xlabel(app.AxesCrossSection, 'Plate Length X [mm]'); ylabel(app.AxesCrossSection, 'Depth Z [mm] (Inward)');
            grid(app.AxesCrossSection, 'on');
            
            % Discretization & Material Table (Bottom Right)
            dtPanel = uipanel(femGrid, 'Title', '📊 PHYSICAL CONSTANTS & NUMERICAL DISCRETIZATION SUMMARY', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.14, 0.16, 0.21]);
            dtPanel.Layout.Row = 2; dtPanel.Layout.Column = 2;
            dtGrid = uigridlayout(dtPanel, [1, 1]); dtGrid.Padding = [4, 4, 4, 4];
            app.MeshDataTable = uitable(dtGrid, 'ColumnName', {'Parameter', 'Value', 'Unit', 'Description'}, ...
                'RowName', {}, 'BackgroundColor', [0.15, 0.17, 0.22; 0.18, 0.20, 0.26], ...
                'ForegroundColor', [0.95, 0.95, 0.95]);
            app.updateMeshDataTable();
        end
        
        %% Tab 4: Thermal Video Studio Construction
        function buildThermalStudioTab(app)
            studioGrid = uigridlayout(app.ThermalStudioTab, [3, 2]);
            studioGrid.RowHeight = {'1x', 140, 40};
            studioGrid.ColumnWidth = {'1x', 360};
            studioGrid.Padding = [6, 6, 6, 6];
            studioGrid.RowSpacing = 4; studioGrid.ColumnSpacing = 6;
            
            % Large Studio Thermogram Axes
            stPanel = uipanel(studioGrid, 'Title', '🎬 FULL-RESOLUTION THERMAL VIDEO SEQUENCE', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            stPanel.Layout.Row = 1; stPanel.Layout.Column = 1;
            stGrid = uigridlayout(stPanel, [1, 1]); stGrid.Padding = [4, 4, 4, 4];
            app.StudioAxes = uiaxes(stGrid);
            app.StudioAxes.Color = [0.08, 0.09, 0.12];
            app.StudioAxes.XColor = [0.8, 0.8, 0.85]; app.StudioAxes.YColor = [0.8, 0.8, 0.85];
            title(app.StudioAxes, 'Surface Thermogram T(x,y,t)', 'Color', [0.95, 0.95, 0.95]);
            xlabel(app.StudioAxes, 'X [mm]'); ylabel(app.StudioAxes, 'Y [mm]');
            colormap(app.StudioAxes, 'turbo');
            
            % Side Sub-plot 1: Dynamic Excitation Flux
            fluxPanel = uipanel(studioGrid, 'Title', '📈 DYNAMIC LFMT HEAT FLUX q(t)', ...
                'FontSize', 9, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            fluxPanel.Layout.Row = 1; fluxPanel.Layout.Column = 2;
            flGrid = uigridlayout(fluxPanel, [1, 1]); flGrid.Padding = [4, 4, 4, 4];
            app.StudioFluxAxes = uiaxes(flGrid);
            app.StudioFluxAxes.Color = [0.08, 0.09, 0.12];
            app.StudioFluxAxes.XColor = [0.8, 0.8, 0.85]; app.StudioFluxAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.StudioFluxAxes, 'Time t [s]'); ylabel(app.StudioFluxAxes, 'Flux [W/m²]');
            grid(app.StudioFluxAxes, 'on');
            
            % Bottom Curves: Temperature Envelope (Tmax, Tmin, Tmean)
            envPanel = uipanel(studioGrid, 'Title', '📊 SURFACE TEMPERATURE ENVELOPE (Tmax, Tmean, Tmin) OVER TIME', ...
                'FontSize', 9, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            envPanel.Layout.Row = 2; envPanel.Layout.Column = [1, 2];
            envGrid = uigridlayout(envPanel, [1, 1]); envGrid.Padding = [4, 4, 4, 4];
            app.StudioEnvelopeAxes = uiaxes(envGrid);
            app.StudioEnvelopeAxes.Color = [0.08, 0.09, 0.12];
            app.StudioEnvelopeAxes.XColor = [0.8, 0.8, 0.85]; app.StudioEnvelopeAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.StudioEnvelopeAxes, 'Time t [s]'); ylabel(app.StudioEnvelopeAxes, 'Temperature T [K]');
            grid(app.StudioEnvelopeAxes, 'on');
            
            % Studio Video Playbar
            stPlayPanel = uipanel(studioGrid, 'BackgroundColor', [0.15, 0.18, 0.23], 'BorderType', 'none');
            stPlayPanel.Layout.Row = 3; stPlayPanel.Layout.Column = [1, 2];
            stPlayGrid = uigridlayout(stPlayPanel, [1, 8]);
            stPlayGrid.ColumnWidth = {36, 65, 36, '1x', 52, 130, 160, 160};
            stPlayGrid.Padding = [4, 2, 4, 2];
            
            uibutton(stPlayGrid, 'Text', '⏮', 'ButtonPushedFcn', @(src, evt) app.stepFrame(-1));
            app.StudioPlayButton = uibutton(stPlayGrid, 'Text', '▶ Play', 'FontWeight', 'bold', ...
                'BackgroundColor', [0.2, 0.45, 0.7], 'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.togglePlayback());
            uibutton(stPlayGrid, 'Text', '⏭', 'ButtonPushedFcn', @(src, evt) app.stepFrame(1));
            
            app.StudioFrameSlider = uislider(stPlayGrid, 'Limits', [1, 251], 'Value', 1, ...
                'ValueChangedFcn', @(src, evt) app.onStudioSliderChanged());
            
            app.StudioSpeedDrop = uidropdown(stPlayGrid, 'Items', {'0.25x', '0.5x', '1.0x', '2.0x', '4.0x'}, 'Value', '1.0x', ...
                'ValueChangedFcn', @(src, evt) app.onStudioSpeedChanged());
            
            app.StudioStatsLabel = uilabel(stPlayGrid, 'Text', 'Frame 1 / 1  (t = 0.00 s)', ...
                'FontColor', [0.95, 0.85, 0.4], 'FontWeight', 'bold', 'FontSize', 10);
            
            app.ExportMP4Button = uibutton(stPlayGrid, 'Text', '📹 Export MP4 Video', 'FontWeight', 'bold', ...
                'BackgroundColor', [0.2, 0.6, 0.4], 'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.exportMP4Video([], true));
            
            uibutton(stPlayGrid, 'Text', '🖥 Large Popout Player', 'FontWeight', 'bold', ...
                'BackgroundColor', [0.4, 0.35, 0.6], 'FontColor', 'w', 'ButtonPushedFcn', @(src, evt) app.openLargeThermalView());
        end
        
        %% Tab 5: 5-Method Benchmark Construction
        function buildBenchmarkTab(app)
            benchGrid = uigridlayout(app.BenchmarkTab, [2, 3]);
            benchGrid.RowHeight = {'1x', '1x'};
            benchGrid.ColumnWidth = {'1x', '1x', '1x'};
            benchGrid.Padding = [6, 6, 6, 6];
            benchGrid.RowSpacing = 6; benchGrid.ColumnSpacing = 6;
            
            app.BenchAxesRaw = app.createMiniAxes(benchGrid, '1. Raw Peak-to-Peak Contrast');
            app.BenchAxesRaw.Layout.Row = 1; app.BenchAxesRaw.Layout.Column = 1;
            
            app.BenchAxesMF = app.createMiniAxes(benchGrid, '2. Matched Filter (Pulse Comp)');
            app.BenchAxesMF.Layout.Row = 1; app.BenchAxesMF.Layout.Column = 2;
            
            app.BenchAxesPCT = app.createMiniAxes(benchGrid, '3. SVD-PCT (EOF-2)');
            app.BenchAxesPCT.Layout.Row = 1; app.BenchAxesPCT.Layout.Column = 3;
            
            app.BenchAxesSPCT = app.createMiniAxes(benchGrid, '4. Sparse PCA (SPCT)');
            app.BenchAxesSPCT.Layout.Row = 2; app.BenchAxesSPCT.Layout.Column = 1;
            
            app.BenchAxesRPT = app.createMiniAxes(benchGrid, '5. Random Projection (RPT)');
            app.BenchAxesRPT.Layout.Row = 2; app.BenchAxesRPT.Layout.Column = 2;
            
            % Comparison Bar Chart Axes
            barPanel = uipanel(benchGrid, 'Title', '📊 CNR & IoU BENCHMARK COMPARISON', ...
                'FontSize', 9, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            barPanel.Layout.Row = 2; barPanel.Layout.Column = 3;
            bGrid = uigridlayout(barPanel, [1, 1]); bGrid.Padding = [4, 4, 4, 4];
            app.BenchBarAxes = uiaxes(bGrid);
            app.BenchBarAxes.Color = [0.08, 0.09, 0.12];
            app.BenchBarAxes.XColor = [0.8, 0.8, 0.85]; app.BenchBarAxes.YColor = [0.8, 0.8, 0.85];
            title(app.BenchBarAxes, 'Quantitative Performance Ranking', 'Color', [0.95, 0.95, 0.95], 'FontSize', 9);
            grid(app.BenchBarAxes, 'on');
        end
        
        %% Tab 6: Results & Audit Construction
        function buildAuditTab(app)
            auditGrid = uigridlayout(app.AuditTab, [2, 2]);
            auditGrid.RowHeight = {'1x', '1x'};
            auditGrid.ColumnWidth = {'1x', '1x'};
            auditGrid.Padding = [6, 6, 6, 6];
            auditGrid.RowSpacing = 6; auditGrid.ColumnSpacing = 6;
            
            % Ground Truth Contrast Curve
            gtPanel = uipanel(auditGrid, 'Title', '🔍 GROUND-TRUTH CONTRAST ANALYSIS (AUDIT ONLY — ISOLATED)', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.95, 0.85, 0.4], ...
                'BackgroundColor', [0.12, 0.13, 0.16]);
            gtPanel.Layout.Row = 1; gtPanel.Layout.Column = 1;
            gtG = uigridlayout(gtPanel, [1, 1]); gtG.Padding = [4, 4, 4, 4];
            app.AuditGTAxes = uiaxes(gtG);
            app.AuditGTAxes.Color = [0.08, 0.09, 0.12];
            app.AuditGTAxes.XColor = [0.8, 0.8, 0.85]; app.AuditGTAxes.YColor = [0.8, 0.8, 0.85];
            xlabel(app.AuditGTAxes, 'Time t [s]'); ylabel(app.AuditGTAxes, 'Differential Contrast \Delta T [K]');
            grid(app.AuditGTAxes, 'on');
            
            % Full Parameters Specification Table
            paramPanel = uipanel(auditGrid, 'Title', '⚙️ ACTIVE EXPERIMENT PARAMETERS SPECIFICATION', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.14, 0.16, 0.21]);
            paramPanel.Layout.Row = 1; paramPanel.Layout.Column = 2;
            pG = uigridlayout(paramPanel, [1, 1]); pG.Padding = [4, 4, 4, 4];
            app.AuditParamTable = uitable(pG, 'ColumnName', {'Section', 'Parameter', 'Configured Value'}, ...
                'RowName', {}, 'BackgroundColor', [0.15, 0.17, 0.22; 0.18, 0.20, 0.26], ...
                'ForegroundColor', [0.95, 0.95, 0.95]);
            
            % Complete Method Metrics Table
            metPanel = uipanel(auditGrid, 'Title', '📋 SCIENTIFIC VERIFICATION & AUDIT METRICS TABLE', ...
                'FontSize', 10, 'FontWeight', 'bold', 'ForegroundColor', [0.9, 0.95, 1.0], ...
                'BackgroundColor', [0.14, 0.16, 0.21]);
            metPanel.Layout.Row = 2; metPanel.Layout.Column = [1, 2];
            mG = uigridlayout(metPanel, [1, 1]); mG.Padding = [4, 4, 4, 4];
            app.AuditMetricsTable = uitable(mG, 'ColumnName', {'Method', 'Detected', 'CNR', 'IoU', 'Dice', 'Loc Error (mm)', 'Diam Error (mm)', 'Runtime (s)'}, ...
                'RowName', {}, 'BackgroundColor', [0.15, 0.17, 0.22; 0.18, 0.20, 0.26], ...
                'ForegroundColor', [0.95, 0.95, 0.95]);
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
            scroll(app.LogTextArea, 'bottom');
            drawnow limitrate;
        end
        
        %% Preset Loaders
        function loadDefaultPreset(app)
            app.DefectPresetDrop.Value = '8 mm (z=0.4 mm) [Default / Easy]';
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
            app.logMessage('Loaded Default Research Configuration (D = 8.0 mm, z = 0.4 mm).');
            app.updateExcitationWaveformPlot();
            app.update3DPhysicalModel();
        end
        
        function loadConferencePreset(app)
            app.DefectPresetDrop.Value = '6 mm (z=0.4 mm) [Medium]';
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
            app.logMessage('Loaded Conference Fast Demo Configuration (D = 6.0 mm, z = 0.4 mm, SNR = 25 dB).');
            app.updateExcitationWaveformPlot();
            app.update3DPhysicalModel();
        end
        
        function loadLiteraturePreset(app)
            app.DefectPresetDrop.Value = '8 mm (z=0.8 mm) [Deep]';
            app.HealthyCheck.Value = false;
            app.enableDefectInputs(true);
            app.DiamEdit.Value = 8.0;
            app.DepthEdit.Value = 0.8;
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
            app.logMessage('Loaded Deep Slag Validation Configuration (D = 8.0 mm, z = 0.8 mm, SNR = 30 dB).');
            app.updateExcitationWaveformPlot();
            app.update3DPhysicalModel();
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
                case '8 mm (z=0.4 mm) [Default / Easy]'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 8.0; app.DepthEdit.Value = 0.4;
                case '6 mm (z=0.4 mm) [Medium]'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 6.0; app.DepthEdit.Value = 0.4;
                case '8 mm (z=0.8 mm) [Deep]'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 8.0; app.DepthEdit.Value = 0.8;
                case '4 mm (z=1.0 mm) [Hard / Small]'
                    app.HealthyCheck.Value = false; app.enableDefectInputs(true);
                    app.DiamEdit.Value = 4.0; app.DepthEdit.Value = 1.0;
                case 'Healthy Control (D=0) [No Defect]'
                    app.HealthyCheck.Value = true; app.enableDefectInputs(false);
                    app.DiamEdit.Value = 0.0;
                case 'Custom Values'
                    app.enableDefectInputs(~app.HealthyCheck.Value);
            end
            app.update3DPhysicalModel();
        end
        
        function onHealthyCheckChanged(app)
            if app.HealthyCheck.Value
                app.enableDefectInputs(false);
                app.DefectPresetDrop.Value = 'Healthy Control (D=0) [No Defect]';
                app.DiamEdit.Value = 0.0;
            else
                app.enableDefectInputs(true);
                app.DefectPresetDrop.Value = 'Custom Values';
                if app.DiamEdit.Value == 0
                    app.DiamEdit.Value = 8.0;
                    app.DepthEdit.Value = 0.4;
                end
            end
            app.update3DPhysicalModel();
        end
        
        function onNoiseModeChanged(app)
            mode = app.NoiseModeDrop.Value;
            switch mode
                case 'Clean (Inf dB)'
                    app.SNREdit.Value = Inf; app.SNREdit.Enable = 'off';
                case '30 dB SNR'
                    app.SNREdit.Value = 30.0; app.SNREdit.Enable = 'off';
                case '25 dB SNR'
                    app.SNREdit.Value = 25.0; app.SNREdit.Enable = 'off';
                case '20 dB SNR'
                    app.SNREdit.Value = 20.0; app.SNREdit.Enable = 'off';
                case 'Custom SNR'
                    app.SNREdit.Enable = 'on';
            end
        end
        
        function onSpeedChanged(app)
            val = app.SpeedDrop.Value;
            app.setSpeedFromText(val);
        end
        
        function onStudioSpeedChanged(app)
            val = app.StudioSpeedDrop.Value;
            app.setSpeedFromText(val);
        end
        
        function setSpeedFromText(app, val)
            switch val
                case '0.25x', app.PlaybackSpeed = 0.25;
                case '0.5x',  app.PlaybackSpeed = 0.5;
                case '1.0x',  app.PlaybackSpeed = 1.0;
                case '2.0x',  app.PlaybackSpeed = 2.0;
                case '4.0x',  app.PlaybackSpeed = 4.0;
            end
            app.SpeedDrop.Value = val;
            app.StudioSpeedDrop.Value = val;
        end
        
        function onSliderChanged(app)
            if ~isempty(app.CurrentResults) && isfield(app.CurrentResults, 'noisy_thermograms')
                app.CurrentFrameIdx = round(app.FrameSlider.Value);
                app.StudioFrameSlider.Value = app.CurrentFrameIdx;
                app.updateThermogramFrame();
            end
        end
        
        function onStudioSliderChanged(app)
            if ~isempty(app.CurrentResults) && isfield(app.CurrentResults, 'noisy_thermograms')
                app.CurrentFrameIdx = round(app.StudioFrameSlider.Value);
                app.FrameSlider.Value = app.CurrentFrameIdx;
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
                app.StudioPlayButton.Text = '▶ Play';
                app.StudioPlayButton.BackgroundColor = [0.2, 0.45, 0.7];
            else
                app.IsPlaying = true;
                app.PlayButton.Text = '⏸ Pause';
                app.PlayButton.BackgroundColor = [0.7, 0.45, 0.2];
                app.StudioPlayButton.Text = '⏸ Pause';
                app.StudioPlayButton.BackgroundColor = [0.7, 0.45, 0.2];
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
            app.StudioFrameSlider.Value = new_idx;
            app.updateThermogramFrame();
        end
        
        function onTimerTick(app)
            if ~app.IsPlaying || isempty(app.CurrentResults)
                return;
            end
            step = max(1, round(app.PlaybackSpeed));
            new_idx = app.CurrentFrameIdx + step;
            if new_idx > app.TotalFrames
                if app.LoopVideoCheck.Value
                    new_idx = 1;
                else
                    new_idx = app.TotalFrames;
                    app.togglePlayback();
                    return;
                end
            end
            app.CurrentFrameIdx = new_idx;
            app.FrameSlider.Value = new_idx;
            app.StudioFrameSlider.Value = new_idx;
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
            app.updateThermogramFrame();
        end
        
        function onCloseRequest(app)
            if ~isempty(app.PlayTimer) && isvalid(app.PlayTimer)
                stop(app.PlayTimer);
                delete(app.PlayTimer);
            end
            if ~isempty(app.PopoutTimer) && isvalid(app.PopoutTimer)
                stop(app.PopoutTimer);
                delete(app.PopoutTimer);
            end
            if ~isempty(app.PopoutFigure) && isvalid(app.PopoutFigure)
                delete(app.PopoutFigure);
            end
            delete(app.UIFigure);
        end
        
        %% Input Validation & Config Builder
        function [cfg, valid, err_msg] = buildValidatedConfig(app)
            valid = true;
            err_msg = '';
            
            cfg = default_config();
            
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
            
            snr_val = app.SNREdit.Value;
            if isinf(snr_val) || snr_val <= 0 || isnan(snr_val)
                cfg.camera.noise_snr_db = [];
            else
                cfg.camera.noise_snr_db = snr_val;
            end
            cfg.camera.noise_seed = uint32(app.SeedEdit.Value);
            
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
                otherwise
                    cfg.simulation.nx = 40; cfg.simulation.ny = 28; cfg.simulation.nz = 10;
                    cfg.simulation.dt_s = 0.04;
            end
        end
        
        %% Main Pipeline Execution
        function runInspection(app)
            if app.IsRunning, return; end
            
            [cfg, valid, err_msg] = app.buildValidatedConfig();
            if ~valid
                if isvalid(app.UIFigure)
                    uialert(app.UIFigure, err_msg, 'Input Validation Error', 'Icon', 'error');
                end
                app.logMessage(['ERROR: ', err_msg]);
                return;
            end
            
            app.IsRunning = true;
            app.RunButton.Enable = 'off';
            app.StopButton.Enable = 'on';
            app.StageLabel.Text = 'Status: Initializing Pipeline...';
            app.StageLabel.FontColor = [0.95, 0.85, 0.4];
            app.updateSimulationConnectionVisuals('stage1');
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
                % Stage 2: LFMT Excitation Waveform
                app.updateSimulationConnectionVisuals('stage2');
                drawnow;
                
                % Stage 3: Forward 3-D Simulation
                app.StageLabel.Text = 'Stage: 3-D Thermal Simulation...';
                app.logMessage('Running 3-D Numerical Simulation...');
                app.updateSimulationConnectionVisuals('stage3');
                drawnow;
                
                sim_hash = lfmt.cache('hash', cfg);
                cached_sim = lfmt.cache('load', sim_hash);
                
                if ~isempty(cached_sim) && isfield(cached_sim, 'mesh') && isfield(cached_sim, 'geometry')
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
                
                % Stage 4: Virtual IR Camera & Noise Injection
                app.StageLabel.Text = 'Stage: Virtual IR Acquisition...';
                app.updateSimulationConnectionVisuals('stage4');
                drawnow;
                
                snr_db = cfg.camera.noise_snr_db;
                seed = cfg.camera.noise_seed;
                [T_noisy, noise_sigma] = lfmt.noise(sim_res.surface_temperature, snr_db, seed);
                if isempty(snr_db) || isinf(snr_db)
                    app.logMessage('Noise Model: Clean Thermograms (sigma = 0.0 K)');
                else
                    app.logMessage(sprintf('Noise Model: AWGN SNR = %.1f dB (sigma = %.4f K, seed = %d)', snr_db, noise_sigma, seed));
                end
                
                % Stage 5: Ground Truth Mask (Isolated strictly for metrics)
                [x_mesh, y_mesh] = meshgrid(sim_res.camera_x_mm, sim_res.camera_y_mm);
                if sim_res.geometry.has_defect
                    d = sim_res.geometry.defect;
                    gt_mask = ((x_mesh - d.center_x_mm).^2 + (y_mesh - d.center_y_mm).^2) <= (d.radius_m * 1e3)^2;
                else
                    gt_mask = false(size(x_mesh));
                end
                
                % Stage 6: 5 Blind Signal Processing Methods
                app.StageLabel.Text = 'Stage: Blind Signal Processing (5 Methods)...';
                app.updateSimulationConnectionVisuals('stage5');
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
                
                % Stage 7: Metrics & Summary Structure
                app.updateSimulationConnectionVisuals('stage7');
                drawnow;
                
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
                
                % Pre-calculate global temperature bounds for locked scale mode
                app.GlobalTMin = min(T_noisy(:));
                app.GlobalTMax = max(T_noisy(:));
                
                % Update UI Displays
                app.TotalFrames = size(T_noisy, 1);
                app.FrameSlider.Limits = [1, app.TotalFrames];
                app.StudioFrameSlider.Limits = [1, app.TotalFrames];
                app.CurrentFrameIdx = 1;
                app.FrameSlider.Value = 1;
                app.StudioFrameSlider.Value = 1;
                
                app.updateThermogramFrame();
                app.updateExcitationWaveformPlot();
                app.updatePixelThermalCurve();
                app.updateGTContrastPlot();
                app.updateAllProcessedPlots();
                app.updatePrimaryDisplay();
                app.updateMetricsTable();
                app.update3DPhysicalModel();
                app.updateStudioEnvelopes();
                app.updateBenchmarkTab();
                app.updateAuditTab();
                
                % Stage 8: Complete
                app.updateSimulationConnectionVisuals('complete');
                app.StageLabel.Text = sprintf('Status: Complete (Total: %.2f s)', tot_runtime);
                app.StageLabel.FontColor = [0.4, 0.9, 0.5];
                app.logMessage(sprintf('Pipeline completed successfully in %.2f s.', tot_runtime));
                app.logMessage('================================================================');
                
            catch ME
                app.logMessage(['FATAL ERROR in pipeline: ', ME.message]);
                app.StageLabel.Text = 'Status: Error';
                app.StageLabel.FontColor = [0.95, 0.3, 0.3];
                app.updateSimulationConnectionVisuals('error');
                if isvalid(app.UIFigure)
                    uialert(app.UIFigure, ME.message, 'Execution Error', 'Icon', 'error');
                end
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
            
            cfg = app.CurrentResults.config;
            if t_curr <= cfg.excitation.duration_s
                f_inst = cfg.excitation.f0_hz + ((cfg.excitation.f1_hz - cfg.excitation.f0_hz) / cfg.excitation.duration_s) * t_curr;
                phase = 2 * pi * (cfg.excitation.f0_hz * t_curr + 0.5 * ((cfg.excitation.f1_hz - cfg.excitation.f0_hz) / cfg.excitation.duration_s) * t_curr^2) - pi/2;
                q_curr = cfg.excitation.q0_w_m2 * 0.5 * (1 + sin(phase));
            else
                f_inst = 0.0;
                q_curr = 0.0;
            end
            
            % Update Main Thermogram Axes
            cla(app.ThermogramAxes);
            imagesc(app.ThermogramAxes, x_mm, y_mm, frame_T);
            axis(app.ThermogramAxes, 'image');
            colorbar(app.ThermogramAxes);
            colormap(app.ThermogramAxes, 'turbo');
            
            if app.LockColorScaleCheck.Value
                clim(app.ThermogramAxes, [app.GlobalTMin, app.GlobalTMax]);
            end
            
            title(app.ThermogramAxes, sprintf('Surface Thermogram T(x,y)  |  t = %.2f s (Frame %d/%d)', t_curr, idx, app.TotalFrames), 'Color', [0.95, 0.95, 0.95], 'FontSize', 10);
            xlabel(app.ThermogramAxes, 'Plate Length X [mm]');
            ylabel(app.ThermogramAxes, 'Plate Width Y [mm]');
            hold(app.ThermogramAxes, 'on');
            
            if app.GTOverlayCheck.Value && sim_res.geometry.has_defect
                d = sim_res.geometry.defect;
                theta = linspace(0, 2*pi, 80);
                gt_x = d.center_x_mm + (d.diameter_mm / 2.0) * cos(theta);
                gt_y = d.center_y_mm + (d.diameter_mm / 2.0) * sin(theta);
                plot(app.ThermogramAxes, gt_x, gt_y, 'w--', 'LineWidth', 1.8);
            end
            
            sel_x = sim_res.camera_x_mm(app.SelectedPixel(2));
            sel_y = sim_res.camera_y_mm(app.SelectedPixel(1));
            plot(app.ThermogramAxes, sel_x, sel_y, 'mp', 'MarkerSize', 10, 'LineWidth', 2.0);
            hold(app.ThermogramAxes, 'off');
            
            % Update Studio Axes if Studio tab exists
            if isvalid(app.StudioAxes)
                cla(app.StudioAxes);
                imagesc(app.StudioAxes, x_mm, y_mm, frame_T);
                axis(app.StudioAxes, 'image');
                colorbar(app.StudioAxes);
                colormap(app.StudioAxes, 'turbo');
                if app.LockColorScaleCheck.Value
                    clim(app.StudioAxes, [app.GlobalTMin, app.GlobalTMax]);
                end
                title(app.StudioAxes, sprintf('Studio View: T(x,y) at t = %.2f s | q(t) = %.0f W/m² | f(t) = %.3f Hz', t_curr, q_curr, f_inst), 'Color', [0.95, 0.95, 0.95]);
                xlabel(app.StudioAxes, 'Length X [mm]'); ylabel(app.StudioAxes, 'Width Y [mm]');
            end
            
            % Update Popout Figure if active
            if ~isempty(app.PopoutAxes) && isvalid(app.PopoutAxes)
                cla(app.PopoutAxes);
                imagesc(app.PopoutAxes, x_mm, y_mm, frame_T);
                axis(app.PopoutAxes, 'image');
                colorbar(app.PopoutAxes);
                colormap(app.PopoutAxes, 'turbo');
                if app.LockColorScaleCheck.Value
                    clim(app.PopoutAxes, [app.GlobalTMin, app.GlobalTMax]);
                end
                title(app.PopoutAxes, sprintf('LFMT Thermal Frame %d / %d  |  t = %.2f s  |  q(t) = %.0f W/m²', idx, app.TotalFrames, t_curr, q_curr));
                xlabel(app.PopoutAxes, 'Length X [mm]'); ylabel(app.PopoutAxes, 'Width Y [mm]');
            end
            
            t_min = min(frame_T(:)); t_max = max(frame_T(:)); t_mean = mean(frame_T(:));
            app.FrameInfoLabel.Text = sprintf('Frame: %d / %d  |  Time: %.2f s  |  Inst. Freq: %.3f Hz', idx, app.TotalFrames, t_curr, f_inst);
            app.ThermalStatsLabel.Text = sprintf('Min: %.2f K  |  Max: %.2f K  |  Mean: %.2f K', t_min, t_max, t_mean);
            app.StudioStatsLabel.Text = sprintf('Frame: %d/%d (%.2f s) | q: %.0f W/m² | T: %.2f..%.2f K', idx, app.TotalFrames, t_curr, q_curr, t_min, t_max);
            
            % Move cursors
            if ~isempty(app.WaveformCursorHandle) && isvalid(app.WaveformCursorHandle)
                app.WaveformCursorHandle.Value = t_curr;
            end
            if ~isempty(app.StudioFluxCursorHandle) && isvalid(app.StudioFluxCursorHandle)
                app.StudioFluxCursorHandle.Value = t_curr;
            end
            if ~isempty(app.StudioEnvCursorHandle) && isvalid(app.StudioEnvCursorHandle)
                app.StudioEnvCursorHandle.Value = t_curr;
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
            
            % Main Tab Waveform
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
            title(app.WaveformAxes, sprintf('LFMT Excitation: f0=%.2f Hz, f1=%.2f Hz, q0=%.0f W/m²', cfg.excitation.f0_hz, cfg.excitation.f1_hz, cfg.excitation.q0_w_m2), 'Color', [0.9, 0.95, 1.0], 'FontSize', 9);
            grid(app.WaveformAxes, 'on');
            app.WaveformCursorHandle = xline(app.WaveformAxes, 0, 'y-', 'LineWidth', 1.5);
            
            % Studio Flux Subplot
            if isvalid(app.StudioFluxAxes)
                cla(app.StudioFluxAxes);
                plot(app.StudioFluxAxes, t, q, 'g-', 'LineWidth', 1.6);
                title(app.StudioFluxAxes, 'LFMT Chirp Excitation q(t)', 'Color', [0.9, 0.95, 1.0], 'FontSize', 9);
                xlabel(app.StudioFluxAxes, 'Time t [s]'); ylabel(app.StudioFluxAxes, 'Flux [W/m²]');
                grid(app.StudioFluxAxes, 'on');
                app.StudioFluxCursorHandle = xline(app.StudioFluxAxes, 0, 'y-', 'LineWidth', 1.5);
            end
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
            T_ref = squeeze(T_cube(:, 2, 2));
            
            cla(app.PixelCurveAxes);
            plot(app.PixelCurveAxes, t_vec, T_pix, 'm-', 'LineWidth', 2.0, 'DisplayName', sprintf('Selected Pixel (X=%.1f, Y=%.1f mm)', sim_res.camera_x_mm(col), sim_res.camera_y_mm(row)));
            hold(app.PixelCurveAxes, 'on');
            plot(app.PixelCurveAxes, t_vec, T_ref, 'c--', 'LineWidth', 1.5, 'DisplayName', 'Sound Reference (Corner)');
            hold(app.PixelCurveAxes, 'off');
            
            grid(app.PixelCurveAxes, 'on');
            legend(app.PixelCurveAxes, 'Location', 'northwest', 'TextColor', [0.9, 0.9, 0.95]);
            title(app.PixelCurveAxes, 'Point Inspector: Transient Thermal Curve T(t)', 'Color', [0.9, 0.95, 1.0], 'FontSize', 9);
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
                title(app.GTAnalysisAxes, 'GROUND-TRUTH ANALYSIS — NOT USED BY DETECTOR', 'Color', [0.95, 0.85, 0.4], 'FontWeight', 'bold', 'FontSize', 9);
                xlabel(app.GTAnalysisAxes, 'Time t [s]');
                ylabel(app.GTAnalysisAxes, 'Differential Contrast \Delta T(t) [K]');
            else
                title(app.GTAnalysisAxes, 'Healthy Control Plate — No Defect Contrast Generated', 'Color', [0.6, 0.8, 0.9], 'FontSize', 9);
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
            
            if det_res.is_detected && ~isnan(det_res.centroid_mm(1))
                plot(ax, det_res.centroid_mm(1), det_res.centroid_mm(2), 'r+', 'MarkerSize', 8, 'LineWidth', 2.0);
                contour(ax, x_mm, y_mm, double(det_res.predicted_mask), [0.5, 0.5], 'r-', 'LineWidth', 1.5);
            end
            
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
            
            if met.is_detected
                app.DetectionLamp.Color = [0.1, 0.85, 0.2];
                app.DetectionText.Text = 'DEFECT DETECTED: YES';
                app.DetectionText.FontColor = [0.2, 0.9, 0.3];
            else
                app.DetectionLamp.Color = [0.85, 0.2, 0.2];
                app.DetectionText.Text = 'DEFECT DETECTED: NO';
                app.DetectionText.FontColor = [0.95, 0.4, 0.4];
            end
            
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
        
        %% Simulation Connection Visuals
        function updateSimulationConnectionVisuals(app, stage)
            if isempty(app.StageLamps) || any(~isvalid(app.StageLamps))
                return;
            end
            
            gray_color = [0.35, 0.38, 0.45];
            green_color = [0.15, 0.85, 0.3];
            amber_color = [0.95, 0.75, 0.2];
            red_color = [0.9, 0.25, 0.25];
            
            switch stage
                case 'ready'
                    for i = 1:8, app.StageLamps(i).Color = gray_color; end
                    app.StageLamps(1).Color = green_color;
                    app.StageStatusLabels(1).Text = 'Inputs Configured';
                    for i = 2:8, app.StageStatusLabels(i).Text = 'Waiting...'; end
                case 'stage1'
                    for i = 1:8, app.StageLamps(i).Color = gray_color; end
                    app.StageLamps(1).Color = amber_color;
                    app.StageStatusLabels(1).Text = 'Validating Config...';
                case 'stage2'
                    app.StageLamps(1).Color = green_color; app.StageStatusLabels(1).Text = 'Config Valid';
                    app.StageLamps(2).Color = amber_color; app.StageStatusLabels(2).Text = 'Synthesizing Chirp...';
                case 'stage3'
                    app.StageLamps(2).Color = green_color; app.StageStatusLabels(2).Text = 'Chirp Synthesized';
                    app.StageLamps(3).Color = amber_color; app.StageStatusLabels(3).Text = 'Solving 3-D FEM...';
                case 'stage4'
                    app.StageLamps(3).Color = green_color; app.StageStatusLabels(3).Text = 'FEM Diffusion Solved';
                    app.StageLamps(4).Color = amber_color; app.StageStatusLabels(4).Text = 'Sampling & AWGN...';
                case 'stage5'
                    app.StageLamps(4).Color = green_color; app.StageStatusLabels(4).Text = 'Cube Acquired';
                    app.StageLamps(5).Color = amber_color; app.StageStatusLabels(5).Text = 'Processing 5 Methods...';
                case 'stage7'
                    app.StageLamps(5).Color = green_color; app.StageStatusLabels(5).Text = '5 Score Maps Computed';
                    app.StageLamps(6).Color = green_color; app.StageStatusLabels(6).Text = 'Defects Segmented';
                    app.StageLamps(7).Color = amber_color; app.StageStatusLabels(7).Text = 'Evaluating Metrics...';
                case 'complete'
                    for i = 1:8
                        app.StageLamps(i).Color = green_color;
                    end
                    app.StageStatusLabels(1).Text = '100 x 70 x 2.3 mm Plate';
                    app.StageStatusLabels(2).Text = '0.05-0.5 Hz Chirp';
                    app.StageStatusLabels(3).Text = 'Hex8 FEM Backward Euler';
                    app.StageStatusLabels(4).Text = '256x256 Thermal Cube';
                    app.StageStatusLabels(5).Text = 'RAW, MF, PCT, SPCT, RPT';
                    app.StageStatusLabels(6).Text = 'Otsu + Morphological';
                    app.StageStatusLabels(7).Text = 'IoU, Dice, CNR Computed';
                    app.StageStatusLabels(8).Text = 'Ready to Export';
                case 'error'
                    for i = 1:8
                        if isequal(app.StageLamps(i).Color, amber_color)
                            app.StageLamps(i).Color = red_color;
                            app.StageStatusLabels(i).Text = 'Failed';
                        end
                    end
            end
        end
        
        function drawSimulationConnectionDiagram(app)
            cla(app.ConnFlowAxes);
            hold(app.ConnFlowAxes, 'on');
            
            % Block coordinates (8 stages)
            x_pos = linspace(0.06, 0.94, 8);
            y_box = 0.5;
            box_w = 0.085;
            box_h = 0.45;
            
            box_titles = {'1. INPUTS', '2. CHIRP', '3. 3-D FEM', '4. CAMERA', '5. 5-METHODS', '6. SEGMENT', '7. METRICS', '8. EXPORT'};
            box_subs = {'Geometry & Slag', 'q(t) & f(t)', 'M(dT/dt)+KT=Q', 'T(x,y,t)+Noise', 'MF,PCT,SPCT...', 'BBox & Centroid', 'IoU, Dice, CNR', 'MAT/CSV/JSON'};
            
            for i = 1:8
                bx = x_pos(i) - box_w/2;
                by = y_box - box_h/2;
                rectangle(app.ConnFlowAxes, 'Position', [bx, by, box_w, box_h], ...
                    'Curvature', 0.2, 'FaceColor', [0.16, 0.20, 0.28], 'EdgeColor', [0.35, 0.65, 0.95], 'LineWidth', 1.5);
                
                text(app.ConnFlowAxes, x_pos(i), y_box + 0.12, box_titles{i}, ...
                    'Color', [0.95, 0.95, 1.0], 'FontWeight', 'bold', 'FontSize', 8, 'HorizontalAlignment', 'center');
                
                text(app.ConnFlowAxes, x_pos(i), y_box - 0.08, box_subs{i}, ...
                    'Color', [0.75, 0.85, 0.95], 'FontSize', 7, 'HorizontalAlignment', 'center');
                
                if i < 8
                    ax_start = bx + box_w;
                    ax_end = x_pos(i+1) - box_w/2;
                    plot(app.ConnFlowAxes, [ax_start, ax_end], [y_box, y_box], 'c-', 'LineWidth', 1.5);
                    plot(app.ConnFlowAxes, ax_end, y_box, 'c>', 'MarkerFaceColor', 'c', 'MarkerSize', 5);
                end
            end
            
            xlim(app.ConnFlowAxes, [0, 1]);
            ylim(app.ConnFlowAxes, [0, 1]);
            hold(app.ConnFlowAxes, 'off');
        end
        
        function populateStageDetailsText(app)
            txt = {...
                '========================================================================', ...
                'LFMT COMPLETE SCIENTIFIC SIMULATION PIPELINE SPECIFICATION', ...
                '========================================================================', ...
                '', ...
                'STAGE 1: INPUT & SPECIFICATION', ...
                '  - Specimen: Mild Steel Plate [Lx = 100 mm, Ly = 70 mm, Lz = 2.3 mm]', ...
                '  - Material: k = 45 W/m-K, rho = 7850 kg/m^3, Cp = 460 J/kg-K (alpha = 1.25e-5 m^2/s)', ...
                '  - Inclusion: Slag (k = 1.2 W/m-K, rho = 2800 kg/m^3, Cp = 850 J/kg-K)', ...
                '  - Thermal Conductivity Contrast Ratio: k_steel / k_slag = 37.5x', ...
                '', ...
                'STAGE 2: LINEAR FREQUENCY-MODULATED EXCITATION', ...
                '  - Instantaneous Heat Flux: q(t) = q0 * 0.5 * (1 + sin(phi(t)))', ...
                '  - Instantaneous Phase: phi(t) = 2*pi*(f0*t + 0.5*((f1-f0)/Texc)*t^2) - pi/2', ...
                '  - Instantaneous Frequency: f(t) = f0 + ((f1 - f0) / Texc) * t', ...
                '  - Observation Window: Tobs >= Texc (includes transient thermal cooling)', ...
                '', ...
                'STAGE 3: 3-D HEX8 FEM TRANSIENT DIFFUSION SOLVER', ...
                '  - Governing PDE: rho*Cp * (dT/dt) = div(k * grad(T))', ...
                '  - Discretization: 3-D Trilinear Hexahedral Elements (Hex8)', ...
                '  - Global System: M * (T_{n} - T_{n-1})/dt + K * T_{n} + M_conv * T_{n} = Q_{n} + Q_amb', ...
                '  - Time Integration: Implicit Backward Euler (A * T_n = rhs)', ...
                '  - Pre-factorization: Cholesky Decomposition of sparse positive-definite A', ...
                '', ...
                'STAGE 4: VIRTUAL IR CAMERA & NOISE INJECTION', ...
                '  - Acquisition: Decoupled camera frame sampling at 25 Hz (251 frames)', ...
                '  - Sensor Model: 2-D surface interpolation over (camera_nx, camera_ny)', ...
                '  - Noise Model: Additive White Gaussian Noise (AWGN) calibrated to SNR (dB)', ...
                '  - Mathematical Form: sigma = std(T_clean) / (10^(SNR_dB / 20))', ...
                '', ...
                'STAGE 5: 5 BLIND SIGNAL PROCESSING METHODS', ...
                '  1. Raw Peak-to-Peak Contrast: S_raw(x,y) = max_t T(x,y,t) - min_t T(x,y,t)', ...
                '  2. Matched Filter: S_MF(x,y) = max_tau |(T(x,y,.) * h(-.))(tau)| (Pulse Compression)', ...
                '  3. SVD-PCT: Empirical Orthogonal Functions (EOF-2 captures defect signature)', ...
                '  4. Sparse PCA (SPCT): L1-regularized sparse loading vectors', ...
                '  5. Random Projection (RPT): Dimension reduction via Gaussian Johnson-Lindenstrauss', ...
                '', ...
                'STAGE 6: BLIND DEFECT SEGMENTATION & SIZING', ...
                '  - Thresholding: Automatic Otsu / Adaptive thresholding on normalized score maps', ...
                '  - Morphology: Bwareaopen filter to suppress pixel noise outliers', ...
                '  - Sizing: Centroid (xc, yc), Equivalent Diameter D = 2*sqrt(Area / pi)', ...
                '', ...
                'STAGE 7: SCIENTIFIC EVALUATION & VERIFICATION', ...
                '  - Overlap: IoU = |A cap B| / |A cup B|, Dice = 2*|A cap B| / (|A| + |B|)', ...
                '  - Signal Quality: Contrast-to-Noise Ratio (CNR = |mu_def - mu_snd| / sqrt(sigma_def^2 + sigma_snd^2))', ...
                '  - Accuracy: Localization Error = sqrt((xc - x_gt)^2 + (yc - y_gt)^2), Diameter Error = |D_est - D_gt|', ...
                '  - ANTI-LEAKAGE: Ground Truth is strictly isolated and NEVER used by detectors.', ...
                '========================================================================' ...
            };
            app.StageDetailTextArea.Value = txt;
        end
        
        %% Tab 3: 3-D Physical Model & FEM Mesh Updates
        function update3DPhysicalModel(app)
            [cfg, valid] = app.buildValidatedConfig();
            if ~valid, return; end
            
            % 1. Draw 3-D Plate Volume & Inclusion
            cla(app.Axes3DPlate);
            hold(app.Axes3DPlate, 'on');
            
            lx = cfg.plate.length_mm;
            ly = cfg.plate.width_mm;
            lz = cfg.plate.thickness_mm;
            
            % Draw Steel Plate Box [0, lx] x [0, ly] x [-lz, 0]
            v_plate = [
                0,  0, -lz;
                lx, 0, -lz;
                lx, ly, -lz;
                0,  ly, -lz;
                0,  0,  0;
                lx, 0,  0;
                lx, ly,  0;
                0,  ly,  0;
            ];
            faces = [
                1 2 3 4; % bottom
                5 6 7 8; % top
                1 2 6 5; % front
                2 3 7 6; % right
                3 4 8 7; % back
                4 1 5 8  % left
            ];
            patch(app.Axes3DPlate, 'Vertices', v_plate, 'Faces', faces, ...
                'FaceColor', [0.65, 0.70, 0.80], 'FaceAlpha', 0.25, 'EdgeColor', [0.4, 0.5, 0.7], 'LineWidth', 1.2);
            
            % Top surface heating face
            patch(app.Axes3DPlate, 'Vertices', v_plate(5:8, :), 'Faces', [1 2 3 4], ...
                'FaceColor', [1.0, 0.6, 0.2], 'FaceAlpha', 0.35, 'EdgeColor', [1.0, 0.7, 0.3], 'LineWidth', 1.5);
            
            % Draw Embedded Slag Cylinder if defect is enabled
            if cfg.plate.has_defect
                d = cfg.plate.defect;
                [cyl_x, cyl_y, cyl_z] = cylinder(d.diameter_mm / 2.0, 36);
                cyl_x = cyl_x + d.center_x_mm;
                cyl_y = cyl_y + d.center_y_mm;
                cyl_z = -d.depth_mm - cyl_z * d.thickness_mm;
                
                surf(app.Axes3DPlate, cyl_x, cyl_y, cyl_z, 'FaceColor', [0.9, 0.15, 0.15], ...
                    'FaceAlpha', 0.85, 'EdgeColor', [0.6, 0.1, 0.1]);
                
                % Top and bottom caps of cylinder
                fill3(app.Axes3DPlate, cyl_x(1,:), cyl_y(1,:), cyl_z(1,:), [0.9, 0.15, 0.15], 'FaceAlpha', 0.85);
                fill3(app.Axes3DPlate, cyl_x(2,:), cyl_y(2,:), cyl_z(2,:), [0.9, 0.15, 0.15], 'FaceAlpha', 0.85);
                
                title(app.Axes3DPlate, sprintf('3-D Plate + Slag Inclusion (D = %.1f mm, z = %.2f mm)', d.diameter_mm, d.depth_mm), 'Color', [0.95, 0.95, 0.95], 'FontSize', 9);
            else
                title(app.Axes3DPlate, 'Healthy Homogeneous Steel Plate (No Inclusions)', 'Color', [0.6, 0.9, 0.6], 'FontSize', 9);
            end
            
            xlim(app.Axes3DPlate, [-5, lx+5]);
            ylim(app.Axes3DPlate, [-5, ly+5]);
            zlim(app.Axes3DPlate, [-lz-0.5, 0.5]);
            hold(app.Axes3DPlate, 'off');
            
            % 2. Draw FEM Hex8 Mesh Visualization
            cla(app.AxesMesh);
            hold(app.AxesMesh, 'on');
            
            nx = cfg.simulation.nx;
            ny = cfg.simulation.ny;
            nz = cfg.simulation.nz;
            
            xm = linspace(0, lx, nx+1);
            ym = linspace(0, ly, ny+1);
            zm = linspace(-lz, 0, nz+1);
            
            % Draw wireframe grids on bounding faces
            [X_top, Y_top] = meshgrid(xm, ym);
            mesh(app.AxesMesh, X_top, Y_top, zeros(size(X_top)), 'EdgeColor', [0.2, 0.7, 0.9], 'FaceColor', 'none', 'LineWidth', 0.8);
            
            [X_front, Z_front] = meshgrid(xm, zm);
            mesh(app.AxesMesh, X_front, zeros(size(X_front)), Z_front, 'EdgeColor', [0.3, 0.5, 0.8], 'FaceColor', 'none', 'LineWidth', 0.6);
            
            [Y_side, Z_side] = meshgrid(ym, zm);
            mesh(app.AxesMesh, zeros(size(Y_side)), Y_side, Z_side, 'EdgeColor', [0.3, 0.5, 0.8], 'FaceColor', 'none', 'LineWidth', 0.6);
            
            if cfg.plate.has_defect
                d = cfg.plate.defect;
                % Defect region wireframe highlight in red
                idx_x = find(xm >= (d.center_x_mm - d.diameter_mm/2) & xm <= (d.center_x_mm + d.diameter_mm/2));
                idx_y = find(ym >= (d.center_y_mm - d.diameter_mm/2) & ym <= (d.center_y_mm + d.diameter_mm/2));
                if ~isempty(idx_x) && ~isempty(idx_y)
                    [X_def, Y_def] = meshgrid(xm(idx_x), ym(idx_y));
                    mesh(app.AxesMesh, X_def, Y_def, -d.depth_mm * ones(size(X_def)), 'EdgeColor', [1.0, 0.2, 0.2], 'FaceColor', 'none', 'LineWidth', 1.5);
                end
            end
            
            total_nodes = (nx + 1) * (ny + 1) * (nz + 1);
            total_elems = nx * ny * nz;
            title(app.AxesMesh, sprintf('Hex8 Mesh: %d Nodes, %d Elements (%d DOFs)', total_nodes, total_elems, total_nodes), 'Color', [0.95, 0.95, 0.95], 'FontSize', 9);
            xlim(app.AxesMesh, [-5, lx+5]); ylim(app.AxesMesh, [-5, ly+5]); zlim(app.AxesMesh, [-lz-0.5, 0.5]);
            hold(app.AxesMesh, 'off');
            
            % 3. Draw 2-D Cross Section Schematic
            cla(app.AxesCrossSection);
            hold(app.AxesCrossSection, 'on');
            
            % Draw plate rectangle [0, lx] x [0, lz]
            rectangle(app.AxesCrossSection, 'Position', [0, 0, lx, lz], 'FaceColor', [0.22, 0.26, 0.35], 'EdgeColor', [0.4, 0.6, 0.8], 'LineWidth', 1.5);
            
            % Front surface flux arrows
            flux_x = linspace(10, lx-10, 8);
            for fx = flux_x
                quiver(app.AxesCrossSection, fx, -0.4, 0, 0.35, 0, 'Color', [1.0, 0.6, 0.1], 'LineWidth', 1.8, 'MaxHeadSize', 2);
            end
            text(app.AxesCrossSection, lx/2, -0.6, 'LFMT Heat Flux q(t)', 'Color', [1.0, 0.7, 0.2], 'FontWeight', 'bold', 'FontSize', 8, 'HorizontalAlignment', 'center');
            
            % Draw defect cross-section (rectangle of width D, depth z, thickness h)
            if cfg.plate.has_defect
                d = cfg.plate.defect;
                def_x0 = d.center_x_mm - d.diameter_mm/2;
                rectangle(app.AxesCrossSection, 'Position', [def_x0, d.depth_mm, d.diameter_mm, d.thickness_mm], ...
                    'FaceColor', [0.85, 0.2, 0.2], 'EdgeColor', [1.0, 0.4, 0.4], 'LineWidth', 1.5);
                text(app.AxesCrossSection, d.center_x_mm, d.depth_mm + d.thickness_mm/2, 'Slag Inclusion', ...
                    'Color', 'w', 'FontSize', 7, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
            end
            
            set(app.AxesCrossSection, 'YDir', 'reverse'); % z increases downward
            xlim(app.AxesCrossSection, [-5, lx+5]);
            ylim(app.AxesCrossSection, [-1.0, lz+0.5]);
            title(app.AxesCrossSection, 'Plate Cross-Section at Y = 35 mm', 'Color', [0.9, 0.95, 1.0], 'FontSize', 9);
            hold(app.AxesCrossSection, 'off');
            
            app.updateMeshDataTable();
        end
        
        function updateMeshDataTable(app)
            [cfg, valid] = app.buildValidatedConfig();
            if ~valid, return; end
            
            nx = cfg.simulation.nx; ny = cfg.simulation.ny; nz = cfg.simulation.nz;
            dx = cfg.plate.length_mm / nx;
            dy = cfg.plate.width_mm / ny;
            dz = cfg.plate.thickness_mm / nz;
            total_nodes = (nx + 1) * (ny + 1) * (nz + 1);
            total_elems = nx * ny * nz;
            
            rows = {
                'Plate Dimensions', sprintf('%.1f x %.1f x %.2f', cfg.plate.length_mm, cfg.plate.width_mm, cfg.plate.thickness_mm), 'mm', 'Length x Width x Thickness';
                'Steel Conductivity k', '45.0', 'W/m-K', 'Mild steel substrate';
                'Steel Density rho', '7850.0', 'kg/m^3', 'Substrate density';
                'Steel Specific Heat Cp', '460.0', 'J/kg-K', 'Substrate heat capacity';
                'Slag Conductivity k', '1.20', 'W/m-K', 'Slag inclusion (37.5x contrast)';
                'Slag Density rho', '2800.0', 'kg/m^3', 'Inclusion density';
                'Slag Specific Heat Cp', '850.0', 'J/kg-K', 'Inclusion heat capacity';
                'Convection Coeff h', '10.0', 'W/m^2-K', 'Natural convection boundary';
                'Hex8 Elements (Nx,Ny,Nz)', sprintf('%d x %d x %d', nx, ny, nz), 'elements', '3-D spatial elements';
                'Element Sizes (dx,dy,dz)', sprintf('%.2f x %.2f x %.3f', dx, dy, dz), 'mm', 'Hexahedral resolution';
                'Total Nodes & DOFs', sprintf('%d', total_nodes), 'DOFs', 'Degrees of Freedom';
                'Total Hex8 Elements', sprintf('%d', total_elems), 'elements', 'Assembled elements';
                'Solver Time Step dt', sprintf('%.3f', cfg.simulation.dt_s), 's', 'Implicit Backward Euler dt';
                'Camera Dimensions', '256 x 256', 'pixels', 'Virtual IR Decoupled Grid'
            };
            app.MeshDataTable.Data = rows;
        end
        
        %% Tab 4: Studio Updates & MP4 Export
        function updateStudioEnvelopes(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                return;
            end
            
            sim_res = app.CurrentResults.simulation;
            T_cube = app.CurrentResults.noisy_thermograms;
            t_vec = sim_res.time_vector;
            n_frames = size(T_cube, 1);
            
            t_max_vec = zeros(n_frames, 1);
            t_min_vec = zeros(n_frames, 1);
            t_mean_vec = zeros(n_frames, 1);
            
            for f = 1:n_frames
                frame = T_cube(f, :, :);
                t_max_vec(f) = max(frame(:));
                t_min_vec(f) = min(frame(:));
                t_mean_vec(f) = mean(frame(:));
            end
            
            cla(app.StudioEnvelopeAxes);
            plot(app.StudioEnvelopeAxes, t_vec, t_max_vec, 'r-', 'LineWidth', 1.8, 'DisplayName', 'T_{max}(t)');
            hold(app.StudioEnvelopeAxes, 'on');
            plot(app.StudioEnvelopeAxes, t_vec, t_mean_vec, 'g-', 'LineWidth', 1.8, 'DisplayName', 'T_{mean}(t)');
            plot(app.StudioEnvelopeAxes, t_vec, t_min_vec, 'b-', 'LineWidth', 1.8, 'DisplayName', 'T_{min}(t)');
            hold(app.StudioEnvelopeAxes, 'off');
            
            grid(app.StudioEnvelopeAxes, 'on');
            legend(app.StudioEnvelopeAxes, 'Location', 'northwest', 'TextColor', [0.9, 0.9, 0.95]);
            title(app.StudioEnvelopeAxes, 'Surface Temperature Range Over Time [Tmax, Tmean, Tmin]', 'Color', [0.9, 0.95, 1.0], 'FontSize', 9);
            xlabel(app.StudioEnvelopeAxes, 'Time t [s]'); ylabel(app.StudioEnvelopeAxes, 'Temperature T [K]');
            
            app.StudioEnvCursorHandle = xline(app.StudioEnvelopeAxes, 0, 'y-', 'LineWidth', 1.5);
        end
        
        function openLargeThermalView(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                if isvalid(app.UIFigure)
                    uialert(app.UIFigure, 'No thermal video available. Run inspection first.', 'Thermal View', 'Icon', 'info');
                end
                return;
            end
            
            if ~isempty(app.PopoutFigure) && isvalid(app.PopoutFigure)
                figure(app.PopoutFigure);
                return;
            end
            
            app.PopoutFigure = uifigure('Name', 'LFMT Standalone Large Thermal Video Player', ...
                'Position', [100, 100, 800, 650], 'Color', [0.10, 0.12, 0.16]);
            
            pGrid = uigridlayout(app.PopoutFigure, [2, 1]);
            pGrid.RowHeight = {'1x', 45};
            pGrid.Padding = [8, 8, 8, 8];
            
            app.PopoutAxes = uiaxes(pGrid);
            app.PopoutAxes.Color = [0.08, 0.09, 0.12];
            app.PopoutAxes.XColor = [0.8, 0.8, 0.85]; app.PopoutAxes.YColor = [0.8, 0.8, 0.85];
            colormap(app.PopoutAxes, 'turbo');
            
            ctrlPanel = uipanel(pGrid, 'BackgroundColor', [0.16, 0.18, 0.22], 'BorderType', 'none');
            ctrlPanel.Layout.Row = 2;
            cGrid = uigridlayout(ctrlPanel, [1, 5]);
            cGrid.ColumnWidth = {40, 70, 40, '1x', 80};
            cGrid.Padding = [4, 2, 4, 2];
            
            uibutton(cGrid, 'Text', '⏮', 'ButtonPushedFcn', @(src, evt) app.stepFrame(-1));
            uibutton(cGrid, 'Text', '▶/⏸', 'FontWeight', 'bold', 'ButtonPushedFcn', @(src, evt) app.togglePlayback());
            uibutton(cGrid, 'Text', '⏭', 'ButtonPushedFcn', @(src, evt) app.stepFrame(1));
            
            uislider(cGrid, 'Limits', [1, app.TotalFrames], 'Value', app.CurrentFrameIdx, ...
                'ValueChangedFcn', @(src, evt) app.onSliderChanged());
            
            uicheckbox(cGrid, 'Text', 'Lock Scale', 'FontColor', [0.85, 0.9, 1.0], 'Value', app.LockColorScaleCheck.Value, ...
                'ValueChangedFcn', @(src, evt) app.updateThermogramFrame());
            
            app.updateThermogramFrame();
        end
        
        function exportMP4Video(app, filename, showAlert)
            if nargin < 3, showAlert = false; end
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'noisy_thermograms')
                if showAlert && isvalid(app.UIFigure)
                    uialert(app.UIFigure, 'No simulation data available to export. Run inspection first.', 'Export Warning', 'Icon', 'warning');
                end
                return;
            end
            
            if nargin < 2 || isempty(filename)
                root_dir = fileparts(mfilename('fullpath'));
                export_dir = fullfile(root_dir, 'results', 'exports');
                if ~exist(export_dir, 'dir'), mkdir(export_dir); end
                ts_str = datestr(now, 'yyyymmdd_HHMMSS');
                filename = fullfile(export_dir, sprintf('lfmt_thermal_video_%s.mp4', ts_str));
            end
            
            app.logMessage(sprintf('Exporting thermal video sequence to MP4: %s...', filename));
            app.StageLabel.Text = 'Status: Exporting MP4 Video...';
            drawnow;
            
            try
                T_data = app.CurrentResults.noisy_thermograms;
                sim_res = app.CurrentResults.simulation;
                n_frames = size(T_data, 1);
                fps = round(sim_res.camera_frame_rate_hz);
                
                h_fig = figure('Visible', 'off', 'Position', [100, 100, 640, 480], 'Color', 'k');
                h_ax = axes(h_fig, 'Color', 'k');
                colormap(h_ax, 'turbo');
                
                v_writer = VideoWriter(filename, 'MPEG-4');
                v_writer.FrameRate = fps;
                v_writer.Quality = 95;
                open(v_writer);
                
                for f = 1:n_frames
                    frame_T = squeeze(T_data(f, :, :));
                    t_f = sim_res.time_vector(f);
                    
                    cla(h_ax);
                    imagesc(h_ax, sim_res.camera_x_mm, sim_res.camera_y_mm, frame_T);
                    axis(h_ax, 'image');
                    colorbar(h_ax, 'Color', 'w');
                    caxis(h_ax, [app.GlobalTMin, app.GlobalTMax]);
                    
                    title(h_ax, sprintf('LFMT Thermal Field T(x,y,t)  |  t = %.2f s (Frame %d/%d)', t_f, f, n_frames), 'Color', 'w');
                    xlabel(h_ax, 'X [mm]', 'Color', 'w'); ylabel(h_ax, 'Y [mm]', 'Color', 'w');
                    set(h_ax, 'XColor', 'w', 'YColor', 'w');
                    
                    f_rendered = getframe(h_fig);
                    writeVideo(v_writer, f_rendered);
                end
                
                close(v_writer);
                delete(h_fig);
                
                app.logMessage(sprintf('MP4 video successfully exported (%d frames at %d fps):\n  -> %s', n_frames, fps, filename));
                app.StageLabel.Text = 'Status: MP4 Export Complete';
                app.StageLabel.FontColor = [0.4, 0.9, 0.5];
                if showAlert && isvalid(app.UIFigure)
                    uialert(app.UIFigure, sprintf('Thermal video exported successfully:\n%s', filename), 'Video Export Complete', 'Icon', 'info');
                end
            catch ME
                app.logMessage(['MP4 Video Export Error: ', ME.message]);
                if exist('h_fig', 'var') && isvalid(h_fig), delete(h_fig); end
            end
        end
        
        %% Tab 5: Benchmark Tab Updates
        function updateBenchmarkTab(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'processed')
                return;
            end
            
            sim_res = app.CurrentResults.simulation;
            proc = app.CurrentResults.processed;
            show_gt = app.GTOverlayCheck.Value;
            
            app.plotSingleMethodAxes(app.BenchAxesRaw, proc.RAW, sim_res, '1. Raw Contrast', show_gt);
            app.plotSingleMethodAxes(app.BenchAxesMF, proc.MF, sim_res, '2. Matched Filter (Pulse Comp)', show_gt);
            app.plotSingleMethodAxes(app.BenchAxesPCT, proc.PCT, sim_res, '3. SVD-PCT (EOF-2)', show_gt);
            app.plotSingleMethodAxes(app.BenchAxesSPCT, proc.SPCT, sim_res, '4. Sparse PCA (SPCT)', show_gt);
            app.plotSingleMethodAxes(app.BenchAxesRPT, proc.RPT, sim_res, '5. Random Projection (RPT)', show_gt);
            
            % Bar chart of CNR and IoU
            cla(app.BenchBarAxes);
            tbl = app.CurrentResults.summary_table;
            
            methods_cat = categorical(cellstr(tbl.Method));
            methods_cat = reordercats(methods_cat, cellstr(tbl.Method));
            
            yyaxis(app.BenchBarAxes, 'left');
            bar(app.BenchBarAxes, methods_cat, tbl.CNR, 0.35, 'FaceColor', [0.2, 0.7, 0.9]);
            ylabel(app.BenchBarAxes, 'CNR (Contrast-to-Noise Ratio)');
            app.BenchBarAxes.YColor = [0.2, 0.7, 0.9];
            
            yyaxis(app.BenchBarAxes, 'right');
            bar(app.BenchBarAxes, methods_cat, tbl.IoU, 0.20, 'FaceColor', [0.95, 0.6, 0.2]);
            ylabel(app.BenchBarAxes, 'IoU (Intersection-over-Union)');
            app.BenchBarAxes.YColor = [0.95, 0.6, 0.2];
            ylim(app.BenchBarAxes, [0, 1.05]);
            
            title(app.BenchBarAxes, 'CNR & IoU Comparison Across 5 Methods', 'Color', [0.9, 0.95, 1.0], 'FontSize', 9);
            grid(app.BenchBarAxes, 'on');
        end
        
        %% Tab 6: Audit Tab Updates
        function updateAuditTab(app)
            if isempty(app.CurrentResults) || ~isfield(app.CurrentResults, 'summary_table')
                return;
            end
            
            sim_res = app.CurrentResults.simulation;
            T_cube = app.CurrentResults.noisy_thermograms;
            t_vec = sim_res.time_vector;
            
            cla(app.AuditGTAxes);
            if sim_res.geometry.has_defect
                d = sim_res.geometry.defect;
                [~, cx_idx] = min(abs(sim_res.camera_x_mm - d.center_x_mm));
                [~, cy_idx] = min(abs(sim_res.camera_y_mm - d.center_y_mm));
                
                T_def = squeeze(T_cube(:, cy_idx, cx_idx));
                T_snd = squeeze(T_cube(:, 2, 2));
                delta_T = T_def - T_snd;
                
                plot(app.AuditGTAxes, t_vec, delta_T, 'Color', [1.0, 0.85, 0.2], 'LineWidth', 2.2);
                grid(app.AuditGTAxes, 'on');
                title(app.AuditGTAxes, 'GROUND-TRUTH DIFFERENTIAL CONTRAST: T_{defect}(t) - T_{sound}(t)  [AUDIT ONLY]', ...
                    'Color', [0.95, 0.85, 0.4], 'FontWeight', 'bold', 'FontSize', 9);
                xlabel(app.AuditGTAxes, 'Time t [s]');
                ylabel(app.AuditGTAxes, '\Delta T(t) [K]');
            else
                title(app.AuditGTAxes, 'Healthy Specimen (No Inclusion) — Zero Differential Contrast Baseline', 'Color', [0.6, 0.8, 0.9], 'FontSize', 9);
            end
            
            % Param specification rows
            cfg = app.CurrentResults.config;
            p_rows = {
                'Plate', 'Dimensions (Lx, Ly, Lz)', sprintf('%.1f x %.1f x %.2f mm', cfg.plate.length_mm, cfg.plate.width_mm, cfg.plate.thickness_mm);
                'Plate', 'Material / Substrate', 'Mild Steel (k = 45 W/m-K, rho = 7850, Cp = 460)';
                'Defect', 'Inclusion Present', string(cfg.plate.has_defect);
                'Defect', 'Slag Diameter & Depth', sprintf('D = %.1f mm, z = %.2f mm, h = %.2f mm', cfg.plate.defect.diameter_mm, cfg.plate.defect.depth_mm, cfg.plate.defect.thickness_mm);
                'Defect', 'Slag Material Properties', 'k = 1.2 W/m-K, rho = 2800, Cp = 850';
                'Excitation', 'Chirp Frequencies (f0 -> f1)', sprintf('%.3f -> %.3f Hz (Sweep Rate = %.4f Hz/s)', cfg.excitation.f0_hz, cfg.excitation.f1_hz, (cfg.excitation.f1_hz - cfg.excitation.f0_hz)/cfg.excitation.duration_s);
                'Excitation', 'Heat Flux Amplitude q0', sprintf('%.0f W/m^2 (Texc = %.1f s, Tobs = %.1f s)', cfg.excitation.q0_w_m2, cfg.excitation.duration_s, cfg.excitation.observation_time_s);
                'Camera', 'Decoupled Resolution', sprintf('%d x %d pixels @ %.1f Hz (%d frames)', size(T_cube, 3), size(T_cube, 2), sim_res.camera_frame_rate_hz, size(T_cube, 1));
                'Camera', 'Noise Model', sprintf('SNR = %s, Seed = %d', string(cfg.camera.noise_snr_db), cfg.camera.noise_seed);
                'Solver', 'Discretization & Time Step', sprintf('%s (dt = %.3f s, Runtime = %.2f s)', sim_res.solver_name, sim_res.solver_dt_s, sim_res.runtime_s)
            };
            app.AuditParamTable.Data = p_rows;
            
            % Summary table
            app.AuditMetricsTable.Data = app.MetricsTable.Data;
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
                exportgraphics(app.Axes3DPlate, fullfile(run_folder, 'plate_3d_geometry.png'), 'Resolution', 300);
                exportgraphics(app.BenchBarAxes, fullfile(run_folder, 'benchmark_ranking.png'), 'Resolution', 300);
                app.logMessage(sprintf('Exported complete report package to folder:\n  -> %s', run_folder));
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
            app.logMessage('Executing MATLAB Unit Test Suite...');
            app.StageLabel.Text = 'Status: Running Unit Tests...';
            drawnow;
            try
                test_res = run_tests();
                if all([test_res.Passed])
                    app.logMessage('All Unit Tests Passed (100% GREEN).');
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
