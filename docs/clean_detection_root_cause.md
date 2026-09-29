# Clean-condition detection anomaly (analysis v1.0.0)

The frozen `2.1.0-final-audited` results remain unchanged. This note supplements,
and qualifies the claim that all anomalies were resolved in, `results_integrity_audit.md`.

## Evidence and causal trace

`python scripts/analyze_detection_surface.py` reads the frozen CSV and exports
625 detection-fraction cells (25 geometries × five methods × five condition
views), 300 paired Wilcoxon comparisons, healthy false alarms, and source hashes.
Each clean cell has one deterministic observation; each noisy cell has ten seed
labels. The pooled fraction weights clean:noisy observations 1:30. These are
empirical fractions under this protocol, not experimentally validated POD curves.

`python scripts/trace_clean_detection.py` reads the existing FEM caches without
rewriting them. It reconstructs the historical 32×32 camera at 10 Hz, runs the
current PCT/RPT/SPCT implementations, and records threshold, selected component,
foreground size, ground-truth overlap, and counts after opening and closing.
The processing implementations differ from commit `53197576` only in unused
imports. The noisy trace uses the current noise implementation and one seed,
and therefore is a mechanism experiment, not a replay of historical noisy scores.

Across all 25 cached clean specimens:

| Method | Otsu foreground overlaps defect | Nonempty after morphology | Overlaps defect after morphology |
|---|---:|---:|---:|
| PCT | 25 | 0 | 0 |
| RPT | 25 | 4 | 0 |
| SPCT | 22 | 2 | 0 |

These surviving-candidate counts match the frozen clean rows exactly. There is
no claim of bitwise historical replay: the local cache metadata lacks config
hashes and includes a 26×18×7 grid, whereas the historical full-run script requested
30×21×8 and accepted existing caches. Cache file hashes are saved in the trace
manifest so this diagnostic can be reproduced and its provenance reviewed.
There is
no special clean branch in Otsu. After per-map min/max normalization, the detector
thresholds with `>=`, opens with a full 3×3 square, then closes with that square.
The opening requires a complete 3×3 foreground neighborhood. Pixel spacing is
100/31 by 70/31 mm; the nominal three-pixel footprint is about 9.7×6.8 mm.
Small, concentrated clean anomalies disappear. In the representative D=4 mm,
z=0.2 mm PCT case, eight thresholded pixels include the four GT pixels; opening
removes all eight. The issue is destructive spatial filtering at inadequate
sampling, not lack of thermal contrast or an Otsu clean-path arithmetic error.

RPT's four and SPCT's two surviving regions have no GT overlap: component
selection/polarity and background structure also matter. PCT selects absolute
excess kurtosis without an energy floor; SPCT selects peak/std; RPT maximizes
dynamic range. All can change selected component when noise is added. Noise
creates broader/random foreground regions that sometimes survive opening and
overlap the centered defect. Higher noisy detection does not establish improved
physical sensitivity. SPCT emits convergence warnings in this replay, another
reason to treat its selected components cautiously.

The degenerate-map path also deserves correction: a constant map becomes zero,
Otsu returns zero, and `>=` initially selects the whole image. This is a separate
edge case, not the explanation of these nonconstant clean maps.

## Statistical interpretation

Pairing uses `(diameter_mm, depth_mm, noise_condition, noise_seed)`, never CSV row
position. Duplicate keys, missing pairs, and nonfinite values fail the analysis.
Two-sided asymptotic Wilcoxon tests cover detection, IoU, and CNR, with Holm
correction across ten method pairs per metric/condition/unit. All-zero differences
have p=1. Geometry-averaged tests are primary; run-level tests are exploratory.
All 375 noisy method/geometry/condition groups have identical detection, IoU,
and CNR values across all ten seed labels. Nominal seed counts must
not be interpreted as independent realizations. See the existing seed-integrity
work and corrected configurations before making inferential claims. Binary
outcomes have extensive ties; a paired binary test is a useful future sensitivity
analysis. Statistical significance is not a claim of practical detection quality.

## Proposed correction (not applied to historical results)

Reserve `conference-v2.2-morphology-calibration` for a separately generated study:

1. Explicitly reject nonfinite/constant maps before thresholding.
2. Replace unconditional opening with connected-component area filtering;
   calibrate minimum physical area and optional morphology on independent
   synthetic training/validation specimens including healthy controls.
3. Increase camera and solver spatial resolution together, recording effective
   pixel size. Upsampling old maps cannot restore spatial information.
4. Gate component selection on energy and stability; evaluate polarity without
   GT. Measure false alarms alongside sensitivity, and preserve score maps.
5. Re-run all methods with verified distinct noise realizations, a held-out
   calibration split, and matched inputs. Report corrected and historical results
side by side with config/source hashes. Never overwrite `final/` or silently
   relabel the old dataset lock.

This follows the issue/root-cause/correction structure of the integrity audit
§2, but is a proposal pending a new versioned benchmark, not an asserted fix.

## Verification prerequisite repair

The first full-suite run reported 97 passed and one existing MATLAB multi-defect
failure (`only a scalar struct can be returned from MATLAB`). The new
`lfmt.solveForPython` MATLAB wrapper exports only the five numeric fields consumed
by the Python backend, avoiding conversion of nested defect struct arrays. It
does not alter the PDE solve or native MATLAB result. The failing test passed
after this repair; full rerun evidence is recorded with the tier checkpoint.
