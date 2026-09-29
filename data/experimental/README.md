# Required real LFMT slag validation data — scaffold only

**No LFMT-on-real-slag validation dataset is supplied here. No sample measurements
or annotations have been fabricated.** The repository has a locally installed
PolyU measured flash-thermography archive and an external measured-data example.
That is a different excitation and defect study; it cannot validate LFMT slag
detection. `data/experimental_lfmt_slag/` currently contains a schema template only.

A human acquisition must supply:

1. Radiometric sequences as NPZ (`thermograms`: time×height×width, explicit K or
   °C units; `time_vector`: measured seconds), or original camera files plus a
   documented radiometric conversion. Include pre-heating baseline, the complete
   chirp, and post-heating cooling for TSR. Preserve dropped-frame and saturation
   flags; do not infer timestamps from a nominal frame rate when actual times exist.
2. Synchronized measured excitation/trigger logs with units, chirp endpoints,
   duration, incident heat-flux calibration and uncertainty, spatial illumination
   map, ambient temperature, air motion, mounting and back/side boundary conditions.
3. Camera model, spectral band, integration time, calibration date, emissivity
   and reflected-temperature correction, NETD, bad-pixel treatment, lens/FOV,
   mm/pixel calibration, optical blur and specimen-to-camera registration.
4. Specimen IDs, steel grade, measured thickness and uncertainty, surface finish,
   coating, weld geometry and heat-affected zone, and independently measured
   thermal properties where available. Include the full intended D/z grid,
   particularly D=4 mm, and defect-free controls from independent specimens.
5. Independent defect truth from sectioning, CT, or another documented reference:
   confirm slag identity, 3D shape, centroid, top-surface depth, lateral dimensions,
   uncertainty, and registered 2D projection masks. Keep truth inaccessible to
   blind inference. Record disagreements/ambiguous specimens rather than deleting them.
6. Repeated acquisitions on different days/operators and independent specimens;
   partition train/calibration/test by specimen before fitting thresholds or models.
   Do not count repeated frames or synthetic noise seeds as independent specimens.
7. A manifest with immutable file hashes, consent/license, source/provenance,
   acquisition software, processing configuration, exclusion reasons, and a
   dataset version. Missing values must be explicit `null`/`[MEASUREMENT NEEDED]`,
   not plausible-looking defaults.

Suggested layout (paths below are placeholders, not supplied data):

```text
data/experimental/<DATASET_VERSION>/
  manifest.json
  calibration/
  specimens/<SPECIMEN_ID>/metadata.json
  specimens/<SPECIMEN_ID>/raw/sequence.npz
  specimens/<SPECIMEN_ID>/raw/excitation.csv
  ground_truth/<SPECIMEN_ID>/reference_and_registration/
  splits.json
```

Before calling a result physical validation, run unit/timestamp/calibration and
registration checks, lock the held-out split, and report sensitivity and false
alarms with specimen-level uncertainty, detection by diameter/depth, IoU,
localization, and acquisition failures. A file-format loader passing its tests
does not establish physical validity.
