# Methodology

This document specifies the geodetic and statistical conventions used by every
experiment. Ambiguity in reference frames, line-of-sight geometry, atmospheric
correction, or the noise model invalidates inter-product comparisons, so the
conventions are stated up front. Any experiment that deviates from them must
record the deviation in its own `README.md` and `results/manifest.json`.

## 1. Coordinate systems and units

- Horizontal coordinates: WGS84 / EPSG:4326 unless the experiment states a
  projected CRS, in which case the authority code is recorded in
  `results/manifest.json`.
- Vertical reference: ellipsoidal heights for raw GNSS, converted to EGM2008
  geoid heights only when comparing to leveling. InSAR products measure
  relative line-of-sight displacement, not absolute height.
- Time: UTC ISO-8601. Time-series epochs use the SLC sensing-mid time of the
  secondary acquisition for DISP-S1 and the analogous epoch for other
  processors.
- Displacement units: millimeters, positive toward the satellite (range
  decrease). Sign conventions are unit-tested per adapter.

## 2. Line-of-sight geometry

For a Sentinel-1 acquisition with local incidence angle $\theta$ (radians,
measured from the local vertical) and satellite heading azimuth $\alpha_h$
(radians, clockwise from north), the LOS unit vector pointing **from the
ground toward the satellite** in the local east-north-up (ENU) frame is

$$
\hat{\mathbf{l}} = \begin{bmatrix}
- \sin\theta \,\cos(\alpha_h - 3\pi/2) \\
\phantom{-}\sin\theta \,\sin(\alpha_h - 3\pi/2) \\
\phantom{-}\cos\theta
\end{bmatrix}.
$$

Right-looking acquisitions are assumed; the convention follows Hanssen
(2001) §2.4. Per-pixel $\theta$ and $\alpha_h$ are pulled from the product
when available (DISP-S1 carries `los_east`, `los_north`; MintPy carries
`incidenceAngle` and `azimuthAngle`). When only scalar values are available
the assumption is recorded in the experiment manifest.

A 3-D ENU displacement vector $\mathbf{d}_{ENU}$ projects to LOS as

$$
d_{LOS} = \hat{\mathbf{l}}^{\top} \mathbf{d}_{ENU}.
$$

The covariance of $d_{LOS}$ given $\operatorname{Cov}(\mathbf{d}_{ENU}) =
\Sigma_{ENU}$ is

$$
\sigma^{2}_{LOS} = \hat{\mathbf{l}}^{\top} \Sigma_{ENU} \hat{\mathbf{l}}.
$$

`disp_s1_eval.gnss.project_enu_to_los` and
`disp_s1_eval.gnss.project_enu_covariance_to_los` implement these forms. GNSS
station covariance from NGL `tenv3` columns is propagated through the
quadratic form; the up-only approximation $\sigma_{LOS} \approx \sigma_{up}$
is not used.

## 3. Reference frames

Continuous-GNSS series and InSAR displacement fields are realized in
different reference frames. Supported realizations are listed below; the
choice is recorded per experiment.

| Frame | Source | Notes |
| --- | --- | --- |
| `IGS14` | Native NGL final solutions (`tenv3`). | Default for all GNSS ingestion. |
| `NA12` | NGL plate-fixed solutions. | Used when isolating intra-plate deformation. |
| `insar_native` | Per-product, defined by the chosen InSAR reference pixel and reference epoch. | Always relative; offsets per station are estimated. |

Cross-frame comparison applies a station-wise additive offset (constant
in time) estimated by minimizing the squared residual on a declared
stable sub-window. The offset, its standard error, and the sub-window are
recorded in the manifest. Plate-motion or Euler-pole rotations are never
applied silently; any rigid-block correction is a named transform.

## 4. Atmospheric correction handling

DISP-S1 ships with an ERA5-derived tropospheric correction layer.
`disp_s1_eval.processors.opera` exposes both the corrected and the raw
displacement so the correction can be treated as an experimental factor.
When comparing products with different correction sources (ERA5, GACOS,
MERRA-2), each product is reported under its native correction; the
residual difference then bundles correction model, unwrapping, and
network design. Experiments that isolate the correction model re-apply a
single correction to all products.

Ionospheric correction is not applied for C-band Sentinel-1 by default.
Solid-earth tides are corrected upstream (PySolid for MintPy and MiaplPy,
the OPERA SAS for DISP-S1).

## 5. Noise and error model

For a station $s$ at epoch $t$, the residual between an InSAR product $p$
and the LOS-projected GNSS observation is

$$
r_{p,s,t} = d^{InSAR}_{p,s,t} - d^{GNSS,LOS}_{s,t}.
$$

We model the residual as

$$
r_{p,s,t} = b_{p} + b_{p,s} + \eta_{p,s,t}, \qquad
\eta_{p,s,t} \sim \mathcal{N}(0, \sigma^{2}_{p}(\mathbf{x}_s, t)),
$$

where $b_p$ is a product-wide bias (absorbing reference-frame offsets),
$b_{p,s}$ is a station-specific bias (absorbing local effects such as
monument motion or unmodeled atmosphere), and $\eta_{p,s,t}$ is a
zero-mean noise term whose variance may depend on location and time.
$\sigma^{2}_{p}$ is estimated in three ways:

1. **Empirical residual variance** at each station after removing
   $b_p + b_{p,s}$.
2. **Empirical variogram** of $r_{p,\cdot,t}$ in space and time, fit to a
   nugget + exponential model. Reports the nugget (point error variance),
   sill (full variance), and range (decorrelation length).
3. **Triple collocation** when three independent products covering the
   same station-epoch pairs are available, following McColl et al. (2014):

$$
\sigma_{p}^{2} = \langle (d_p - d_q)(d_p - d_r) \rangle, \qquad p \neq q \neq r,
$$

assuming pairwise-independent errors and a common scale. The independence
assumption is documented per experiment.

## 6. Reference-point sensitivity

Reference-point choice is a nuisance variable. We draw $N$ reference
candidates from a stable mask (coherence threshold, low-deformation
prior, exclusion of urban and agricultural classes) and re-estimate the
per-pixel velocity field under each. The inter-quantile range across the
$N$ realizations is reported as a reference-uncertainty map alongside the
central estimate. Mask, $N$, and seed are recorded in the manifest.

## 7. Statistical reporting

- Confidence intervals are 95% bootstrap percentile intervals over
  station-level resampling, unless a parametric interval is used, in
  which case the parametric assumption is named.
- Hypothesis tests against zero (e.g. "is product P biased relative to
  GNSS?") use a paired bootstrap on station-mean residuals. We report
  the test statistic, the bootstrap-distribution percentile, and the
  number of resamples.
- Multiple-comparison adjustments (Holm or Benjamini-Hochberg) apply
  when more than one product or correction is tested in a single
  experiment; the adjustment method is named in the experiment README.

## 8. Provenance capture

Every experiment writes a `results/manifest.json` containing:

- Python version and platform string.
- Versions of all imported scientific packages (`numpy`, `scipy`,
  `xarray`, `mintpy`, `miaplpy`, `isce3` if used).
- Version of `disp_s1_eval` itself.
- Random seeds.
- Granule identifiers and download URLs.
- GNSS station list with NGL solution timestamp.
- Wall-clock runtime.
- SHA-256 of every committed result artifact.

## 9. Bibliography

- Hanssen, R. F. (2001). *Radar Interferometry: Data Interpretation and
  Error Analysis*. Kluwer.
- Berardino, P., Fornaro, G., Lanari, R., & Sansosti, E. (2002). A new
  algorithm for surface deformation monitoring based on small baseline
  differential SAR interferograms. *IEEE TGRS*, 40(11), 2375–2383.
- Ferretti, A., Prati, C., & Rocca, F. (2001). Permanent scatterers in
  SAR interferometry. *IEEE TGRS*, 39(1), 8–20.
- Ansari, H., De Zan, F., & Bamler, R. (2018). Efficient phase estimation
  for interferogram stacks. *IEEE TGRS*, 56(7), 4109–4125.
- Fattahi, H., & Amelung, F. (2013). DEM error correction in InSAR time
  series. *IEEE TGRS*, 51(7), 4249–4259.
- Yunjun, Z., Fattahi, H., & Amelung, F. (2019). Small baseline InSAR
  time series analysis: Unwrapping error correction and noise reduction.
  *Computers & Geosciences*, 133.
- Bekaert, D. P. S., Walters, R. J., Wright, T. J., Hooper, A. J., &
  Parker, D. J. (2015). Statistical comparison of InSAR tropospheric
  correction techniques. *Remote Sensing of Environment*, 170, 40–47.
- McColl, K. A., Vogelzang, J., Konings, A. G., Entekhabi, D., Piles, M.,
  & Stoffelen, A. (2014). Extended triple collocation: Estimating errors
  and correlation coefficients with respect to an unknown target. *GRL*,
  41, 6229–6236.
- Blewitt, G., Hammond, W. C., & Kreemer, C. (2018). Harnessing the GPS
  data explosion for interdisciplinary science. *EOS*, 99.
- OPERA Project (2024). *OPERA Surface Displacement from Sentinel-1
  (DISP-S1) Algorithm Theoretical Basis Document*, JPL D-108762.
