classdef TestLFMTConnectionVisualizer < matlab.unittest.TestCase
    % TESTLFMTCONNECTIONVISUALIZER Unit tests for LFMT simulation & physical connection diagrams and Simulink model
    
    properties
        FigList = []
    end
    
    methods (TestMethodSetup)
        function setupPaths(testCase)
            root_dir = fileparts(fileparts(mfilename('fullpath')));
            addpath(root_dir);
            lfmt_setup_paths();
            testCase.FigList = [];
        end
    end
    
    methods (TestMethodTeardown)
        function closeFigures(testCase)
            for k = 1:length(testCase.FigList)
                if isvalid(testCase.FigList(k))
                    delete(testCase.FigList(k));
                end
            end
            testCase.FigList = [];
        end
    end
    
    methods (Test)
        function testSimulationDiagramRendering(testCase)
            % Test pipeline diagram generation
            cfg = default_config();
            h = plot_simulation_connection(cfg, 'Target', 'simulation', 'Export', false, 'Visible', 'off');
            testCase.verifyNotEmpty(h);
            testCase.verifyTrue(isvalid(h));
            testCase.FigList = [testCase.FigList, h];
        end
        
        function testPhysicalDiagramRendering(testCase)
            % Test proposed physical experimental rig diagram generation
            cfg = default_config();
            h = plot_simulation_connection(cfg, 'Target', 'physical', 'Export', false, 'Visible', 'off');
            testCase.verifyNotEmpty(h);
            testCase.verifyTrue(isvalid(h));
            testCase.FigList = [testCase.FigList, h];
        end
        
        function testSpecimenSchematicRendering(testCase)
            % Test 3-D specimen cross section schematic generation
            cfg = default_config();
            h = plot_simulation_connection(cfg, 'Target', 'specimen', 'Export', false, 'Visible', 'off');
            testCase.verifyNotEmpty(h);
            testCase.verifyTrue(isvalid(h));
            testCase.FigList = [testCase.FigList, h];
        end
        
        function testHealthyPlateDiagrams(testCase)
            % Test connection diagrams for healthy plate (no inclusion)
            cfg = default_config();
            cfg.defects = [];
            cfg.plate.has_defect = false;
            
            [h_sim, h_phys, h_spec] = plot_simulation_connection(cfg, 'Target', 'all', 'Export', false, 'Visible', 'off');
            testCase.verifyTrue(isvalid(h_sim));
            testCase.verifyTrue(isvalid(h_phys));
            testCase.verifyTrue(isvalid(h_spec));
            testCase.FigList = [testCase.FigList, h_sim, h_phys, h_spec];
        end
        
        function testFigureExports(testCase)
            % Test 300-DPI PNG exports to results/figures
            root_dir = fileparts(fileparts(mfilename('fullpath')));
            fig_dir = fullfile(root_dir, 'results', 'figures');
            
            [h_sim, h_phys, h_spec] = plot_simulation_connection([], 'Target', 'all', 'Export', true, 'Visible', 'off');
            testCase.FigList = [testCase.FigList, h_sim, h_phys, h_spec];
            
            sim_png = fullfile(fig_dir, 'simulation_connection.png');
            phys_png = fullfile(fig_dir, 'physical_connection.png');
            spec_png = fullfile(fig_dir, 'specimen_connection.png');
            
            testCase.verifyTrue(exist(sim_png, 'file') > 0, 'simulation_connection.png must exist');
            testCase.verifyTrue(exist(phys_png, 'file') > 0, 'physical_connection.png must exist');
            testCase.verifyTrue(exist(spec_png, 'file') > 0, 'specimen_connection.png must exist');
        end
        
        function testSimulinkModelGenerationAndSubsystems(testCase)
            % Test programmatic generation of LFMT_System_Connection.slx
            slx_path = build_lfmt_simulink_model();
            testCase.verifyTrue(exist(slx_path, 'file') > 0, 'LFMT_System_Connection.slx must exist on disk');
            
            load_system('LFMT_System_Connection');
            
            % Verify all 7 major subsystems exist
            expected_subsystems = { ...
                'LFMT_System_Connection/1_Specimen_and_Excitation_Config', ...
                'LFMT_System_Connection/2_LFMT_Chirp_Generator', ...
                'LFMT_System_Connection/3_3D_Hex8_FEM_Thermal_Solver', ...
                'LFMT_System_Connection/4_Virtual_IR_Camera_and_Noise', ...
                'LFMT_System_Connection/5_Blind_Signal_Processing_Suite', ...
                'LFMT_System_Connection/6_Automatic_Defect_Segmentation', ...
                'LFMT_System_Connection/7_Quantitative_Metrics_and_Scopes' ...
            };
            
            for k = 1:length(expected_subsystems)
                sub_h = getSimulinkBlockHandle(expected_subsystems{k});
                testCase.verifyNotEqual(sub_h, -1, sprintf('Subsystem %s must exist in Simulink model', expected_subsystems{k}));
            end
            
            bdclose('all');
        end
        
        function testLiveLabConnectionIntegration(testCase)
            % Test GUI buttons and callbacks in LFMTLiveLab
            app = LFMTLiveLab();
            testCase.verifyTrue(isvalid(app.UIFigure));
            
            % Verify button controls exist
            testCase.verifyTrue(isvalid(app.ViewSimConnButton));
            testCase.verifyTrue(isvalid(app.ViewPhysConnButton));
            testCase.verifyTrue(isvalid(app.OpenSimulinkButton));
            testCase.verifyTrue(isvalid(app.SidebarSimConnButton));
            testCase.verifyTrue(isvalid(app.SidebarSimulinkButton));
            
            % Clean up
            delete(app);
            bdclose('all');
            close all hidden;
        end
    end
end
