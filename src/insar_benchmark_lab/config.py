from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FIELDS = (
    "name",
    "slug",
    "application",
    "region",
    "time_window",
    "reference",
    "data_sources",
)


@dataclass(frozen=True)
class StudyAreaConfig:
    name: str
    slug: str
    application: str
    region: dict[str, float]
    time_window: dict[str, str]
    reference: dict[str, str]
    data_sources: dict[str, list[str]]


def load_study_area_config(path: str | Path) -> StudyAreaConfig:
    """Load and validate a study-area YAML configuration."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    with config_path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}

    if not isinstance(raw, dict):
        raise ValueError("study-area config must be a YAML mapping")

    for field in REQUIRED_FIELDS:
        if field not in raw:
            raise ValueError(f"missing required field: {field}")

    region = _validate_region(raw["region"])
    time_window = _validate_string_mapping(raw["time_window"], "time_window", ("start", "end"))
    reference = _validate_string_mapping(raw["reference"], "reference", ("method", "notes"))
    data_sources = _validate_data_sources(raw["data_sources"])

    return StudyAreaConfig(
        name=str(raw["name"]),
        slug=str(raw["slug"]),
        application=str(raw["application"]),
        region=region,
        time_window=time_window,
        reference=reference,
        data_sources=data_sources,
    )


def _validate_region(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError("region must be a mapping")
    required = ("west", "south", "east", "north")
    for key in required:
        if key not in value:
            raise ValueError(f"region missing required field: {key}")
    region = {key: float(value[key]) for key in required}
    if region["west"] >= region["east"]:
        raise ValueError("region west must be less than east")
    if region["south"] >= region["north"]:
        raise ValueError("region south must be less than north")
    return region


def _validate_string_mapping(value: Any, field_name: str, required: tuple[str, ...]) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    for key in required:
        if key not in value:
            raise ValueError(f"{field_name} missing required field: {key}")
    return {key: str(value[key]) for key in value}


def _validate_data_sources(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ValueError("data_sources must be a mapping")
    sources: dict[str, list[str]] = {}
    for key, entries in value.items():
        if not isinstance(entries, list):
            raise ValueError(f"data_sources.{key} must be a list")
        sources[str(key)] = [str(entry) for entry in entries]
    return sources
