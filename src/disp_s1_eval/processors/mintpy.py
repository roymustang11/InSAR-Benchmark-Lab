"""MintPy reader.

Loads displacement time-series from a MintPy ``timeseries.h5`` file together
with the companion ``geometryGeo.h5`` (or ``geometryRadar.h5``) for LOS
geometry. ``h5py`` is imported lazily inside :meth:`load`.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np

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


class MintPyReader(DeformationProductReader):
    """Reader for MintPy HDF5 outputs."""

    def __init__(
        self,
        timeseries_h5: str | Path,
        geometry_h5: str | Path,
        *,
        product_id: str | None = None,
    ) -> None:
        self._timeseries_h5 = Path(timeseries_h5)
        self._geometry_h5 = Path(geometry_h5)
        if not self._timeseries_h5.exists():
            raise FileNotFoundError(self._timeseries_h5)
        if not self._geometry_h5.exists():
            raise FileNotFoundError(self._geometry_h5)
        self._product_id = product_id or self._timeseries_h5.stem

    def metadata(self) -> ProductMetadata:
        return ProductMetadata(
            processor="MintPy",
            product_id=self._product_id,
            version=None,
            reference_frame="insar_native",
            extra={
                "timeseries_h5": str(self._timeseries_h5),
                "geometry_h5": str(self._geometry_h5),
            },
        )

    def los_geometry(self, aoi: BBox) -> LOSGeometry:
        return self.load(aoi).geometry

    def load(self, aoi: BBox) -> ProductSample:
        try:
            import h5py  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "MintPyReader.load requires h5py; install with `pip install -e .[io]`"
            ) from exc

        with h5py.File(self._timeseries_h5, "r") as ts:
            attrs = dict(ts.attrs)
            longitude, latitude = _grid_from_mintpy_attrs(attrs)
            lat_slice, lon_slice = select_aoi_indices(longitude, latitude, aoi)
            date_strings = [
                _decode(v) for v in ts["date"][:]  # type: ignore[index]
            ]
            dates = tuple(_yyyymmdd_to_date(s) for s in date_strings)
            displacement = np.asarray(
                ts["timeseries"][:, lat_slice, lon_slice], dtype=float
            ) * _METERS_TO_MM

        with h5py.File(self._geometry_h5, "r") as geo:
            inc = np.asarray(geo["incidenceAngle"][lat_slice, lon_slice], dtype=float)
            head = np.asarray(geo["azimuthAngle"][lat_slice, lon_slice], dtype=float)
            inc_rad = np.deg2rad(inc)
            head_rad = np.deg2rad(head)
            los_e = -np.sin(inc_rad) * np.cos(head_rad - 1.5 * np.pi)
            los_n = np.sin(inc_rad) * np.sin(head_rad - 1.5 * np.pi)
            los_u = np.cos(inc_rad)
            geometry = LOSGeometry(
                incidence=inc_rad,
                heading=head_rad,
                los_unit=np.stack([los_e, los_n, los_u], axis=0),
            )

        sample_lon = np.asarray(longitude[lon_slice], dtype=float)
        sample_lat = np.asarray(latitude[lat_slice], dtype=float)

        return ProductSample(
            dates=dates,
            longitude=sample_lon,
            latitude=sample_lat,
            displacement=displacement,
            geometry=geometry,
            metadata=self.metadata(),
        )


def _grid_from_mintpy_attrs(attrs: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    width = int(attrs["WIDTH"])
    length = int(attrs["LENGTH"])
    x_first = float(attrs["X_FIRST"])
    y_first = float(attrs["Y_FIRST"])
    x_step = float(attrs["X_STEP"])
    y_step = float(attrs["Y_STEP"])
    longitude = x_first + x_step * np.arange(width)
    latitude = y_first + y_step * np.arange(length)
    return longitude, latitude


def _yyyymmdd_to_date(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def _decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _factory(**kwargs: Any) -> MintPyReader:
    return MintPyReader(**kwargs)


register_reader("mintpy", _factory)
