function L = buildConductionOperator(grid, k_field)
% BUILDCONDUCTIONOPERATOR Assembles conservative 3-D conduction matrix
%
% Uses harmonic mean interface conductivity across discontinuous interfaces:
%   k_face = (dx1 + dx2) / (dx1/k1 + dx2/k2)
%
% Returns:
%   L: Sparse symmetric positive semi-definite conduction matrix (N x N)
%      where N = Nx * Ny * Nz

Nx = grid.Nx;
Ny = grid.Ny;
Nz = grid.Nz;
N = Nx * Ny * Nz;

% Flattening convention: node(i, j, k) = i + (j-1)*Nx + (k-1)*Nx*Ny
node_idx = @(i, j, k) (i + (j - 1) * Nx + (k - 1) * Nx * Ny);

% Estimate maximum nonzeros: 7 diagonals (center + 6 neighbors)
max_nnz = 7 * N;
I_idx = zeros(max_nnz, 1);
J_idx = zeros(max_nnz, 1);
V_val = zeros(max_nnz, 1);
entry_count = 0;

diag_accum = zeros(N, 1);

% 1. Conduction in X direction (between (i,j,k) and (i+1,j,k))
for k = 1:Nz
    dz = grid.dz(k);
    for j = 1:Ny
        dy = grid.dy(j);
        Area_x = dy * dz;
        for i = 1:(Nx - 1)
            dx1 = grid.dx(i);
            dx2 = grid.dx(i + 1);
            k1 = k_field(i, j, k);
            k2 = k_field(i + 1, j, k);
            
            % Harmonic mean interface conductivity
            k_face = (dx1 + dx2) / (dx1 / k1 + dx2 / k2);
            dist = 0.5 * (dx1 + dx2);
            conductance = k_face * Area_x / dist;
            
            p1 = node_idx(i, j, k);
            p2 = node_idx(i + 1, j, k);
            
            % Accumulate off-diagonals
            entry_count = entry_count + 1;
            I_idx(entry_count) = p1;
            J_idx(entry_count) = p2;
            V_val(entry_count) = -conductance;
            
            entry_count = entry_count + 1;
            I_idx(entry_count) = p2;
            J_idx(entry_count) = p1;
            V_val(entry_count) = -conductance;
            
            diag_accum(p1) = diag_accum(p1) + conductance;
            diag_accum(p2) = diag_accum(p2) + conductance;
        end
    end
end

% 2. Conduction in Y direction (between (i,j,k) and (i,j+1,k))
for k = 1:Nz
    dz = grid.dz(k);
    for i = 1:Nx
        dx = grid.dx(i);
        Area_y = dx * dz;
        for j = 1:(Ny - 1)
            dy1 = grid.dy(j);
            dy2 = grid.dy(j + 1);
            k1 = k_field(i, j, k);
            k2 = k_field(i, j + 1, k);
            
            k_face = (dy1 + dy2) / (dy1 / k1 + dy2 / k2);
            dist = 0.5 * (dy1 + dy2);
            conductance = k_face * Area_y / dist;
            
            p1 = node_idx(i, j, k);
            p2 = node_idx(i, j + 1, k);
            
            entry_count = entry_count + 1;
            I_idx(entry_count) = p1;
            J_idx(entry_count) = p2;
            V_val(entry_count) = -conductance;
            
            entry_count = entry_count + 1;
            I_idx(entry_count) = p2;
            J_idx(entry_count) = p1;
            V_val(entry_count) = -conductance;
            
            diag_accum(p1) = diag_accum(p1) + conductance;
            diag_accum(p2) = diag_accum(p2) + conductance;
        end
    end
end

% 3. Conduction in Z direction (between (i,j,k) and (i,j,k+1))
for j = 1:Ny
    dy = grid.dy(j);
    for i = 1:Nx
        dx = grid.dx(i);
        Area_z = dx * dy;
        for k = 1:(Nz - 1)
            dz1 = grid.dz(k);
            dz2 = grid.dz(k + 1);
            k1 = k_field(i, j, k);
            k2 = k_field(i, j, k + 1);
            
            k_face = (dz1 + dz2) / (dz1 / k1 + dz2 / k2);
            dist = 0.5 * (dz1 + dz2);
            conductance = k_face * Area_z / dist;
            
            p1 = node_idx(i, j, k);
            p2 = node_idx(i, j, k + 1);
            
            entry_count = entry_count + 1;
            I_idx(entry_count) = p1;
            J_idx(entry_count) = p2;
            V_val(entry_count) = -conductance;
            
            entry_count = entry_count + 1;
            I_idx(entry_count) = p2;
            J_idx(entry_count) = p1;
            V_val(entry_count) = -conductance;
            
            diag_accum(p1) = diag_accum(p1) + conductance;
            diag_accum(p2) = diag_accum(p2) + conductance;
        end
    end
end

% Diagonal entries
for p = 1:N
    entry_count = entry_count + 1;
    I_idx(entry_count) = p;
    J_idx(entry_count) = p;
    V_val(entry_count) = diag_accum(p);
end

% Trim unused preallocated elements
I_idx = I_idx(1:entry_count);
J_idx = J_idx(1:entry_count);
V_val = V_val(1:entry_count);

L = sparse(I_idx, J_idx, V_val, N, N);
end
