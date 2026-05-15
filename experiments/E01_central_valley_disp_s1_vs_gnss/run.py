"""CLI entry point for experiment E01.

Orchestrates the stages from the experiment README: processor
instantiation, GNSS ingestion, collocation, metric computation,
sensitivity analyses, and artifact writing. I/O dependencies (``xarray``,
``h5py``, ``requests``) are imported lazily by the underlying modules.

Numerical steps are delegated to :mod:`disp_s1_eval` so the experiment
is reproducible and auditable from a single command.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from disp_s1_eval import __version__ as framework_version
from disp_s1_eval.errors import empirical_variogram, fit_exponential_variogram
from disp_s1_eval.gnss import (
    download_ngl_station,
    download_station_holdings,
    parse_station_holdings,
    project_enu_covariance_to_los,
    project_enu_to_los,
    read_tenv3_file,
    resolve_collocation,
    select_stations_for_aoi,
)
from disp_s1_eval.metrics import correlation, mae, rmse, trend_bias, uncertainty_coverage
from disp_s1_eval.opera import parse_opera_disp_s1_filename
from disp_s1_eval.opera_access import (
    download_disp_s1_granules,
    local_granule_inventory,
    search_disp_s1_granules,
)
from disp_s1_eval.processors import BBox, OperaDispS1Reader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run experiment E01.")
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to the experiment config.yml.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output directory for results/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the configuration and emit a manifest without running I/O.",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Search/download OPERA inputs and emit inventory artifacts without running station validation.",
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Search OPERA metadata and emit inventory artifacts without downloading products.",
    )
    parser.add_argument(
        "--station-inventory-only",
        action="store_true",
        help="Build GNSS station inventory from NGL holdings without validating displacement.",
    )
    parser.add_argument(
        "--gnss-download-only",
        action="store_true",
        help="Resolve/download NGL tenv3 files and emit station inventory without OPERA processing.",
    )
    parser.add_argument(
        "--use-existing",
        action="store_true",
        help="Use existing cached OPERA granules instead of searching/downloading.",
    )
    parser.add_argument(
        "--limit-granules",
        type=int,
        default=None,
        help="Limit OPERA granule count for smoke tests and incremental runs.",
    )
    parser.add_argument(
        "--limit-stations",
        type=int,
        default=None,
        help="Limit GNSS station count for smoke tests and incremental runs.",
    )
    args = parser.parse_args(argv)

    config = _load_config(args.config)
    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    manifest = _start_manifest(args.config, config)

    if args.dry_run:
        _write_manifest(output_dir / "manifest.json", manifest)
        _write_summary(output_dir / "summary.md", config, mode="dry_run")
        return 0

    if args.search_only:
        records = resolve_opera_records(config, limit_granules=args.limit_granules)
        _write_json(output_dir / "opera_inventory.json", {"granules": records})
        manifest["run_mode"] = "search_only"
        manifest["inputs"] = {"opera_granules": records}
        manifest["outputs"] = _output_checksums(output_dir)
        _write_manifest(output_dir / "manifest.json", manifest)
        _write_summary(output_dir / "summary.md", config, mode="search_only")
        return 0

    if args.station_inventory_only:
        stations = select_e01_station_inventory(config, limit_stations=args.limit_stations)
        _write_station_inventory(output_dir / "gnss_station_inventory.csv", stations)
        manifest["run_mode"] = "station_inventory_only"
        manifest["inputs"] = {
            "gnss_holdings_path": str(_ensure_holdings_file(config)),
            "n_selected_stations": len(stations),
        }
        manifest["outputs"] = _output_checksums(output_dir)
        _write_manifest(output_dir / "manifest.json", manifest)
        _write_summary(output_dir / "summary.md", config, mode="station_inventory_only")
        return 0

    if args.gnss_download_only:
        resolved = resolve_gnss_stations(
            config,
            use_existing=args.use_existing,
            limit_stations=args.limit_stations,
        )
        stations = _stations_from_resolved(config, resolved)
        _write_station_inventory(output_dir / "gnss_station_inventory.csv", stations)
        manifest["run_mode"] = "gnss_download_only"
        manifest["inputs"] = {
            "gnss_stations": [
                {
                    "station_id": item["station_id"],
                    "longitude": item["longitude"],
                    "latitude": item["latitude"],
                    "tenv3_path": str(item["tenv3_path"]),
                    "sha256": _file_sha256(Path(item["tenv3_path"])),
                }
                for item in resolved
            ]
        }
        manifest["outputs"] = _output_checksums(output_dir)
        _write_manifest(output_dir / "manifest.json", manifest)
        _write_summary(output_dir / "summary.md", config, mode="gnss_download_only")
        return 0

    if args.download_only:
        paths = resolve_opera_granule_paths(
            config,
            use_existing=args.use_existing,
            limit_granules=args.limit_granules,
        )
        inventory = local_granule_inventory(paths)
        _write_json(output_dir / "opera_inventory.json", {"granules": inventory})
        manifest["run_mode"] = "download_only"
        manifest["inputs"] = {"opera_granules": inventory}
        manifest["outputs"] = _output_checksums(output_dir)
        _write_manifest(output_dir / "manifest.json", manifest)
        _write_summary(output_dir / "summary.md", config, mode="download_only")
        return 0

    results = _run_wet(
        config,
        output_dir,
        use_existing=args.use_existing,
        limit_granules=args.limit_granules,
        limit_stations=args.limit_stations,
    )
    manifest["run_mode"] = "wet"
    manifest["inputs"] = results["inputs"]
    manifest["outputs"] = _output_checksums(output_dir)
    _write_manifest(output_dir / "manifest.json", manifest)
    _write_summary(output_dir / "summary.md", config, mode="wet")
    return 0


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}
    if not isinstance(config, dict):
        raise ValueError("E01 config must be a YAML mapping")
    for required in ("name", "slug", "study_area", "processor", "gnss", "collocation"):
        if required not in config:
            raise ValueError(f"E01 config missing required field: {required}")
    return config


def _start_manifest(config_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment": config.get("slug", "E01"),
        "framework_version": framework_version,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_path": str(config_path),
        "config_sha256": _file_sha256(config_path),
        "config": config,
        "outputs": {},
    }


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    payload = json.dumps(manifest, indent=2, sort_keys=True, default=_json_default)
    path.write_text(payload + "\n", encoding="utf-8")


def _write_summary(path: Path, config: dict[str, Any], *, mode: str) -> None:
    status_by_mode = {
        "dry_run": "dry-run validation of the experiment configuration.",
        "search_only": "live OPERA metadata search; no product download or station validation.",
        "station_inventory_only": "GNSS station inventory; no product download or station validation.",
        "gnss_download_only": "GNSS station download/cache preparation; no OPERA processing.",
        "download_only": "OPERA product download/cache preparation; no station validation.",
        "wet": "full validation run.",
    }
    lines = [
        f"# {config.get('name', 'E01')}",
        "",
        f"Slug: `{config.get('slug', 'E01')}`",
        "",
        f"Status: {status_by_mode.get(mode, mode)}",
        "",
        "## Configuration summary",
        "",
        f"- Processor: `{config['processor']['name']}`",
        f"- GNSS source: `{config['gnss']['source']}` ({config['gnss']['reference_frame']})",
        f"- Stations declared: {len(config['gnss'].get('stations', []))}",
        f"- Time window: {config['study_area']['time_window']['start']} → {config['study_area']['time_window']['end']}",
        f"- Collocation strategy: `{config['collocation']['strategy']}`",
        "",
        "See `manifest.json` for full provenance and software versions.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _run_wet(
    config: dict[str, Any],
    output_dir: Path,
    *,
    use_existing: bool = False,
    limit_granules: int | None = None,
    limit_stations: int | None = None,
) -> dict[str, Any]:
    bbox = _bbox_from_config(config)
    granule_paths = resolve_opera_granule_paths(
        config,
        use_existing=use_existing,
        limit_granules=limit_granules,
    )
    sample = _load_opera_sample(config, bbox, granule_paths)
    stations = _load_station_series(
        config,
        use_existing=use_existing,
        limit_stations=limit_stations,
    )

    station_timeseries_dir = output_dir / "station_timeseries"
    station_timeseries_dir.mkdir(parents=True, exist_ok=True)

    per_station: list[dict[str, Any]] = []
    skipped_stations: list[dict[str, str]] = []
    residual_records: list[tuple[float, float, float]] = []

    for station in stations:
        try:
            record, series_rows = _evaluate_station(config, sample, station)
        except ValueError as exc:
            skipped_stations.append(
                {"station_id": str(station["station_id"]), "reason": str(exc)}
            )
            continue
        per_station.append(record)
        residual_records.extend(
            (
                float(station["longitude"]),
                float(station["latitude"]),
                float(row["residual_mm"]),
            )
            for row in series_rows
            if np.isfinite(float(row["residual_mm"]))
        )
        _write_station_timeseries(
            station_timeseries_dir / f"{station['station_id']}.csv",
            series_rows,
        )
        _write_station_figure(
            output_dir / "figures" / f"station_{station['station_id']}_timeseries.png",
            station["station_id"],
            series_rows,
        )

    if not per_station:
        raise ValueError("E01 wet run found no stations with enough valid collocations")

    _write_per_station(output_dir / "per_station.csv", per_station)
    _write_skipped_stations(output_dir / "skipped_stations.csv", skipped_stations)
    aggregate = _aggregate_metrics(per_station, residual_records)
    aggregate["n_skipped_stations"] = len(skipped_stations)
    aggregate["skipped_stations"] = skipped_stations
    _write_json(output_dir / "aggregate.json", aggregate)
    _write_residual_histogram(output_dir / "figures" / "residual_histogram.png", residual_records)
    _write_variogram_figure(output_dir / "figures" / "residual_variogram.png", aggregate)

    return {
        "inputs": {
            "opera_granules": [
                {"path": str(path), "sha256": _file_sha256(path)}
                for path in granule_paths
            ],
            "gnss_stations": [
                {
                    "station_id": station["station_id"],
                    "longitude": station["longitude"],
                    "latitude": station["latitude"],
                    "tenv3_path": str(station["tenv3_path"]),
                    "sha256": _file_sha256(Path(station["tenv3_path"])),
                }
                for station in stations
            ],
        }
    }


def _bbox_from_config(config: dict[str, Any]) -> BBox:
    region = config["study_area"]["region"]
    return BBox(
        west=float(region["west"]),
        south=float(region["south"]),
        east=float(region["east"]),
        north=float(region["north"]),
    )


def _load_opera_sample(config: dict[str, Any], bbox: BBox, granule_paths: list[Path]):
    processor = config["processor"]
    reader = OperaDispS1Reader(
        granule_paths,
        apply_atmospheric_correction=bool(
            processor.get("apply_atmospheric_correction", True)
        ),
        polarization_filter=processor.get("polarization_filter"),
    )
    return reader.load(bbox)


def resolve_opera_granule_paths(
    config: dict[str, Any],
    *,
    use_existing: bool = False,
    limit_granules: int | None = None,
    fetcher: Any | None = None,
) -> list[Path]:
    """Resolve OPERA granules from explicit paths, cache, records, or search."""
    processor = config["processor"]
    raw_paths = processor.get("granule_paths")
    if raw_paths:
        paths = [Path(value) for value in raw_paths]
        paths = _filter_opera_paths(paths, processor)
        return _validate_and_limit_granules(paths, limit_granules)

    cache_dir = Path(processor.get("cache_dir", "data/raw/opera/disp_s1"))
    if use_existing or processor.get("use_existing", False):
        paths = sorted(cache_dir.glob("OPERA_L3_DISP-S1*.nc"))
        paths = _filter_opera_paths(paths, processor)
        return _validate_and_limit_granules(paths, limit_granules)

    records = resolve_opera_records(config, limit_granules=limit_granules)
    if limit_granules is not None:
        records = list(records)[: int(limit_granules)]

    downloads = download_disp_s1_granules(records, cache_dir, fetcher=fetcher)
    paths = [download.path for download in downloads]
    return _validate_and_limit_granules(paths, limit_granules)


def resolve_opera_records(
    config: dict[str, Any],
    *,
    limit_granules: int | None = None,
    search_fn: Any | None = None,
) -> list[dict[str, Any]]:
    """Resolve OPERA inventory records from config or live CMR search."""
    processor = config["processor"]
    records = processor.get("download_records")
    if records is not None:
        records = list(records)
    else:
        bbox = _bbox_from_config(config)
        time_window = config["study_area"]["time_window"]
        records = search_disp_s1_granules(
            bbox,
            start=date.fromisoformat(time_window["start"]),
            end=date.fromisoformat(time_window["end"]),
            limit=int(processor.get("search_limit", limit_granules or 100)),
            search_fn=search_fn,
        )
    frame_id = processor.get("frame_id")
    if frame_id:
        records = [record for record in records if record.get("frame_id") == frame_id]
    if limit_granules is not None:
        records = list(records)[: int(limit_granules)]
    return list(records)


def _filter_opera_paths(paths: list[Path], processor: dict[str, Any]) -> list[Path]:
    frame_id = processor.get("frame_id")
    polarization = processor.get("polarization_filter")
    if not frame_id and not polarization:
        return paths
    filtered = []
    for path in paths:
        product = parse_opera_disp_s1_filename(path.name)
        if frame_id and product.frame_id != frame_id:
            continue
        if polarization and product.polarization != polarization:
            continue
        filtered.append(path)
    return filtered


def _validate_and_limit_granules(paths: list[Path], limit_granules: int | None) -> list[Path]:
    if limit_granules is not None:
        paths = paths[: int(limit_granules)]
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(missing[0])
    if not paths:
        raise ValueError("no OPERA DISP-S1 granules resolved for E01")
    return paths


def _load_station_series(
    config: dict[str, Any],
    *,
    use_existing: bool = False,
    limit_stations: int | None = None,
) -> list[dict[str, Any]]:
    stations = resolve_gnss_stations(
        config,
        use_existing=use_existing,
        limit_stations=limit_stations,
    )
    loaded: list[dict[str, Any]] = []
    for item in stations:
        tenv3_path = Path(item["tenv3_path"])
        series = read_tenv3_file(
            tenv3_path,
            station_id=str(item["station_id"]),
            reference_frame=str(config["gnss"].get("reference_frame", "IGS14")),
            longitude=float(item["longitude"]),
            latitude=float(item["latitude"]),
        )
        loaded.append(
            {
                "station_id": str(item["station_id"]),
                "longitude": float(item["longitude"]),
                "latitude": float(item["latitude"]),
                "tenv3_path": tenv3_path,
                "series": series,
            }
        )
    if not loaded:
        raise ValueError("E01 wet run requires at least one GNSS station")
    return loaded


def resolve_gnss_stations(
    config: dict[str, Any],
    *,
    use_existing: bool = False,
    limit_stations: int | None = None,
) -> list[dict[str, Any]]:
    """Resolve GNSS station config entries to local tenv3 paths."""
    gnss = config["gnss"]
    raw_stations = gnss.get("stations", [])
    if not raw_stations:
        raw_stations = _auto_select_station_ids(config)
    if limit_stations is not None:
        raw_stations = list(raw_stations)[: int(limit_stations)]

    cache_dir = Path(gnss.get("cache_dir", "data/raw/ngl"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    holdings_by_id = {
        station.station_id: station
        for station in _read_holdings_if_configured(config)
    }

    resolved: list[dict[str, Any]] = []
    for entry in raw_stations:
        if isinstance(entry, dict):
            station_id = str(entry["station_id"]).upper()
            longitude = float(entry["longitude"])
            latitude = float(entry["latitude"])
            tenv3_path = Path(entry["tenv3_path"]) if "tenv3_path" in entry else cache_dir / f"{station_id}.tenv3"
        else:
            station_id = str(entry).upper()
            if station_id not in holdings_by_id:
                raise ValueError(
                    f"GNSS station {station_id} requires gnss.holdings_path "
                    "with longitude/latitude metadata or a dict station entry"
                )
            holding = holdings_by_id[station_id]
            longitude = float(holding.longitude)
            latitude = float(holding.latitude)
            tenv3_path = cache_dir / f"{station_id}.tenv3"

        if not tenv3_path.exists():
            if use_existing or gnss.get("use_existing", False):
                raise FileNotFoundError(tenv3_path)
            tenv3_path = download_ngl_station(
                station_id,
                cache_dir,
                reference_frame=str(gnss.get("reference_frame", "IGS14")),
            )

        resolved.append(
            {
                "station_id": station_id,
                "longitude": longitude,
                "latitude": latitude,
                "tenv3_path": tenv3_path,
            }
        )

    return resolved


def _auto_select_station_ids(config: dict[str, Any]) -> list[str]:
    holdings = _read_holdings(config)
    if not holdings:
        raise ValueError("gnss.stations is empty and gnss.holdings_path is not configured")
    time_window = config["study_area"]["time_window"]
    selected = select_stations_for_aoi(
        holdings,
        _bbox_from_config(config),
        start=date.fromisoformat(time_window["start"]),
        end=date.fromisoformat(time_window["end"]),
        min_epochs=int(config["gnss"].get("min_epochs", 200)),
    )
    return [station.station_id for station in selected]


def _select_e01_station_inventory(
    config: dict[str, Any],
    *,
    limit_stations: int | None,
):
    holdings = _read_holdings(config)
    time_window = config["study_area"]["time_window"]
    selected = select_stations_for_aoi(
        holdings,
        _bbox_from_config(config),
        start=date.fromisoformat(time_window["start"]),
        end=date.fromisoformat(time_window["end"]),
        min_epochs=int(config["gnss"].get("min_epochs", 200)),
    )
    return selected[: int(limit_stations)] if limit_stations is not None else selected


def select_e01_station_inventory(
    config: dict[str, Any],
    *,
    limit_stations: int | None = None,
):
    return _select_e01_station_inventory(config, limit_stations=limit_stations)


def _stations_from_resolved(config: dict[str, Any], resolved: list[dict[str, Any]]):
    holdings_by_id = {station.station_id: station for station in _read_holdings(config)}
    stations = []
    for item in resolved:
        station = holdings_by_id.get(item["station_id"])
        if station is not None:
            stations.append(station)
    return stations


def _read_holdings(config: dict[str, Any]):
    holdings_path = _ensure_holdings_file(config)
    if not holdings_path.exists():
        raise FileNotFoundError(holdings_path)
    with holdings_path.open("r", encoding="utf-8") as stream:
        return parse_station_holdings(stream)


def _read_holdings_if_configured(config: dict[str, Any]):
    if not config["gnss"].get("holdings_path"):
        return []
    return _read_holdings(config)


def _ensure_holdings_file(config: dict[str, Any]) -> Path:
    path_value = config["gnss"].get("holdings_path")
    if not path_value:
        raise ValueError("gnss.holdings_path is required for station inventory")
    holdings_path = Path(path_value)
    if not holdings_path.exists() and config["gnss"].get("holdings_url"):
        download_station_holdings(
            holdings_path,
            url=str(config["gnss"]["holdings_url"]),
        )
    return holdings_path


def _write_station_inventory(path: Path, stations: list[Any]) -> None:
    fieldnames = ["station_id", "latitude", "longitude", "start", "end", "n_epochs"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for station in stations:
            writer.writerow(
                {
                    "station_id": station.station_id,
                    "latitude": f"{station.latitude:.4f}",
                    "longitude": f"{station.longitude:.4f}",
                    "start": station.start.isoformat(),
                    "end": station.end.isoformat(),
                    "n_epochs": station.n_epochs,
                }
            )


def _evaluate_station(config: dict[str, Any], sample: Any, station: dict[str, Any]):
    y_idx, x_idx = _nearest_pixel(sample, station["longitude"], station["latitude"])
    half_window = int(config.get("masking", {}).get("neighborhood_size", 1)) // 2
    y_slice = slice(max(0, y_idx - half_window), min(sample.latitude.size, y_idx + half_window + 1))
    x_slice = slice(max(0, x_idx - half_window), min(sample.longitude.size, x_idx + half_window + 1))

    insar_mm = np.nanmean(sample.displacement[:, y_slice, x_slice], axis=(1, 2))
    sigma_mm = (
        np.nanmean(sample.uncertainty[:, y_slice, x_slice], axis=(1, 2))
        if sample.uncertainty is not None
        else None
    )

    los_unit = sample.geometry.los_unit[:, y_idx, x_idx]
    gnss = station["series"]
    enu = np.stack([gnss.east_mm, gnss.north_mm, gnss.up_mm], axis=0)
    gnss_los_mm = project_enu_to_los(enu, los_unit)
    gnss_los_sigma_mm = np.sqrt(
        np.asarray(
            [
                project_enu_covariance_to_los(gnss.covariance(i), los_unit)
                for i in range(len(gnss.dates))
            ],
            dtype=float,
        )
    )

    collocator = resolve_collocation(config["collocation"]["strategy"])
    collocation_kwargs = {
        key: value
        for key, value in config["collocation"].items()
        if key != "strategy"
    }
    collocated_gnss = collocator(
        gnss.dates,
        gnss_los_mm,
        sample.dates,
        **collocation_kwargs,
    )
    collocated_sigma = collocator(
        gnss.dates,
        gnss_los_sigma_mm,
        sample.dates,
        **collocation_kwargs,
    )

    valid = np.isfinite(insar_mm) & np.isfinite(collocated_gnss)
    if np.count_nonzero(valid) < 2:
        raise ValueError(f"station {station['station_id']} has fewer than 2 collocated pairs")

    offset = float(np.nanmean(insar_mm[valid] - collocated_gnss[valid]))
    aligned_insar = insar_mm - offset
    residual = aligned_insar - collocated_gnss

    rows = []
    for date_value, insar_value, gnss_value, residual_value, station_sigma in zip(
        sample.dates,
        aligned_insar,
        collocated_gnss,
        residual,
        collocated_sigma,
        strict=True,
    ):
        rows.append(
            {
                "date": date_value.isoformat(),
                "insar_los_mm": float(insar_value),
                "gnss_los_mm": float(gnss_value),
                "residual_mm": float(residual_value),
                "gnss_los_sigma_mm": float(station_sigma),
            }
        )

    record = {
        "station_id": station["station_id"],
        "longitude": station["longitude"],
        "latitude": station["latitude"],
        "n_pairs": int(np.count_nonzero(valid)),
        "rmse_mm": rmse(collocated_gnss[valid], aligned_insar[valid]),
        "mae_mm": mae(collocated_gnss[valid], aligned_insar[valid]),
        "bias_mm": trend_bias(collocated_gnss[valid], aligned_insar[valid]),
        "correlation": correlation(collocated_gnss[valid], aligned_insar[valid]),
        "reference_offset_mm": offset,
        "uncertainty_coverage_1sigma": (
            uncertainty_coverage(
                collocated_gnss[valid],
                aligned_insar[valid],
                sigma_mm[valid],
            )
            if sigma_mm is not None
            else None
        ),
    }
    return record, rows


def _nearest_pixel(sample: Any, longitude: float, latitude: float) -> tuple[int, int]:
    x_idx = int(np.argmin(np.abs(sample.longitude - float(longitude))))
    y_idx = int(np.argmin(np.abs(sample.latitude - float(latitude))))
    return y_idx, x_idx


def _write_station_timeseries(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "date",
        "insar_los_mm",
        "gnss_los_mm",
        "residual_mm",
        "gnss_los_sigma_mm",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_per_station(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "station_id",
        "n_pairs",
        "rmse_mm",
        "mae_mm",
        "bias_mm",
        "correlation",
        "reference_offset_mm",
        "uncertainty_coverage_1sigma",
        "longitude",
        "latitude",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _write_skipped_stations(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["station_id", "reason"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _aggregate_metrics(
    per_station: list[dict[str, Any]],
    residual_records: list[tuple[float, float, float]],
) -> dict[str, Any]:
    residuals = np.asarray([item[2] for item in residual_records], dtype=float)
    aggregate = {
        "n_stations": len(per_station),
        "n_collocated_pairs": int(sum(row["n_pairs"] for row in per_station)),
        "rmse_mm": float(np.sqrt(np.nanmean(residuals**2))) if residuals.size else None,
        "bias_mm": float(np.nanmean(residuals)) if residuals.size else None,
        "mae_mm": float(np.nanmean(np.abs(residuals))) if residuals.size else None,
        "stations": per_station,
    }
    if len(residual_records) >= 3:
        coordinates = np.asarray([[item[0], item[1]] for item in residual_records], dtype=float)
        try:
            bins = empirical_variogram(coordinates, residuals, n_bins=5)
            aggregate["variogram"] = {
                "bins": [bin_item.__dict__ for bin_item in bins],
            }
            if len(bins) >= 3:
                fit = fit_exponential_variogram(bins)
                aggregate["variogram"]["model"] = {
                    "nugget": fit.nugget,
                    "partial_sill": fit.partial_sill,
                    "range": fit.range,
                    "sill": fit.sill,
                }
        except ValueError:
            aggregate["variogram"] = {"bins": []}
    return aggregate


def _write_station_figure(path: Path, station_id: str, rows: list[dict[str, Any]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    dates = [row["date"] for row in rows]
    insar = [row["insar_los_mm"] for row in rows]
    gnss = [row["gnss_los_mm"] for row in rows]
    fig, ax = plt.subplots(figsize=(6.0, 3.5), constrained_layout=True)
    ax.plot(dates, insar, marker="o", label="DISP-S1 LOS")
    ax.plot(dates, gnss, marker="s", label="GNSS LOS")
    ax.set_title(f"{station_id}: collocated displacement")
    ax.set_ylabel("LOS displacement (mm)")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(frameon=False)
    ax.grid(True, linewidth=0.4, alpha=0.4)
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _write_residual_histogram(
    path: Path,
    residual_records: list[tuple[float, float, float]],
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    residuals = [item[2] for item in residual_records]
    fig, ax = plt.subplots(figsize=(5.0, 3.5), constrained_layout=True)
    ax.hist(residuals, bins=min(10, max(1, len(residuals))), color="#2c3e50", alpha=0.8)
    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.set_title("DISP-S1 minus GNSS residuals")
    ax.set_xlabel("residual (mm)")
    ax.set_ylabel("count")
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _write_variogram_figure(path: Path, aggregate: dict[str, Any]) -> None:
    variogram = aggregate.get("variogram", {})
    bins = variogram.get("bins", [])
    if not bins:
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(5.0, 3.5), constrained_layout=True)
    ax.scatter(
        [item["distance"] for item in bins],
        [item["semivariance"] for item in bins],
        color="#2c3e50",
    )
    ax.set_title("Residual variogram")
    ax.set_xlabel("lag distance")
    ax.set_ylabel("semivariance (mm²)")
    ax.grid(True, linewidth=0.4, alpha=0.4)
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _output_checksums(output_dir: Path) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            outputs[str(path.relative_to(output_dir))] = _file_sha256(path)
    return outputs


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
