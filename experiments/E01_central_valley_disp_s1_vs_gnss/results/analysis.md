# E01 Expanded Result Analysis

## Aim

This study evaluates whether OPERA DISP-S1 provides reliable line-of-sight
displacement measurements for groundwater-related land subsidence in the
San Joaquin Valley when validated against independent continuous GNSS.

The experiment is not a generic InSAR processing demo. It tests a specific
scientific question: how well a public Sentinel-1 displacement product
matches ground-based geodetic observations after consistent LOS projection,
temporal collocation, station-wise reference alignment, and quality masking.

## Study Configuration

| Item | Value |
| --- | --- |
| Region | San Joaquin Valley, California |
| InSAR product | OPERA DISP-S1 V1 |
| OPERA frame | F09155 |
| Polarization | VV |
| GNSS source | NGL final IGS20 `tenv3` |
| OPERA epochs | 12 |
| Admitted GNSS stations | 21 |
| Collocated InSAR-GNSS pairs | 243 |
| Primary collocation | Nearest GNSS daily solution within 3 days |
| Primary coherence threshold | 0.5 |

## Main Quantitative Result

The expanded run produced the following aggregate residual statistics for
DISP-S1 minus GNSS LOS displacement:

| Metric | Value |
| --- | ---: |
| RMSE | 25.5817 mm |
| RMSE 95% bootstrap CI | 23.6258 to 27.5315 mm |
| MAE | 20.9956 mm |
| Median absolute residual | 18.9393 mm |
| Mean bias | approximately 0.0 mm |
| Bias 95% bootstrap CI | -3.3032 to 3.0121 mm |
| Station median RMSE | 25.7487 mm |
| Station RMSE IQR | 7.2900 mm |

The near-zero mean bias is expected after station-wise reference alignment
and should not be interpreted as proof of absolute geodetic agreement. The
more informative result is the residual scale: station-level errors remain
on the order of 20-30 mm for this frame and time window.

## Sensitivity Findings

Temporal collocation does not materially change the result. Weighted-window
and Gaussian-smoothed GNSS collocation produce RMSE values close to the
nearest-neighbor primary result.

Coherence masking changes the station network more than it changes the
aggregate residual scale. Raising the threshold to 0.7 reduces the admitted
network from 21 to 16 stations, but RMSE remains near 25 mm.

Stable-window reference alignment increases RMSE and produces non-zero
aggregate bias. This indicates that reference alignment is a meaningful
methodological factor and must be reported explicitly.

## Scientific Interpretation

For the selected frame and time window, OPERA DISP-S1 captures a subsidence
signal that is broadly comparable to GNSS in trend direction at many
stations, but the residual magnitude is too large for a strict final-quality
validation verdict under the protocol. The result is scientifically useful
because it identifies the scale and structure of the disagreement rather
than hiding it behind a processing demonstration.

The current evidence supports an expanded-tier validation result:

- The real-data workflow is reproducible from cached OPERA and GNSS inputs.
- The station network is large enough for aggregate residual analysis.
- Residual magnitude is robust across temporal-collocation choices.
- Spatial residual diagnostics and station-level figures are available.

The current evidence does not yet support a final regional verdict for all
Central Valley subsidence monitoring use cases. That would require stronger
trend-level analysis across more frames, longer time windows, or comparison
against additional independent products.

## Key Limitations

- The result is frame-specific (`F09155`) and should not be generalized to
  all Central Valley OPERA frames without repeating the workflow.
- Station-wise mean alignment removes constant offsets, so aggregate bias is
  not an absolute reference-frame validation.
- The default OPERA product did not provide per-pixel uncertainty in the
  fields used by this reader, so uncertainty coverage is not yet evaluated.
- GNSS step-event screening is documented in the protocol but not yet wired
  to the NGL `steps.txt` database in this run.
- The analysis uses a single OPERA product family; cross-processor
  comparison remains future work.

## Result Artifacts

- `aggregate.json` — aggregate metrics, bootstrap intervals, variogram.
- `per_station.csv` — station-level metrics and trend comparisons.
- `sensitivity.json` — collocation, masking, and reference sensitivity.
- `station_coverage.csv` — candidate station coverage against valid OPERA pixels.
- `figures/opera_displacement_map.png` — OPERA LOS displacement map.
- `figures/station_coverage_map.png` — admitted GNSS station map.
- `figures/station_residual_map.png` — station RMSE map.
- `figures/multi_station_timeseries.png` — residual time-series comparison.
- `figures/sensitivity_summary.png` — RMSE sensitivity summary.

## Next Scientific Step

The strongest next analysis is to repeat the same validation for adjacent
Central Valley frames and compare whether residual scale and sensitivity
behavior are frame-specific or systematic across the aquifer system.
