"""OPERA DISP-S1 reader.

Reads the NetCDF-4 distribution of the OPERA Level-3 DISP-S1 product.
``xarray`` and ``netCDF4`` are imported lazily inside :meth:`load` so the
module can be imported (and the reader registered) without the ``[io]``
extras installed.

The displacement variable is converted to millimeters under the LOS sign
convention of ``docs/methodology.md`` §1 (positive = motion toward the
satellite, range decrease).

Reference: OPERA Project (2024). Surface Displacement from Sentinel-1
(DISP-S1) Algorithm Theoretical Basis Document, NASA JPL D-108762.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from disp_s1_eval.opera import (
    OPERA_DISP_S1_SHORT_NAME,
    parse_opera_disp_s1_filename,
)
from disp_s1_eval.processors.base import (
    BBox,
    DeformationProductReader,
    LOSGeometry,
    ProductMetadata,
    ProductSample,
    register_reader,
    select_aoi_indices,
)


_METERS_TO_MM = 1000.0


class OperaDispS1Reader(DeformationProductReader):
    """Reader for the OPERA Level-3 DISP-S1 NetCDF distribution.

    Parameters:
        granule_paths:    Iterable of paths to per-epoch DISP-S1 NetCDF files.
                          The reader concatenates them along the time axis,
                          sorted by secondary acquisition datetime.
        apply_atmospheric_correction:
                          When True (default), the ERA5 tropospheric correction
                          shipped with the product is added back into the
                          displacement field. When False, the displacement
                          variable is returned as stored, leaving the
                          correction available to the caller as a separate
                          experimental factor.
        polarization_filter:
                          Optional polarization string (``"VV"``, ``"VH"``)
                          used to filter the granule list.
    """

    def __init__(
        self,
        granule_paths: Iterable[str | Path],
        *,
        apply_atmospheric_correction: bool = True,
        polarization_filter: str | None = None,
    ) -> None:
        self._granule_paths = [Path(p) for p in granule_paths]
        if not self._granule_paths:
            raise ValueError("OperaDispS1Reader requires at least one granule path")
        self._apply_atmospheric_correction = bool(apply_atmospheric_correction)
        self._polarization_filter = polarization_filter

        self._parsed = []
        for path in self._granule_paths:
            try:
                parsed = parse_opera_disp_s1_filename(path.name)
            except ValueError as exc:
                raise ValueError(f"granule does not match DISP-S1 naming: {path}") from exc
            if (
                self._polarization_filter is not None
                and parsed.polarization != self._polarization_filter
            ):
                continue
            self._parsed.append((path, parsed))

        if not self._parsed:
            raise ValueError(
                "no granules matched the requested polarization filter "
                f"{self._polarization_filter!r}"
            )

        self._parsed.sort(key=lambda item: item[1].secondary_datetime)

        first = self._parsed[0][1]
        self._frame_id = first.frame_id
        self._polarization = first.polarization
        self._product_version = first.product_version
        for _path, parsed in self._parsed[1:]:
            if parsed.frame_id != self._frame_id:
                raise ValueError("OperaDispS1Reader granules must share a single frame_id")

    def metadata(self) -> ProductMetadata:
        return ProductMetadata(
            processor="OPERA_DISP-S1",
            product_id=f"{OPERA_DISP_S1_SHORT_NAME}_{self._frame_id}",
            version=self._product_version,
            reference_frame="insar_native",
            polarization=self._polarization,
            extra={
                "frame_id": self._frame_id,
                "n_granules": len(self._parsed),
                "apply_atmospheric_correction": self._apply_atmospheric_correction,
            },
        )

    def los_geometry(self, aoi: BBox) -> LOSGeometry:
        sample = self.load(aoi)
        return sample.geometry

    def load(self, aoi: BBox) -> ProductSample:
        try:
            import xarray as xr  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - exercised only when xarray missing
            raise ImportError(
                "OperaDispS1Reader.load requires xarray and netCDF4; "
                "install with `pip install -e .[io]`"
            ) from exc

        first_path, _ = self._parsed[0]
        with xr.open_dataset(first_path, decode_times=True) as ds:
            grid = self._grid_for_aoi(ds, aoi)
            lat_slice, lon_slice = grid["lat_slice"], grid["lon_slice"]
            geometry = self._read_geometry(ds, lat_slice, lon_slice)
            sample_lon = np.asarray(grid["longitude"], dtype=float)
            sample_lat = np.asarray(grid["latitude"], dtype=float)

        dates: list[date] = []
        displacement_stack: list[np.ndarray] = []
        uncertainty_stack: list[np.ndarray] = []
        coherence_stack: list[np.ndarray] = []

        for path, parsed in self._parsed:
            with xr.open_dataset(path, decode_times=True) as ds:
                dates.append(_secondary_datetime_to_date(parsed.secondary_datetime))
                displacement_stack.append(self._read_displacement(ds, lat_slice, lon_slice))
                unc = self._read_optional(ds, ("displacement_uncertainty",), lat_slice, lon_slice)
                if unc is not None:
                    uncertainty_stack.append(unc * _METERS_TO_MM)
                coh = self._read_optional(
                    ds,
                    ("temporal_coherence", "coherence", "phase_similarity"),
                    lat_slice,
                    lon_slice,
                )
                if coh is not None:
                    coherence_stack.append(coh)

        displacement = np.stack(displacement_stack, axis=0)
        uncertainty = np.stack(uncertainty_stack, axis=0) if uncertainty_stack else None
        coherence = np.stack(coherence_stack, axis=0) if coherence_stack else None

        return ProductSample(
            dates=tuple(dates),
            longitude=sample_lon,
            latitude=sample_lat,
            displacement=displacement,
            geometry=geometry,
            metadata=self.metadata(),
            coherence=coherence,
            uncertainty=uncertainty,
        )

    def _read_displacement(self, ds: Any, lat_slice: slice, lon_slice: slice) -> np.ndarray:
        var_name = self._first_present(ds, ("displacement", "los_displacement"))
        data = np.asarray(ds[var_name].values[..., lat_slice, lon_slice], dtype=float)
        if data.ndim == 3:
            data = data[0]
        if (
            self._apply_atmospheric_correction
            and "tropospheric_delay" in ds.variables
        ):
            trop = np.asarray(
                ds["tropospheric_delay"].values[..., lat_slice, lon_slice], dtype=float
            )
            if trop.ndim == 3:
                trop = trop[0]
            data = data + trop
        return data * _METERS_TO_MM

    def _read_geometry(self, ds: Any, lat_slice: slice, lon_slice: slice) -> LOSGeometry:
        if "los_east" in ds.variables and "los_north" in ds.variables:
            los_e = np.asarray(ds["los_east"].values[lat_slice, lon_slice], dtype=float)
            los_n = np.asarray(ds["los_north"].values[lat_slice, lon_slice], dtype=float)
            los_u = np.sqrt(np.clip(1.0 - los_e**2 - los_n**2, 0.0, 1.0))
            incidence = np.arccos(los_u)
            heading = np.arctan2(los_n, los_e)
            los_unit = np.stack([los_e, los_n, los_u], axis=0)
            return LOSGeometry(incidence=incidence, heading=heading, los_unit=los_unit)

        scalar_inc = float(ds.attrs.get("incidence_angle_deg", 38.0)) * np.pi / 180.0
        scalar_head = float(ds.attrs.get("heading_angle_deg", -12.0)) * np.pi / 180.0
        e = -np.sin(scalar_inc) * np.cos(scalar_head - 1.5 * np.pi)
        n = np.sin(scalar_inc) * np.sin(scalar_head - 1.5 * np.pi)
        u = np.cos(scalar_inc)
        shape = (_slice_length(lat_slice), _slice_length(lon_slice))
        los_unit = np.stack(
            [
                np.full(shape, e, dtype=float),
                np.full(shape, n, dtype=float),
                np.full(shape, u, dtype=float),
            ],
            axis=0,
        )
        return LOSGeometry(
            incidence=np.full(shape, scalar_inc, dtype=float),
            heading=np.full(shape, scalar_head, dtype=float),
            los_unit=los_unit,
        )

    @staticmethod
    def _read_optional(
        ds: Any,
        candidates: Iterable[str],
        lat_slice: slice,
        lon_slice: slice,
    ) -> np.ndarray | None:
        for name in candidates:
            if name in ds.variables:
                values = np.asarray(ds[name].values[..., lat_slice, lon_slice], dtype=float)
                if values.ndim == 3:
                    values = values[0]
                return values
        return None

    @staticmethod
    def _first_present(ds: Any, candidates: Iterable[str]) -> str:
        for name in candidates:
            if name in ds.variables:
                return name
        raise KeyError(f"none of {tuple(candidates)} found in dataset variables")

    @staticmethod
    def _coord_array(ds: Any, candidates: Iterable[str]) -> np.ndarray:
        for name in candidates:
            if name in ds.coords or name in ds.variables:
                return np.asarray(ds[name].values, dtype=float)
        raise KeyError(f"none of {tuple(candidates)} found in dataset coordinates")

    @classmethod
    def _grid_for_aoi(cls, ds: Any, aoi: BBox) -> dict[str, Any]:
        if ("longitude" in ds.coords or "longitude" in ds.variables or "lon" in ds.coords or "lon" in ds.variables) and (
            "latitude" in ds.coords or "latitude" in ds.variables or "lat" in ds.coords or "lat" in ds.variables
        ):
            longitude = cls._coord_array(ds, ("longitude", "lon"))
            latitude = cls._coord_array(ds, ("latitude", "lat"))
            lat_slice, lon_slice = select_aoi_indices(longitude, latitude, aoi)
            return {
                "lat_slice": lat_slice,
                "lon_slice": lon_slice,
                "longitude": longitude[lon_slice],
                "latitude": latitude[lat_slice],
            }

        x = cls._coord_array(ds, ("x",))
        y = cls._coord_array(ds, ("y",))
        x_slice, y_slice = cls._projected_aoi_slices(ds, x, y, aoi)
        sample_x = np.asarray(x[x_slice], dtype=float)
        sample_y = np.asarray(y[y_slice], dtype=float)
        center_y = float(sample_y[sample_y.size // 2])
        center_x = float(sample_x[sample_x.size // 2])
        longitude = cls._transform_xy_to_lonlat(ds, sample_x, np.full(sample_x.shape, center_y))[0]
        latitude = cls._transform_xy_to_lonlat(ds, np.full(sample_y.shape, center_x), sample_y)[1]
        return {
            "lat_slice": y_slice,
            "lon_slice": x_slice,
            "longitude": longitude,
            "latitude": latitude,
        }

    @classmethod
    def _projected_aoi_slices(
        cls,
        ds: Any,
        x: np.ndarray,
        y: np.ndarray,
        aoi: BBox,
    ) -> tuple[slice, slice]:
        xs, ys = cls._transform_lonlat_to_xy(
            ds,
            np.asarray([aoi.west, aoi.west, aoi.east, aoi.east], dtype=float),
            np.asarray([aoi.south, aoi.north, aoi.south, aoi.north], dtype=float),
        )
        x_inside = np.flatnonzero((x >= np.nanmin(xs)) & (x <= np.nanmax(xs)))
        y_inside = np.flatnonzero((y >= np.nanmin(ys)) & (y <= np.nanmax(ys)))
        if x_inside.size == 0 or y_inside.size == 0:
            raise ValueError("AOI does not intersect the product grid")
        return (
            slice(int(x_inside[0]), int(x_inside[-1]) + 1),
            slice(int(y_inside[0]), int(y_inside[-1]) + 1),
        )

    @staticmethod
    def _transform_lonlat_to_xy(ds: Any, longitude: np.ndarray, latitude: np.ndarray):
        try:
            from pyproj import CRS, Transformer  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Projected OPERA grids require pyproj; install with `pip install -e .[io]`"
            ) from exc
        crs = CRS.from_wkt(ds["spatial_ref"].attrs["crs_wkt"])
        transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        return transformer.transform(longitude.tolist(), latitude.tolist())

    @staticmethod
    def _transform_xy_to_lonlat(ds: Any, x: np.ndarray, y: np.ndarray):
        try:
            from pyproj import CRS, Transformer  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Projected OPERA grids require pyproj; install with `pip install -e .[io]`"
            ) from exc
        crs = CRS.from_wkt(ds["spatial_ref"].attrs["crs_wkt"])
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        return transformer.transform(x.tolist(), y.tolist())


def _secondary_datetime_to_date(value: str) -> date:
    return datetime.strptime(value, "%Y%m%dT%H%M%SZ").date()


def _slice_length(value: slice) -> int:
    if value.start is None or value.stop is None:
        raise ValueError("slice length requires bounded start and stop")
    return max(0, int(value.stop) - int(value.start))


def _factory(**kwargs: Any) -> OperaDispS1Reader:
    return OperaDispS1Reader(**kwargs)


register_reader("opera_disp_s1", _factory)
