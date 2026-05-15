# Validation Protocol

The protocol is pre-declared: it is fixed before any experiment is run and
is referenced by every experiment's `README.md`. Deviations must be named
in the experiment's deviations section with justification.

For a given InSAR product $P$, a GNSS station $s$, and a time window
$[t_0, t_1]$, the protocol defines what it means for $P$ to be validated
at $s$. Per-station and aggregate verdicts are reported.

## 1. Inclusion criteria

A station $s$ enters the validation set when:

1. NGL provides a final-solution `tenv3` file with at least 200 valid
   daily epochs inside $[t_0, t_1]$.
2. The station lies inside the InSAR product footprint, with at least
   90% of its required pixel neighborhood (3×3 pixels by default) marked
   valid.
3. The station's NGL `steps.txt` reports no uncorrected equipment or
   coseismic offset inside $[t_0, t_1]$. Stations with uncorrected steps
   may enter a sensitivity branch but not the primary set.

## 2. Spatial collocation

The InSAR sample at station $s$ is computed as the coherence-weighted
mean of the $k \times k$ pixel neighborhood centered on $s$ (default
$k=3$, recorded per experiment), excluding pixels masked by the
product-native quality layer or by the experiment's coherence threshold.
If fewer than $\lceil k^2 / 2 \rceil$ pixels remain valid, the station
is excluded.

## 3. Temporal collocation

Three strategies are supported; the choice is named in the experiment
configuration.

| Strategy | Definition |
| --- | --- |
| `nearest` | The GNSS daily solution closest in time to the InSAR epoch (within ±3 days, otherwise NaN). |
| `weighted_window` | A symmetric ±$w$-day window around the InSAR epoch with inverse-time-distance weights; default $w=7$. |
| `gaussian_smoothing` | A Gaussian temporal kernel of standard deviation $\sigma_t$ days centered on the InSAR epoch; default $\sigma_t=10$. |

Primary results use `nearest`; the other two appear in the sensitivity
section.

## 4. Reference-frame alignment

Both series are aligned by removing a constant additive offset estimated
on the stable sub-window declared in the experiment configuration. The
offset is the sub-window mean residual. Its standard error must be below
2 mm; otherwise the station is flagged.

GNSS ENU is projected to LOS using per-pixel geometry per
[`methodology.md`](methodology.md) §2, with covariance propagation.

## 5. Per-station metrics

For each admitted station, the framework reports:

- $N_{eff}$, the number of collocated InSAR–GNSS pairs.
- RMSE of the residual in mm.
- Mean residual (bias) in mm.
- Pearson correlation coefficient.
- Linear-regression slope of InSAR on GNSS, with 95% CI.
- Velocity over $[t_0, t_1]$ for each series, with 95% CI from
  Newey-West-corrected linear regression.
- Velocity difference (InSAR − GNSS) in mm/yr with 95% CI from a paired
  bootstrap over epochs.
- $\sigma$-coverage at $1\sigma$ and $2\sigma$ when product uncertainty
  is available, computed by `disp_s1_eval.metrics.uncertainty_coverage`.

## 6. Per-station verdict

A station is validated for $P$ when all of the following hold:

1. $|\text{velocity difference}| \leq 2.0$ mm/yr.
2. RMSE of the residual $\leq 5.0$ mm.
3. Velocity difference 95% CI excludes a magnitude of 5 mm/yr.
4. Pearson $r \geq 0.7$ when the GNSS series shows a clear trend
   ($|v_{GNSS}| \geq 2$ mm/yr); otherwise the correlation criterion is
   reported but does not enter the verdict (correlation against a flat
   series is not informative).

Defaults are consistent with published Sentinel-1 validation practice
and may be tightened or relaxed per experiment; the chosen values are
recorded in the manifest.

## 7. Aggregate verdict

Across the validation set, the framework reports:

- The fraction of stations with a positive verdict.
- The product-wide bias and its 95% CI from a station-resampling
  bootstrap.
- The product-wide RMSE and its 95% CI from the same bootstrap.
- Spatial maps of per-station residual statistics.
- A variogram of the residual field as defined in
  [`docs/methodology.md`](methodology.md) §5, reporting nugget, sill,
  and range.

A product passes the aggregate verdict when at least 75% of admitted
stations have a positive per-station verdict and the product-wide bias
95% CI includes zero. The threshold is reportable, not punitive: an
experiment may report a failed verdict and analyze why.

## 8. Multiple-product comparisons

When an experiment evaluates several products jointly, the framework
additionally reports:

- A paired bootstrap of per-station bias differences between every pair.
- A Holm-corrected family-wise table of pairwise tests.
- A variance-decomposition (one-way ANOVA over residuals with product as
  the factor; mixed-effects with station as a random intercept when
  station counts allow).

## 9. Sensitivity branches

Each primary experiment includes sensitivity sub-sections covering:

- Reference-point bootstrap (§6 of methodology).
- Coherence-threshold sweep ($\gamma \in \{0.3, 0.5, 0.7\}$ by default).
- Atmospheric-correction switch (native vs ERA5-only vs uncorrected when
  the product permits).
- Temporal collocation strategy (§3 of this protocol).

The primary verdict is reported under default settings; the sensitivity
branches indicate how robust the verdict is to those choices.

## 10. Reporting format

Every experiment produces, at minimum:

- `results/per_station.csv` — one row per station, all metrics.
- `results/aggregate.json` — aggregate statistics with confidence
  intervals.
- `results/figures/` — at least: residual histogram, residual variogram,
  per-station bias map, time-series for the three best- and worst-fit
  stations, sensitivity panels.
- `results/manifest.json` — see [`methodology.md`](methodology.md) §8.
- `results/summary.md` — a short prose summary generated from the JSON.
