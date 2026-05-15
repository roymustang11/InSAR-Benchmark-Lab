# E01 Final Local Status

## Scope

This local result package contains an expanded validation of OPERA DISP-S1
against continuous GNSS for the San Joaquin Valley portion of California's
Central Valley.

## Final Expanded Run

| Item | Value |
| --- | --- |
| OPERA product | OPERA DISP-S1 V1 |
| Frame | F09155 |
| Polarization | VV |
| GNSS source | NGL final IGS20 `tenv3` |
| OPERA epochs | 12 |
| Admitted GNSS stations | 21 |
| Collocated pairs | 243 |
| Primary coherence threshold | 0.5 |
| Primary temporal collocation | nearest daily GNSS solution within 3 days |

## Main Metrics

| Metric | Value |
| --- | ---: |
| RMSE | 25.5817 mm |
| RMSE 95% bootstrap CI | 23.6258 to 27.5315 mm |
| MAE | 20.9956 mm |
| Median absolute residual | 18.9393 mm |
| Bias | approximately 0.0 mm |
| Bias 95% bootstrap CI | -3.3032 to 3.0121 mm |
| Station median RMSE | 25.7487 mm |
| Station RMSE IQR | 7.2900 mm |

## Verification Commands

```bash
PYTHONPATH=src python -m experiments.E01_central_valley_disp_s1_vs_gnss.run \
  --config experiments/E01_central_valley_disp_s1_vs_gnss/config.yml \
  --output experiments/E01_central_valley_disp_s1_vs_gnss/results \
  --use-existing \
  --limit-granules 12

python -m pytest -q

git ls-files 'data/raw/**' '*.nc' '*.h5' '.netrc'
```

Verification result: the workflow regenerated from cached local data, the
test suite passed, and no raw data products or credential files are tracked
by Git.

## Interpretation

The study now supports an expanded-tier validation result for OPERA frame
F09155. The product is not being presented as universally validated for all
Central Valley frames. The main scientific result is that DISP-S1 and GNSS
show comparable deformation behavior at a network scale, while residuals of
roughly 20-30 mm remain after station-wise reference alignment. Sensitivity
tests show that this residual scale is stable across temporal collocation
choices and coherence thresholds, while reference alignment has a stronger
effect on aggregate bias and RMSE.

## Local Package Contents

- `aggregate.json`
- `per_station.csv`
- `sensitivity.json`
- `station_coverage.csv`
- `analysis.md`
- `study_log.md`
- `figures/*.png`
- `station_timeseries/*.csv`
- `manifest.json`

## Remaining Scientific Limitations

- The result is specific to OPERA frame F09155.
- Raw OPERA NetCDF products and GNSS caches are local ignored inputs, not
  committed repository artifacts.
- Station-wise alignment removes constant offsets; it does not validate an
  absolute reference frame.
- GNSS equipment/coseismic step screening is not yet connected to the NGL
  step database.
- Cross-frame and cross-processor validation remain future extensions.
