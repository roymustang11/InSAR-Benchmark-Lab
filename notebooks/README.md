# Notebooks

The notebook track has two layers:

1. **Method-definition notebooks (01–05).** Self-contained, no live data
   downloads. They define the analysis methods on small controlled
   inputs and document the project scope.
2. **Framework overview (06).** Exercises the `disp_s1_eval` library
   end-to-end on inline data: GNSS ingestion, ENU-to-LOS projection
   with covariance, triple collocation, and an experiment dry-run.

Real-data analyses live under [`experiments/`](../experiments) and are
invoked via a CLI runner that writes a complete provenance trace to
`results/manifest.json`.

| Notebook | Purpose |
| --- | --- |
| [`01_project_orientation.ipynb`](01_project_orientation.ipynb) | Study area, scientific question, data sources, workflow map. |
| [`02_hyp3_or_opera_to_timeseries.ipynb`](02_hyp3_or_opera_to_timeseries.ipynb) | Search OPERA DISP-S1 products, build an inventory table, inspect Zarr-reference metadata. |
| [`03_mintpy_timeseries_validation.ipynb`](03_mintpy_timeseries_validation.ipynb) | Define the InSAR-vs-GNSS validation method on controlled inputs. |
| [`04_uncertainty_and_reference_sensitivity.ipynb`](04_uncertainty_and_reference_sensitivity.ipynb) | Define reference-point, coherence, and masking sensitivity methods on controlled inputs. |
| [`05_deformation_story_map.ipynb`](05_deformation_story_map.ipynb) | Define the final-figure recipe (maps, time series, residuals) on controlled inputs. |
| [`06_framework_overview.ipynb`](06_framework_overview.ipynb) | Run the `disp_s1_eval` core abstractions and an experiment dry-run with no external dependencies. |

Notebooks 03–05 are method-definition notebooks, not Central Valley
deformation measurements.
