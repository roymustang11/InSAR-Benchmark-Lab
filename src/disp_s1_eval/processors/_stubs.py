"""Reader stubs for processors whose I/O adapters are not yet wired.

Each stub registers itself in the default reader registry. Calling
:meth:`load` raises :class:`NotImplementedError` with a message naming
the on-disk artifact the adapter is expected to consume. This lets
experiments declare a processor by name and fail loudly if the I/O has
not been implemented, rather than silently dropping the processor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from disp_s1_eval.processors.base import (
    BBox,
    DeformationProductReader,
    LOSGeometry,
    ProductMetadata,
    ProductSample,
    register_reader,
)


class _StubReader(DeformationProductReader):
    processor_name: str = "stub"
    expected_inputs: str = "(unspecified)"

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs

    def metadata(self) -> ProductMetadata:
        return ProductMetadata(
            processor=self.processor_name,
            product_id=str(self._kwargs.get("product_id", "unknown")),
            extra={"inputs": {k: str(v) for k, v in self._kwargs.items()}},
        )

    def los_geometry(self, aoi: BBox) -> LOSGeometry:  # pragma: no cover - stub
        raise NotImplementedError(self._message())

    def load(self, aoi: BBox) -> ProductSample:  # pragma: no cover - stub
        raise NotImplementedError(self._message())

    def _message(self) -> str:
        return (
            f"{self.processor_name} reader is registered but not yet implemented; "
            f"expected inputs: {self.expected_inputs}"
        )


class MiaplPyReader(_StubReader):
    processor_name = "MiaplPy"
    expected_inputs = "MiaplPy run directory containing 'inverted/' phase-linked time-series"


class Hyp3SbasReader(_StubReader):
    processor_name = "HyP3-SBAS"
    expected_inputs = (
        "directory of ASF HyP3 unwrapped GeoTIFFs plus an SBAS-inversion summary "
        "(e.g. hyp3-sbas time_series.csv) and the corresponding LOS geometry rasters"
    )


class PyGmtsarReader(_StubReader):
    processor_name = "PyGMTSAR"
    expected_inputs = "PyGMTSAR project directory with NetCDF time-series exports and LOS rasters"


register_reader("miaplpy", lambda **kwargs: MiaplPyReader(**kwargs))
register_reader("hyp3_sbas", lambda **kwargs: Hyp3SbasReader(**kwargs))
register_reader("pygmtsar", lambda **kwargs: PyGmtsarReader(**kwargs))


def _list_paths(value: Any) -> list[Path]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [Path(value)]
    return [Path(v) for v in value]
