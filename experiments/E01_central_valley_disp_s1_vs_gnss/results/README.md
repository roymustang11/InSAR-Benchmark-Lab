# E01 Results

This directory contains the local expanded validation result for OPERA
DISP-S1 frame `F09155` over the San Joaquin Valley.

## Headline Metrics

| Metric | Value |
| --- | ---: |
| OPERA epochs | 12 |
| GNSS stations | 21 |
| Collocated pairs | 243 |
| RMSE | 25.58 mm |
| MAE | 21.00 mm |
| RMSE 95% CI | 23.63 to 27.53 mm |
| Bias 95% CI | -3.30 to 3.01 mm |

## Figures

| Figure | What it shows |
| --- | --- |
| `figures/opera_displacement_map.png` | Measured OPERA LOS displacement for the final epoch. |
| `figures/opera_coherence_map.png` | Mean OPERA temporal coherence used for quality assessment. |
| `figures/station_coverage_map.png` | GNSS stations admitted to the validation set. |
| `figures/station_residual_map.png` | Station-level residual RMSE. |
| `figures/multi_station_timeseries.png` | Residual time series for representative stations. |
| `figures/sensitivity_summary.png` | RMSE response to collocation, coherence, and reference choices. |
| `figures/residual_histogram.png` | Distribution of DISP-S1 minus GNSS residuals. |
| `figures/residual_variogram.png` | Spatial residual semivariance. |

## Tables and JSON

| Artifact | Contents |
| --- | --- |
| `aggregate.json` | Aggregate metrics, bootstrap intervals, and variogram. |
| `per_station.csv` | Station-level metrics and trend comparisons. |
| `sensitivity.json` | Sensitivity branch metrics. |
| `station_coverage.csv` | GNSS station inclusion and coverage status. |
| `station_timeseries/*.csv` | Collocated DISP-S1 and GNSS LOS time series. |
| `manifest.json` | Config snapshot, input hashes, output hashes, provenance. |

## Interpretation

Read `analysis.md` for the scientific interpretation and `final_status.md`
for the verification summary. The result is specific to frame `F09155`; it
should not be generalized to all Central Valley frames without repeating the
same validation protocol.
