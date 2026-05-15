from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


OPERA_DISP_S1_SHORT_NAME = "OPERA_L3_DISP-S1_V1"

_DISP_S1_PATTERN = re.compile(
    r"^(?P<short_name>OPERA_L3_DISP-S1)_"
    r"(?P<mode>[A-Z]+)_"
    r"(?P<frame_id>F\d+)_"
    r"(?P<polarization>[A-Z]{2})_"
    r"(?P<reference_datetime>\d{8}T\d{6}Z)_"
    r"(?P<secondary_datetime>\d{8}T\d{6}Z)_"
    r"(?P<product_version>v\d+\.\d+)_"
    r"(?P<processing_datetime>\d{8}T\d{6}Z)"
    r"(?P<extension>\.nc|\.zarr\.json\.gz)$"
)


@dataclass(frozen=True)
class OperaDispS1Product:
    short_name: str
    mode: str
    frame_id: str
    polarization: str
    reference_datetime: str
    secondary_datetime: str
    product_version: str
    processing_datetime: str
    extension: str


def parse_opera_disp_s1_filename(value: str) -> OperaDispS1Product:
    """Parse an OPERA DISP-S1 filename or URL into product fields."""
    filename = _filename_from_url_or_path(value)
    match = _DISP_S1_PATTERN.match(filename)
    if match is None:
        raise ValueError(f"not an OPERA DISP-S1 filename: {filename}")
    fields = match.groupdict()
    fields["short_name"] = OPERA_DISP_S1_SHORT_NAME
    return OperaDispS1Product(**fields)


def classify_opera_link(url: str) -> str:
    """Classify common OPERA DISP-S1 data and reference links."""
    filename = _filename_from_url_or_path(url)
    if filename.endswith("_short_wavelength_displacement.zarr.json.gz"):
        return "short_wavelength_zarr_reference"
    if filename.endswith(".zarr.json.gz"):
        return "zarr_reference"
    if filename.endswith(".nc"):
        return "netcdf"
    return "other"


def links_by_kind(links: Iterable[str]) -> dict[str, list[str]]:
    """Group OPERA product links by lightweight link kind."""
    grouped = {
        "netcdf": [],
        "zarr_reference": [],
        "short_wavelength_zarr_reference": [],
        "other": [],
    }
    for link in links:
        grouped[classify_opera_link(link)].append(link)
    return grouped


def granule_to_inventory_record(granule: Any) -> dict[str, Any]:
    """Convert an earthaccess DataGranule-like object into a flat inventory row."""
    umm = granule.get("umm", {})
    collection = umm.get("CollectionReference", {})
    temporal = umm.get("TemporalExtent", {}).get("RangeDateTime", {})
    links = granule.data_links() if hasattr(granule, "data_links") else []
    grouped_links = links_by_kind(links)

    netcdf_link = _first_or_none(grouped_links["netcdf"])
    product = _try_parse_product(netcdf_link or _first_or_none(grouped_links["zarr_reference"]))

    record = {
        "granule_id": umm.get("GranuleUR"),
        "short_name": collection.get("ShortName") or OPERA_DISP_S1_SHORT_NAME,
        "version": collection.get("Version"),
        "begin_time": temporal.get("BeginningDateTime"),
        "end_time": temporal.get("EndingDateTime"),
        "size_mb": granule.get("size"),
        "netcdf_link": netcdf_link,
        "zarr_reference_link": _first_or_none(grouped_links["zarr_reference"]),
        "short_wavelength_zarr_reference_link": _first_or_none(grouped_links["short_wavelength_zarr_reference"]),
    }

    if product is not None:
        record.update(
            {
                "mode": product.mode,
                "frame_id": product.frame_id,
                "polarization": product.polarization,
                "reference_datetime": product.reference_datetime,
                "secondary_datetime": product.secondary_datetime,
                "product_version": product.product_version,
                "processing_datetime": product.processing_datetime,
            }
        )
    return record


def extract_zarr_reference_variables(reference_json: dict[str, Any]) -> list[str]:
    """Return top-level array names from a Kerchunk-style Zarr reference JSON object."""
    refs = reference_json.get("refs", {})
    if not isinstance(refs, dict):
        raise ValueError("zarr reference JSON must contain a refs mapping")

    variables = set()
    for key in refs:
        if "/" not in key:
            continue
        top_level, remainder = key.split("/", 1)
        if top_level.startswith(".") or "/" in remainder:
            continue
        if remainder in {".zarray", ".zattrs"}:
            variables.add(top_level)
    return sorted(variables)


def _filename_from_url_or_path(value: str) -> str:
    parsed = urlparse(value)
    path = parsed.path if parsed.scheme else value
    return Path(path).name


def _first_or_none(values: list[str]) -> str | None:
    return values[0] if values else None


def _try_parse_product(value: str | None) -> OperaDispS1Product | None:
    if value is None:
        return None
    try:
        return parse_opera_disp_s1_filename(value)
    except ValueError:
        return None
