"""Base types for the processor abstraction.

The protocol does not depend on ``xarray`` so that the type contract can
be tested without heavy I/O dependencies. Concrete adapters return
:class:`ProductSample` objects whose ``displacement`` field is a NumPy
array of shape ``(time, y, x)``; coordinate arrays are returned
alongside.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Iterable, Protocol, runtime_checkable

import numpy as np


@dataclass(frozen=True)
class BBox:
    """Geographic bounding box in WGS84 / EPSG:4326 degrees."""

    west: float
    south: float
    east: float
    north: float

    def __post_init__(self) -> None:
        if self.west >= self.east:
            raise ValueError("BBox west must be less than east")
        if self.south >= self.north:
            raise ValueError("BBox south must be less than north")
        if not (-180.0 <= self.west < self.east <= 180.0):
            raise ValueError("BBox longitudes must lie in [-180, 180]")
        if not (-90.0 <= self.south < self.north <= 90.0):
            raise ValueError("BBox latitudes must lie in [-90, 90]")

    def contains(self, lon: float, lat: float) -> bool:
        """Return True when ``(lon, lat)`` lies inside the bounding box."""
        return self.west <= lon <= self.east and self.south <= lat <= self.north


@dataclass(frozen=True)
class LOSGeometry:
    """Per-pixel line-of-sight geometry.

    Angles are in radians. ``incidence`` is measured from the local
    vertical; ``heading`` is the satellite heading azimuth (clockwise from
    north). ``los_unit`` is the unit vector pointing from the ground
    toward the satellite, expressed in ENU with shape ``(3, y, x)``.
    Scalar geometry uses 0-D arrays. Convention: ``docs/methodology.md`` §2.
    """

    incidence: np.ndarray
    heading: np.ndarray
    los_unit: np.ndarray

    def __post_init__(self) -> None:
        if self.los_unit.shape[0] != 3:
            raise ValueError("los_unit first axis must have length 3 (E, N, U)")
        if self.incidence.shape != self.heading.shape:
            raise ValueError("incidence and heading must have the same shape")


@dataclass(frozen=True)
class ProductMetadata:
    """Provenance metadata reported by every reader."""

    processor: str
    product_id: str
    version: str | None = None
    reference_frame: str = "insar_native"
    polarization: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProductSample:
    """A loaded chunk of an InSAR displacement product.

    Attributes:
        dates:           Tuple of acquisition dates of length ``T``.
        longitude:       1-D array of pixel longitudes of length ``X``.
        latitude:        1-D array of pixel latitudes of length ``Y``.
        displacement:    Array of LOS displacement in millimeters with shape
                         ``(T, Y, X)``. Positive values denote motion toward
                         the satellite.
        coherence:       Optional coherence array, shape ``(T, Y, X)`` or
                         ``(Y, X)`` for a temporal mean, dimensionless in
                         ``[0, 1]``.
        uncertainty:     Optional 1-σ displacement uncertainty in millimeters,
                         same shape as ``displacement``.
        geometry:        :class:`LOSGeometry` describing the per-pixel LOS.
        metadata:        :class:`ProductMetadata` with provenance fields.
    """

    dates: tuple[date, ...]
    longitude: np.ndarray
    latitude: np.ndarray
    displacement: np.ndarray
    geometry: LOSGeometry
    metadata: ProductMetadata
    coherence: np.ndarray | None = None
    uncertainty: np.ndarray | None = None

    def __post_init__(self) -> None:
        T = len(self.dates)
        Y = self.latitude.size
        X = self.longitude.size
        if self.displacement.shape != (T, Y, X):
            raise ValueError(
                f"displacement shape {self.displacement.shape} does not match "
                f"(T={T}, Y={Y}, X={X})"
            )
        if self.uncertainty is not None and self.uncertainty.shape != self.displacement.shape:
            raise ValueError("uncertainty must have the same shape as displacement")
        if self.coherence is not None and self.coherence.shape not in {
            self.displacement.shape,
            (Y, X),
        }:
            raise ValueError("coherence must have shape (T, Y, X) or (Y, X)")


@runtime_checkable
class DeformationProductReader(Protocol):
    """Uniform read interface implemented by every processor adapter."""

    def metadata(self) -> ProductMetadata:
        """Return provenance metadata for the underlying product."""

    def los_geometry(self, aoi: BBox) -> LOSGeometry:
        """Return the per-pixel LOS geometry over the AOI."""

    def load(self, aoi: BBox) -> ProductSample:
        """Return a :class:`ProductSample` covering the AOI and full time window."""


class ReaderRegistry:
    """Registry mapping a processor name to a factory callable.

    Used by experiments and CLI entry points to construct readers from a
    string identifier in a configuration file.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[..., DeformationProductReader]] = {}

    def register(
        self,
        name: str,
        factory: Callable[..., DeformationProductReader],
    ) -> None:
        key = name.lower()
        if key in self._factories:
            raise ValueError(f"reader already registered: {name}")
        self._factories[key] = factory

    def resolve(self, name: str, **kwargs: Any) -> DeformationProductReader:
        key = name.lower()
        if key not in self._factories:
            available = ", ".join(sorted(self._factories)) or "(none)"
            raise KeyError(f"unknown reader '{name}'; available: {available}")
        return self._factories[key](**kwargs)

    def names(self) -> list[str]:
        return sorted(self._factories)


_DEFAULT_REGISTRY = ReaderRegistry()


def register_reader(name: str, factory: Callable[..., DeformationProductReader]) -> None:
    """Register a reader factory in the default registry."""
    _DEFAULT_REGISTRY.register(name, factory)


def resolve_reader(name: str, **kwargs: Any) -> DeformationProductReader:
    """Construct a reader from the default registry by name."""
    return _DEFAULT_REGISTRY.resolve(name, **kwargs)


def available_readers() -> list[str]:
    """Return the list of registered reader names in the default registry."""
    return _DEFAULT_REGISTRY.names()


def select_aoi_indices(
    longitude: Iterable[float],
    latitude: Iterable[float],
    aoi: BBox,
) -> tuple[slice, slice]:
    """Return slices into longitude and latitude arrays that cover the AOI.

    The longitude and latitude inputs are assumed to be sorted in either
    ascending or descending order. Useful for adapters whose backing arrays
    are regular grids.
    """
    lon = np.asarray(list(longitude), dtype=float)
    lat = np.asarray(list(latitude), dtype=float)

    lon_inside = np.flatnonzero((lon >= aoi.west) & (lon <= aoi.east))
    lat_inside = np.flatnonzero((lat >= aoi.south) & (lat <= aoi.north))

    if lon_inside.size == 0 or lat_inside.size == 0:
        raise ValueError("AOI does not intersect the product grid")

    return (
        slice(int(lat_inside[0]), int(lat_inside[-1]) + 1),
        slice(int(lon_inside[0]), int(lon_inside[-1]) + 1),
    )
