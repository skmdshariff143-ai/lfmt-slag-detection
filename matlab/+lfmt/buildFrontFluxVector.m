function q_unit_vec = buildFrontFluxVector(grid)
% BUILDFRONTFLUXVECTOR Unit heat flux distribution across front (z=0) surface
%
% Returns:
%   q_unit_vec: Vector (N x 1) containing cell surface areas on z=0 face.
%               When multiplied by heat flux q(t) [W/m^2], gives Watts into cell.

Nx = grid.Nx;
Ny = grid.Ny;
Nz = grid.Nz;
N = Nx * Ny * Nz;

node_idx = @(i, j, k) (i + (j - 1) * Nx + (k - 1) * Nx * Ny);
q_unit_vec = zeros(N, 1);

for j = 1:Ny
    dy = grid.dy(j);
    for i = 1:Nx
        dx = grid.dx(i);
        Area_z = dx * dy;
        p_front = node_idx(i, j, 1);
        q_unit_vec(p_front) = Area_z;
    end
end
end
