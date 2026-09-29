function mat = materials(name)
% MATERIALS Thermophysical Material Properties Database for LFMT Simulation.
%
% Returns a struct containing verified thermophysical properties:
%   - thermal_conductivity (k) [W/(m·K)]
%   - density (rho) [kg/m^3]
%   - specific_heat (Cp) [J/(kg·K)]
%   - thermal_diffusivity (alpha) [m^2/s]
%   - thermal_effusivity (e) [W·s^(1/2)/(m^2·K)]
%   - reference literature citation

if nargin < 1 || isempty(name)
    name = 'mild_steel';
end

clean_name = lower(strtrim(name));
clean_name = strrep(clean_name, ' ', '_');
clean_name = strrep(clean_name, '-', '_');

switch clean_name
    case {'mild_steel', 'mild_steel_1018', 'aisi_1018', 'steel'}
        mat = struct(...
            'name', 'Mild Steel (AISI 1018)', ...
            'thermal_conductivity', 51.9, ... % W/(m·K) at 300 K
            'density', 7850.0, ...            % kg/m^3
            'specific_heat', 486.0, ...       % J/(kg·K)
            'reference', 'Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (7th Ed., Wiley, 2011), App. A', ...
            'doi_isbn', 'ISBN: 978-0470501979', ...
            'is_placeholder', false ...
        );
        
    case {'slag', 'welding_slag', 'welding_slag_silicate', 'silicate_slag'}
        mat = struct(...
            'name', 'Welding Slag (Silicate / Flux Residue)', ...
            'thermal_conductivity', 1.20, ... % W/(m·K)
            'density', 2800.0, ...            % kg/m^3
            'specific_heat', 850.0, ...       % J/(kg·K)
            'reference', 'Mills, K.C., Structure and Properties of Slags (1993); ASM Handbook Vol. 6', ...
            'doi_isbn', 'ISBN: 978-0852953204', ...
            'is_placeholder', false ...
        );
        
    case {'air', 'air_cavity', 'void', 'delamination'}
        mat = struct(...
            'name', 'Air / Delamination Void', ...
            'thermal_conductivity', 0.026, ...% W/(m·K) at 300 K
            'density', 1.161, ...             % kg/m^3
            'specific_heat', 1007.0, ...      % J/(kg·K)
            'reference', 'NIST Standard Reference Database 69 (Chemistry WebBook)', ...
            'doi_isbn', 'DOI: 10.18434/T4D303', ...
            'is_placeholder', false ...
        );
        
    case {'stainless_steel_304', 'ss304', 'stainless_steel'}
        mat = struct(...
            'name', 'Stainless Steel (AISI 304)', ...
            'thermal_conductivity', 14.9, ... % W/(m·K)
            'density', 7900.0, ...            % kg/m^3
            'specific_heat', 477.0, ...       % J/(kg·K)
            'reference', 'Incropera & DeWitt (7th Ed.), Table A.1', ...
            'doi_isbn', 'ISBN: 978-0470501979', ...
            'is_placeholder', false ...
        );
        
    otherwise
        error('LFMT:UnknownMaterial', 'Material "%s" is not in the material database.', name);
end

% Derived thermophysical quantities
mat.thermal_diffusivity = mat.thermal_conductivity / (mat.density * mat.specific_heat);
mat.thermal_effusivity = sqrt(mat.thermal_conductivity * mat.density * mat.specific_heat);
end
