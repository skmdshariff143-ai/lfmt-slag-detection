function grid = createGrid(Lx_mm, Ly_mm, Lz_mm, Nx, Ny, Nz)
% CREATEGRID Generates a structured 3-D Cartesian grid in strict SI units
%
% Parameters:
%   Lx_mm, Ly_mm, Lz_mm: Plate dimensions in millimeters
%   Nx, Ny, Nz:          Number of cell control volumes in x, y, z

if nargin < 6, Nz = 12; end
if nargin < 5, Ny = 28; end
if nargin < 4, Nx = 40; end
if nargin < 3, Lz_mm = 2.3; end
if nargin < 2, Ly_mm = 70.0; end
if nargin < 1, Lx_mm = 100.0; end

% Convert dimensions to SI meters
Lx_m = Lx_mm * 1e-3;
Ly_m = Ly_mm * 1e-3;
Lz_m = Lz_mm * 1e-3;

% Cell edges
x_edges = linspace(0, Lx_m, Nx + 1);
y_edges = linspace(0, Ly_m, Ny + 1);
z_edges = linspace(0, Lz_m, Nz + 1);

% Cell centers
xc = 0.5 * (x_edges(1:end-1) + x_edges(2:end));
yc = 0.5 * (y_edges(1:end-1) + y_edges(2:end));
zc = 0.5 * (z_edges(1:end-1) + z_edges(2:end));

% Cell sizes
dx = diff(x_edges);
dy = diff(y_edges);
dz = diff(z_edges);

% 3-D meshgrid of cell centers (indexing: (ix, iy, iz))
[X, Y, Z] = ndgrid(xc, yc, zc);
[DX, DY, DZ] = ndgrid(dx, dy, dz);

grid = struct(...
    'Lx_m', Lx_m, 'Ly_m', Ly_m, 'Lz_m', Lz_m, ...
    'Nx', Nx, 'Ny', Ny, 'Nz', Nz, ...
    'total_cells', Nx * Ny * Nz, ...
    'x_edges', x_edges, 'y_edges', y_edges, 'z_edges', z_edges, ...
    'xc', xc, 'yc', yc, 'zc', zc, ...
    'dx', dx, 'dy', dy, 'dz', dz, ...
    'X', X, 'Y', Y, 'Z', Z, ...
    'DX', DX, 'DY', DY, 'DZ', DZ, ...
    'dV', DX .* DY .* DZ ...
);
end
