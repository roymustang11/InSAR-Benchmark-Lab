"""Uniform processor abstraction for InSAR displacement products.

Each supported processor (OPERA DISP-S1, MintPy, MiaplPy, HyP3-SBAS,
PyGMTSAR) is exposed through the :class:`DeformationProductReader`
protocol so experiments compare them under identical collocation,
masking, and reference-frame conventions.

The base layer depends only on the standard library and NumPy. Concrete
adapters import their I/O backends (``xarray``, ``h5py``, ``netCDF4``,
``zarr``) lazily inside their loader methods, so importing the package
does not require the ``[io]`` extras.
"""

from disp_s1_eval.processors.base import (
    BBox,
    DeformationProductReader,
    LOSGeometry,
    ProductMetadata,
    ProductSample,
    ReaderRegistry,
    available_readers,
    register_reader,
    resolve_reader,
)
from disp_s1_eval.processors.opera import OperaDispS1Reader
from disp_s1_eval.processors.mintpy import MintPyReader
from disp_s1_eval.processors._stubs import (
    Hyp3SbasReader,
    MiaplPyReader,
    PyGmtsarReader,
)

__all__ = [
    "Hyp3SbasReader",
    "MiaplPyReader",
    "MintPyReader",
    "PyGmtsarReader",
    "BBox",
    "DeformationProductReader",
    "LOSGeometry",
    "OperaDispS1Reader",
    "ProductMetadata",
    "ProductSample",
    "ReaderRegistry",
    "available_readers",
    "register_reader",
    "resolve_reader",
]
