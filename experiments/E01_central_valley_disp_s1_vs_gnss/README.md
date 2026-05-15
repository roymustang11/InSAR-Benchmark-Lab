# E01 — OPERA DISP-S1 vs Continuous GNSS over the San Joaquin Valley

## Question

Under the validation protocol declared in
[`docs/validation-protocol.md`](../../docs/validation-protocol.md), what
is the per-station residual distribution between the OPERA Level-3
DISP-S1 product and continuous-GNSS daily positions over the San Joaquin
Valley, and does the product satisfy the aggregate verdict?

## Hypothesis

H1. After common-window referencing and per-pixel LOS projection, the
DISP-S1 minus GNSS residual at admissible stations has zero mean within
±2 mm/yr and an RMSE under 5 mm.

H0 is the negation. The hypothesis is evaluated by paired bootstrap on
station-mean residuals.

## Datasets

- **InSAR.** OPERA DISP-S1 V1 NetCDF granules covering one Sentinel-1
  ascending frame intersecting the AOI declared in `config.yml`.
  Granule identifiers and download URLs are recorded in
  `results/manifest.json` after a run.
- **GNSS.** Final IGS14 daily solutions from the Nevada Geodetic
  Laboratory (`tenv3`) for stations whose footprint lies inside the AOI
  and that meet the protocol inclusion criteria.

Provenance for both is documented in
[`docs/data-provenance.md`](../../docs/data-provenance.md).

## Method

1. Load DISP-S1 granules through
   `disp_s1_eval.processors.OperaDispS1Reader`.
2. For each admitted GNSS station, project ENU (with full covariance)
   into the per-pixel LOS using `disp_s1_eval.gnss.project_enu_*`.
3. Temporally collocate GNSS to InSAR epochs using the strategy declared
   in `config.yml` (default: `nearest`).
4. Reference both series by removing the mean residual on the declared
   stable sub-window.
5. Compute per-station metrics from `disp_s1_eval.metrics`.
6. Compute the empirical residual variogram
   (`disp_s1_eval.errors.empirical_variogram`) and fit an exponential
   model.
7. Run the reference-point bootstrap as a sensitivity branch.
8. Write `results/per_station.csv`, `results/aggregate.json`,
   `results/figures/`, `results/summary.md`, and
   `results/manifest.json`.

## Reproducibility

```bash
python -m experiments.E01_central_valley_disp_s1_vs_gnss.run \
    --config experiments/E01_central_valley_disp_s1_vs_gnss/config.yml \
    --output experiments/E01_central_valley_disp_s1_vs_gnss/results
```

The run is deterministic given the seed declared in `config.yml`. Wall
clock depends on the number of granules and stations; for a two-year,
single-frame configuration with ~20 stations, the typical time on a
modern laptop is on the order of minutes once data are downloaded.

## Deviations

None.
