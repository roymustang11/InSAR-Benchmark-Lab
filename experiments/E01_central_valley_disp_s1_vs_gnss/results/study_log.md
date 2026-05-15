# E01 Study Log

## Phase 0 Baseline Audit

Date: 2026-05-15

Repository commit: `5face02`

Purpose: lock the current real-data pilot as the baseline before expanding the study.

Commands run:

```bash
PYTHONPATH=src python -m experiments.E01_central_valley_disp_s1_vs_gnss.run \
  --config experiments/E01_central_valley_disp_s1_vs_gnss/config.yml \
  --output experiments/E01_central_valley_disp_s1_vs_gnss/results \
  --download-only \
  --limit-granules 2

PYTHONPATH=src python -m experiments.E01_central_valley_disp_s1_vs_gnss.run \
  --config experiments/E01_central_valley_disp_s1_vs_gnss/config.yml \
  --output experiments/E01_central_valley_disp_s1_vs_gnss/results \
  --gnss-download-only

PYTHONPATH=src python -m experiments.E01_central_valley_disp_s1_vs_gnss.run \
  --config experiments/E01_central_valley_disp_s1_vs_gnss/config.yml \
  --output experiments/E01_central_valley_disp_s1_vs_gnss/results \
  --use-existing \
  --limit-granules 2

python -m pytest -q
```

Baseline metrics:

| Metric | Value |
| --- | ---: |
| OPERA epochs | 2 |
| GNSS stations | 5 |
| Collocated pairs | 10 |
| RMSE | 17.6806 mm |
| MAE | 17.6617 mm |
| Mean bias | 0.0000 mm |
| Skipped stations | 0 |

Baseline artifacts verified:

- `aggregate.json`
- `per_station.csv`
- `manifest.json`
- `figures/residual_histogram.png`
- `figures/residual_variogram.png`
- station time-series CSV files for CRBT, JLN5, LOWS, P284, and P285

Interpretation at this phase: the pilot proves the local real-data pipeline is functional. It is not yet a final scientific result because it uses only two OPERA epochs and five stations.

## Phase 1 Scientific Design

Purpose: align the experiment documentation with the Central Valley validation study before scaling the data.

Design decisions:

- Primary problem: evaluate OPERA DISP-S1 reliability for groundwater-related subsidence monitoring using independent GNSS.
- GNSS reference frame: NGL IGS20 final `tenv3` solutions.
- Evidence tiers: pilot, expanded, and final, so early runs are not overclaimed.
- Admitted stations must lie inside both the AOI and selected OPERA frame footprint and must have enough valid OPERA pixels and collocated GNSS epochs.

Verification:

```bash
python -m pytest -q
```

## Phase 2 Data Expansion

Purpose: expand from the pilot stack to a same-frame validation stack.

Data expansion summary:

| Item | Value |
| --- | ---: |
| OPERA frame | F09155 |
| OPERA epochs cached | 12 |
| Candidate GNSS stations checked | 101 |
| GNSS stations with valid OPERA coverage | 21 |
| Covered GNSS `tenv3` files cached | 21 |

Covered stations:

```text
CRBT, JLN5, LOWS, P284, P285, P287, P288, P289, P290, P291, P295,
P523, P525, P526, P527, P528, P576, PEA1, PEA2, SHP5, USLO
```

Artifacts:

- `opera_inventory.json`
- `station_coverage.csv`
- `gnss_station_inventory.csv`

Interpretation at this phase: the selected frame supports the expanded-tier sample size. The study can now move from pipeline validation to quantitative validation.

## Phase 3 Core Validation Metrics

Purpose: run the expanded validation and report quantitative DISP-S1 vs GNSS agreement metrics.

Expanded validation summary:

| Metric | Value |
| --- | ---: |
| OPERA epochs | 12 |
| GNSS stations | 21 |
| Collocated pairs | 249 |
| RMSE | 26.2436 mm |
| MAE | 21.6181 mm |
| Median absolute residual | 19.3644 mm |
| Station median RMSE | 25.9646 mm |
| Station RMSE IQR | 6.4349 mm |
| Mean bias | 0.0000 mm |
| Skipped stations | 0 |

Primary interpretation: the expanded run is reproducible and station-complete for the selected frame, but the residual scale is much larger than the aspirational final-quality threshold. This makes the next phase essential: sensitivity and error characterization must determine whether the discrepancy is controlled by reference alignment, collocation, masking, geometry, or product/station behavior.

## Phase 4 Sensitivity and Error Characterization

Purpose: test whether the validation conclusion depends on method choices.

Primary expanded result after applying the configured coherence threshold:

| Metric | Value |
| --- | ---: |
| OPERA epochs | 12 |
| GNSS stations | 21 |
| Collocated pairs | 243 |
| RMSE | 25.5817 mm |
| RMSE 95% bootstrap CI | 23.6258 to 27.5315 mm |
| Bias 95% bootstrap CI | -3.3032 to 3.0121 mm |
| Median absolute residual | 18.9393 mm |

Sensitivity summary:

| Variant | Stations | Pairs | RMSE mm | Median abs residual mm |
| --- | ---: | ---: | ---: | ---: |
| Primary | 21 | 243 | 25.5817 | 18.9393 |
| Weighted temporal window | 21 | 245 | 25.7802 | 18.3208 |
| Gaussian temporal smoothing | 21 | 246 | 25.8085 | 18.4056 |
| Coherence threshold 0.3 | 21 | 249 | 26.2328 | 19.3644 |
| Coherence threshold 0.5 | 21 | 243 | 25.5817 | 18.9393 |
| Coherence threshold 0.7 | 16 | 166 | 25.0475 | 18.5378 |
| Stable-window reference | 21 | 243 | 27.9619 | 17.8323 |

Interpretation at this phase: the residual scale is stable across temporal collocation choices and coherence thresholds. The stricter coherence threshold reduces the station network from 21 to 16 but does not materially reduce RMSE. Stable-window referencing increases aggregate bias and RMSE, indicating that reference alignment is an important methodological factor.

## Phase 5 Study-Quality Figures

Purpose: make the expanded validation interpretable from figures as well as tables.

Generated figures:

- `opera_displacement_map.png` — DISP-S1 LOS displacement field for the final epoch in the expanded stack.
- `station_coverage_map.png` — admitted GNSS station locations colored by collocated-pair count.
- `station_residual_map.png` — station locations colored by RMSE.
- `multi_station_timeseries.png` — residual time series for representative stations.
- `sensitivity_summary.png` — aggregate RMSE across sensitivity variants.
- `residual_histogram.png` and `residual_variogram.png` — distribution and spatial structure of residuals.
- `station_*_timeseries.png` — per-station DISP-S1 and GNSS LOS time series.

Interpretation at this phase: the visual outputs show that the study now has a traceable spatial footprint, station-level diagnostics, temporal residual behavior, and sensitivity behavior. These figures support scientific interpretation rather than merely demonstrating that the code runs.

## Phase 6 Results Interpretation

Purpose: convert the expanded metrics and figures into a careful local analysis.

Artifacts:

- `analysis.md`
- updated top-level `README.md` real-data summary

Interpretation summary:

- The workflow has reached expanded-tier evidence for OPERA frame F09155.
- The result is scientifically meaningful because it quantifies disagreement, not just product availability.
- RMSE remains near 25.6 mm across most sensitivity choices.
- Bias after station-wise alignment is near zero, but this should not be read as absolute reference-frame agreement.
- The study is frame-specific and should be extended to adjacent Central Valley frames before making regional claims.
