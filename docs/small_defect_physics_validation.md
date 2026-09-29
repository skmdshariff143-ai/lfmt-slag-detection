# D=4 mm numerical agreement: inadequate spatial resolution

**D=4 mm detectability is not validated by the quoted 0.13–0.20% aggregate L2
agreement.** A focused comparison finds missing FDM defect material on the
baseline mesh and large contrast differences when the defect becomes represented.
No solver or frozen result was changed for this diagnostic.

`python scripts/verify_small_defect_physics.py` ran nine independent FEM/FDM pairs:
all five D=4 mm depths on a 30×22×12 uniform grid, D=8 mm/z=0.4 mm and healthy
references, plus D=4 mm/z=0.2 and 1.0 mm on a 40×28×16 grid. Both solvers were
interpolated to the same 32×32 camera and timestamps over the first four seconds,
matching the legacy comparison window. Unlike the older V2 comparison script,
this does not crop different spatial arrays and assume their pixels coincide.
Configurations, source hashes and solver metadata are saved with the CSV.
The contrast samples use camera pixels (16,16) and (2,2), approximately
(51.61,36.13) and (6.45,4.52) mm, not an exact continuous defect-center probe.
FDM uses explicit stability substeps while FEM uses implicit 0.1-second steps;
time-discretization and boundary/interpolation differences can also contribute.
This comparison isolates neither lateral diffusion nor spatial discretization
alone, and a timestep-convergence study is needed before assigning all error to
the mesh.

| Case | Grid | L2 on °C field | L2 on temperature rise | FEM / FDM peak center-to-sound contrast |
|---|---|---:|---:|---:|
| D4, z0.2 | 30×22×12 | 0.1454% | 1.4724% | 0.1060 / 0.0020 K |
| D4, z1.0 | 30×22×12 | 0.1429% | 1.4476% | 0.0329 / 0.0020 K |
| D4, z0.2 | 40×28×16 | **0.3196%** | **3.2365%** | **0.1908 / 1.5277 K** |
| D4, z1.0 | 40×28×16 | 0.1282% | 1.2982% | 0.0569 / 0.2068 K |
| D8, z0.4 | 30×22×12 | 0.2283% | 2.3100% | 0.4001 / 1.1467 K |
| Healthy | 30×22×12 | 0.1416% | 1.4347% | 0.0027 / 0.0020 K |

The baseline D4 Celsius-norm range is 0.1429–0.1454%, superficially within the
quoted aggregate range. However, `FiniteDifferenceBackend` assigns materials at
cell centers. On the baseline mesh the nearest x/y centers are outside the
2 mm radius: **zero FDM cells contain slag at every D4 depth**. The FEM uses
quadrature-point material classification, so these discretizations do not
represent the same small inclusion. `python scripts/report_small_defect_physics.py`
reconstructs the FDM assignment from recorded geometry and saves actual occupied
cell counts and represented-volume errors.

On the finer grid the shallow D4 Celsius L2 error rises to 0.3196%, exceeding
the 0.20% upper reference, and peak contrast disagrees strongly. The nominal
diameter resolution is still only 1.6 cells, so this is a resolution-sensitivity
test, **not** a converged reference. The baseline's small global error partly
reflects the defect's small area and a missing material region, not validated
lateral diffusion. Celsius and Kelvin normalizations also depend on an arbitrary
temperature offset; baseline-subtracted and defect-contrast errors are more
informative for NDT.

Required follow-up: match represented inclusion volumes/material interfaces,
refine laterally and through the cover layer until both solvers converge,
compare full heating/cooling sequences and registered contrast profiles, and
then acquire independent real LFMT slag data. Do not report either solver as
experimental truth or interpret mutual coarse-grid agreement as validation.

The installed PolyU archive is measured flash thermography and is explicitly
labelled as a transfer study. It does not provide real LFMT slag validation.
The required human dataset is scaffolded in `data/experimental/README.md`.
