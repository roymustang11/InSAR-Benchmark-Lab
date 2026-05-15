"""OPERA DISP-S1 search and local-cache helpers.

Network access is kept behind small injectable functions so tests remain
offline. Live experiments can pass the default fetcher, while unit tests
use an in-memory byte fetcher.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlparse

from disp_s1_eval.opera import (
    OPERA_DISP_S1_SHORT_NAME,
    granule_to_inventory_record,
    parse_opera_disp_s1_filename,
)
from disp_s1_eval.processors import BBox


@dataclass(frozen=True)
class CachedDownload:
    """Metadata for a downloaded or reused cache file."""

    url: str
    path: Path
    sha256: str
    size_bytes: int
    reused_existing: bool


def build_disp_s1_search_query(
    bbox: BBox,
    *,
    start: date,
    end: date,
    limit: int = 100,
) -> dict[str, object]:
    """Return earthaccess/CMR search parameters for OPERA DISP-S1."""
    if end < start:
        raise ValueError("end date must be on or after start date")
    if limit <= 0:
        raise ValueError("limit must be positive")
    return {
        "short_name": OPERA_DISP_S1_SHORT_NAME,
        "bounding_box": (bbox.west, bbox.south, bbox.east, bbox.north),
        "temporal": (
            f"{start.isoformat()}T00:00:00Z",
            f"{end.isoformat()}T23:59:59Z",
        ),
        "count": int(limit),
    }


def cached_download(
    url: str,
    cache_dir: str | Path,
    *,
    filename: str | None = None,
    fetcher: Callable[[str], bytes] | None = None,
) -> CachedDownload:
    """Download ``url`` into ``cache_dir`` unless the file already exists."""
    out_dir = Path(cache_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = filename or _filename_from_url(url)
    if not out_name:
        raise ValueError("cached_download requires a URL with a filename or explicit filename")
    out_path = out_dir / out_name

    reused = out_path.exists()
    if not reused:
        content = (fetcher or _requests_fetcher)(url)
        out_path.write_bytes(content)

    return CachedDownload(
        url=url,
        path=out_path,
        sha256=_file_sha256(out_path),
        size_bytes=out_path.stat().st_size,
        reused_existing=reused,
    )


def search_disp_s1_granules(
    bbox: BBox,
    *,
    start: date,
    end: date,
    limit: int = 100,
    search_fn: Callable[..., Iterable[Any]] | None = None,
) -> list[dict[str, Any]]:
    """Search OPERA DISP-S1 granules and return inventory records."""
    query = build_disp_s1_search_query(bbox, start=start, end=end, limit=limit)
    records = []
    for granule in (search_fn or _earthaccess_search)(**query):
        records.append(granule_to_inventory_record(granule))
    return records


def download_disp_s1_granules(
    records: Iterable[dict[str, Any]],
    cache_dir: str | Path,
    *,
    fetcher: Callable[[str], bytes] | None = None,
) -> list[CachedDownload]:
    """Download the NetCDF links in DISP-S1 inventory records."""
    downloads: list[CachedDownload] = []
    for record in records:
        link = record.get("netcdf_link")
        if not link:
            continue
        downloads.append(
            cached_download(str(link), cache_dir, fetcher=fetcher or earthaccess_fetcher)
        )
    return downloads


def local_granule_inventory(paths: Iterable[str | Path]) -> list[dict[str, object]]:
    """Return a sorted inventory for local DISP-S1 granules."""
    rows = []
    for value in paths:
        path = Path(value)
        product = parse_opera_disp_s1_filename(path.name)
        rows.append(
            {
                "path": str(path),
                "short_name": product.short_name,
                "mode": product.mode,
                "frame_id": product.frame_id,
                "polarization": product.polarization,
                "reference_datetime": product.reference_datetime,
                "secondary_datetime": product.secondary_datetime,
                "product_version": product.product_version,
                "processing_datetime": product.processing_datetime,
                "extension": product.extension,
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    return sorted(rows, key=lambda row: str(row["secondary_datetime"]))


def _earthaccess_search(**query: object) -> Iterable[Any]:
    try:
        import earthaccess  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "search_disp_s1_granules requires earthaccess; "
            "install with `pip install -e .[io,notebooks]`"
        ) from exc
    return earthaccess.search_data(**query)


def earthaccess_fetcher(
    url: str,
    *,
    earthaccess_module: Any | None = None,
    auth_strategy: str = "netrc",
    timeout_seconds: float = 60.0,
) -> bytes:
    """Fetch an Earthdata-protected URL through an authenticated earthaccess session."""
    if earthaccess_module is None:
        try:
            import earthaccess as earthaccess_module  # type: ignore[import-not-found,no-redef]
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "earthaccess_fetcher requires earthaccess; "
                "install with `pip install -e .[io,notebooks]`"
            ) from exc

    earthaccess_module.login(strategy=auth_strategy, persist=False)
    session = earthaccess_module.get_requests_https_session()
    response = session.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.content


def _requests_fetcher(url: str) -> bytes:
    try:
        import requests  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "cached_download requires requests for live downloads; "
            "install with `pip install -e .[io]`"
        ) from exc

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    return Path(parsed.path).name


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
