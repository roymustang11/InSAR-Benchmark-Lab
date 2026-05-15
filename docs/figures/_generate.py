"""Reproducible generator for the documentation figures.

Run from the repository root:

    python docs/figures/_generate.py

All figures are synthetic and clearly labelled as illustrative. They
exist to communicate the framework's data model and analysis stages, not
to report measurements. Real-data figures are produced by the
experiments under ``experiments/`` and live next to the experiment that
generated them.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyArrow, FancyBboxPatch, Rectangle


OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 130,
    "figure.dpi": 100,
    "savefig.bbox": "tight",
    "image.interpolation": "nearest",
})


def _save(fig: plt.Figure, name: str) -> Path:
    path = OUT_DIR / name
    fig.savefig(path, pil_kwargs={"optimize": True})
    plt.close(fig)
    return path


def _bowl(nx: int = 220, ny: int = 170, depth_mm: float = 80.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.linspace(-1.6, 1.6, nx)
    y = np.linspace(-1.2, 1.2, ny)
    X, Y = np.meshgrid(x, y)
    r2 = (X - 0.15) ** 2 + (Y + 0.05) ** 2
    bowl = -depth_mm * np.exp(-r2 / 0.35)
    secondary = -0.35 * depth_mm * np.exp(-((X + 0.95) ** 2 + (Y - 0.55) ** 2) / 0.18)
    return X, Y, bowl + secondary


def figure_wrapped_phase() -> None:
    X, Y, los_mm = _bowl()
    rng = np.random.default_rng(7)
    los_mm = los_mm + rng.normal(0.0, 1.5, size=los_mm.shape)

    wavelength_mm = 55.5
    los_to_phase = -4.0 * np.pi / wavelength_mm
    phase = los_mm * los_to_phase
    wrapped = (phase + np.pi) % (2.0 * np.pi) - np.pi

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2), constrained_layout=True)

    norm = TwoSlopeNorm(vcenter=0.0, vmin=float(np.nanmin(los_mm)), vmax=float(np.nanmax(los_mm)))
    im0 = axes[0].imshow(
        los_mm,
        extent=(X.min(), X.max(), Y.min(), Y.max()),
        origin="lower",
        cmap="RdBu_r",
        norm=norm,
        aspect="auto",
    )
    axes[0].set_title("LOS displacement (synthetic, illustrative)")
    axes[0].set_xlabel("longitude offset")
    axes[0].set_ylabel("latitude offset")
    cbar0 = fig.colorbar(im0, ax=axes[0], shrink=0.85)
    cbar0.set_label("mm")

    im1 = axes[1].imshow(
        wrapped,
        extent=(X.min(), X.max(), Y.min(), Y.max()),
        origin="lower",
        cmap="twilight",
        vmin=-np.pi,
        vmax=np.pi,
        aspect="auto",
    )
    axes[1].set_title("Wrapped interferometric phase (synthetic)")
    axes[1].set_xlabel("longitude offset")
    axes[1].set_ylabel("latitude offset")
    cbar1 = fig.colorbar(im1, ax=axes[1], shrink=0.85, ticks=[-np.pi, 0, np.pi])
    cbar1.ax.set_yticklabels([r"$-\pi$", "0", r"$+\pi$"])
    cbar1.set_label("rad")

    fig.suptitle(
        "Phase-to-displacement convention used by the framework",
        fontsize=12,
        y=1.04,
    )
    _save(fig, "wrapped_phase_vs_displacement.png")


def figure_coherence_map() -> None:
    rng = np.random.default_rng(11)
    nx, ny = 220, 170
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    X, Y = np.meshgrid(x, y)
    base = 0.85 - 0.55 * Y
    field_decorr = 0.18 * np.exp(-((X - 0.65) ** 2 + (Y - 0.4) ** 2) / 0.02)
    speckle = 0.05 * rng.standard_normal(base.shape)
    coherence = np.clip(base - field_decorr + speckle, 0.05, 0.99)

    fig, ax = plt.subplots(figsize=(6.4, 4.4), constrained_layout=True)
    im = ax.imshow(coherence, origin="lower", cmap="cividis", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_title("Mean temporal coherence (synthetic, illustrative)")
    ax.set_xlabel("range pixel index")
    ax.set_ylabel("azimuth pixel index")
    cbar = fig.colorbar(im, ax=ax, shrink=0.9)
    cbar.set_label(r"$\bar{\gamma}$")
    ax.contour(coherence, levels=[0.3, 0.5, 0.7], colors="white", linewidths=0.6, alpha=0.8)
    _save(fig, "coherence_map.png")


def figure_timeseries() -> None:
    rng = np.random.default_rng(3)
    n = 90
    t = np.linspace(0, 5.0, n)
    velocity_mm_yr = -22.0
    seasonal = 4.0 * np.sin(2.0 * np.pi * t)
    trend = velocity_mm_yr * t
    insar = trend + seasonal + rng.normal(0.0, 2.5, size=n)
    gnss = trend + seasonal + rng.normal(0.0, 1.2, size=n)

    fit_t = np.linspace(t.min(), t.max(), 300)
    insar_trend = velocity_mm_yr * fit_t

    fig, ax = plt.subplots(figsize=(7.6, 4.4), constrained_layout=True)
    ax.scatter(t, insar, s=14, color="#c0392b", alpha=0.85, label="OPERA DISP-S1 (synthetic)")
    ax.scatter(t, gnss, s=14, color="#2c3e50", alpha=0.85, label="GNSS LOS (synthetic)")
    ax.plot(fit_t, insar_trend, color="#7f8c8d", linestyle="--", linewidth=1.2,
            label=f"Linear fit, {velocity_mm_yr:.0f} mm/yr")
    ax.axhline(0.0, color="black", linewidth=0.5)
    ax.set_xlabel("years from reference epoch")
    ax.set_ylabel("LOS displacement (mm)")
    ax.set_title("Co-located displacement time series (illustrative)")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(True, linewidth=0.4, alpha=0.4)
    _save(fig, "timeseries_insar_vs_gnss.png")


def figure_variogram() -> None:
    distances = np.linspace(0.5, 60.0, 14)
    nugget = 1.4
    sill = 6.5
    range_ = 18.0
    rng = np.random.default_rng(9)
    model = nugget + (sill - nugget) * (1.0 - np.exp(-distances / range_))
    empirical = model + rng.normal(0.0, 0.35, size=distances.size)

    fine = np.linspace(0.0, 60.0, 400)
    fitted = nugget + (sill - nugget) * (1.0 - np.exp(-fine / range_))

    fig, ax = plt.subplots(figsize=(6.4, 4.4), constrained_layout=True)
    ax.scatter(distances, empirical, s=36, color="#2c3e50", label="Empirical", zorder=3)
    ax.plot(fine, fitted, color="#c0392b", linewidth=1.5, label="Exponential fit")
    ax.axhline(nugget, color="#7f8c8d", linestyle=":", linewidth=1.0, label=f"Nugget = {nugget:.1f}")
    ax.axhline(sill, color="#34495e", linestyle=":", linewidth=1.0, label=f"Sill = {sill:.1f}")
    ax.axvline(range_, color="#16a085", linestyle=":", linewidth=1.0, label=f"Range = {range_:.0f}")
    ax.set_xlabel("lag distance (km)")
    ax.set_ylabel(r"semivariance $\hat{\gamma}(h)$ (mm$^2$)")
    ax.set_title("Empirical residual variogram with exponential model")
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    ax.grid(True, linewidth=0.4, alpha=0.4)
    _save(fig, "residual_variogram.png")


def figure_los_geometry() -> None:
    fig, ax = plt.subplots(figsize=(6.6, 4.6), constrained_layout=True)
    ax.set_xlim(-1.4, 1.6)
    ax.set_ylim(-0.4, 1.6)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot([-1.2, 1.4], [0, 0], color="#7f8c8d", linewidth=1.0)
    ax.fill_between([-1.2, 1.4], -0.05, 0.0, color="#bdc3c7")
    ax.text(1.4, -0.15, "ground", color="#7f8c8d", ha="right")

    sat_xy = (0.95, 1.25)
    ax.scatter(*sat_xy, s=240, marker="s", color="#34495e", zorder=4)
    ax.text(sat_xy[0] + 0.05, sat_xy[1] + 0.05, "Sentinel-1", color="#34495e")

    ground_xy = (0.0, 0.0)
    ax.annotate(
        "",
        xy=sat_xy,
        xytext=ground_xy,
        arrowprops=dict(arrowstyle="->", color="#c0392b", linewidth=1.8),
    )
    ax.text(0.45, 0.65, r"$\hat{\mathbf{l}}$", color="#c0392b", fontsize=14)

    ax.annotate(
        "",
        xy=(0.0, 0.85),
        xytext=ground_xy,
        arrowprops=dict(arrowstyle="->", color="#16a085", linewidth=1.4),
    )
    ax.text(-0.18, 0.45, "up", color="#16a085")

    theta = np.deg2rad(38.0)
    arc_r = 0.35
    arc_t = np.linspace(np.pi / 2, np.pi / 2 - theta, 60)
    ax.plot(arc_r * np.cos(arc_t), arc_r * np.sin(arc_t), color="black", linewidth=1.0)
    ax.text(0.18, 0.22, r"$\theta$", fontsize=12)

    ax.text(
        -1.3, 1.45,
        (
            r"$d_{\mathrm{LOS}} = \hat{\mathbf{l}}^{\top}\,\mathbf{d}_{\mathrm{ENU}}$"
            "\n"
            r"$\sigma^{2}_{\mathrm{LOS}} = \hat{\mathbf{l}}^{\top}\,\Sigma_{\mathrm{ENU}}\,\hat{\mathbf{l}}$"
        ),
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#bdc3c7"),
    )

    ax.set_title("ENU-to-LOS projection convention (Hanssen 2001 §2.4)")
    _save(fig, "los_geometry.png")


def figure_workflow() -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.6), constrained_layout=True)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.6)
    ax.axis("off")

    blocks = [
        (0.2, 2.5, 1.9, 1.0, "OPERA DISP-S1\nNetCDF granules", "#34495e"),
        (0.2, 1.0, 1.9, 1.0, "NGL GNSS\ntenv3 series", "#34495e"),
        (2.6, 2.5, 1.9, 1.0, "DeformationProductReader\nadapters", "#16a085"),
        (2.6, 1.0, 1.9, 1.0, "ENU \u2192 LOS projection\n(covariance propagated)", "#16a085"),
        (5.0, 1.75, 2.0, 1.0, "Temporal collocation\nnearest / window / Gaussian", "#16a085"),
        (7.4, 2.6, 1.7, 0.9, "Validation metrics\nRMSE, bias, r, velocity", "#c0392b"),
        (7.4, 1.5, 1.7, 0.9, "Error diagnostics\nvariogram, triple coloc.", "#c0392b"),
        (7.4, 0.4, 1.7, 0.9, "Reference-point\nbootstrap", "#c0392b"),
        (9.4, 1.75, 1.5, 1.0, "experiments/\nresults +\nmanifest.json", "#2c3e50"),
    ]
    for x, y, w, h, label, color in blocks:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.04,rounding_size=0.15",
                linewidth=1.2,
                edgecolor=color,
                facecolor="white",
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9, color=color)

    arrows = [
        (2.1, 3.0, 2.6, 3.0),
        (2.1, 1.5, 2.6, 1.5),
        (4.5, 3.0, 5.0, 2.55),
        (4.5, 1.5, 5.0, 1.95),
        (7.0, 2.25, 7.4, 2.85),
        (7.0, 2.25, 7.4, 1.95),
        (7.0, 2.25, 7.4, 0.85),
        (9.1, 3.05, 9.4, 2.55),
        (9.1, 1.95, 9.4, 2.25),
        (9.1, 0.85, 9.4, 1.95),
    ]
    for x0, y0, x1, y1 in arrows:
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(arrowstyle="-|>", color="#7f8c8d", linewidth=1.0),
        )

    ax.text(0.2, 4.2, "inputs", fontsize=10, color="#34495e", weight="bold")
    ax.text(2.6, 4.2, "library", fontsize=10, color="#16a085", weight="bold")
    ax.text(7.4, 4.2, "diagnostics", fontsize=10, color="#c0392b", weight="bold")
    ax.text(9.4, 4.2, "artifacts", fontsize=10, color="#2c3e50", weight="bold")

    _save(fig, "workflow.png")


def figure_processor_intercomparison() -> None:
    rng = np.random.default_rng(13)
    n_stations = 32
    bias = {
        "OPERA DISP-S1": rng.normal(-0.4, 1.2, n_stations),
        "MintPy SBAS": rng.normal(0.6, 1.6, n_stations),
        "MiaplPy": rng.normal(-0.2, 1.0, n_stations),
        "HyP3-SBAS": rng.normal(1.1, 2.1, n_stations),
        "PyGMTSAR": rng.normal(0.3, 1.4, n_stations),
    }

    fig, ax = plt.subplots(figsize=(7.4, 4.4), constrained_layout=True)
    positions = np.arange(len(bias))
    bp = ax.boxplot(
        list(bias.values()),
        positions=positions,
        widths=0.55,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=1.2),
    )
    palette = ["#c0392b", "#16a085", "#2980b9", "#8e44ad", "#d35400"]
    for patch, color in zip(bp["boxes"], palette, strict=True):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)

    ax.axhline(0.0, color="black", linewidth=0.6, linestyle="--")
    ax.set_xticks(positions)
    ax.set_xticklabels(list(bias), rotation=12)
    ax.set_ylabel("per-station bias vs GNSS (mm/yr)")
    ax.set_title("Cross-processor velocity bias (illustrative)")
    ax.grid(True, linewidth=0.4, alpha=0.4, axis="y")
    _save(fig, "processor_intercomparison.png")


def main() -> None:
    figure_workflow()
    figure_wrapped_phase()
    figure_coherence_map()
    figure_timeseries()
    figure_variogram()
    figure_los_geometry()
    figure_processor_intercomparison()


if __name__ == "__main__":
    main()
