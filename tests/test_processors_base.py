import numpy as np
import pytest

from disp_s1_eval.processors.base import (
    BBox,
    DeformationProductReader,
    LOSGeometry,
    ProductMetadata,
    ProductSample,
    ReaderRegistry,
    available_readers,
    resolve_reader,
    select_aoi_indices,
)
from disp_s1_eval.processors import OperaDispS1Reader, MintPyReader


def test_bbox_rejects_inverted_bounds():
    with pytest.raises(ValueError):
        BBox(west=10.0, south=0.0, east=5.0, north=10.0)
    with pytest.raises(ValueError):
        BBox(west=0.0, south=10.0, east=10.0, north=5.0)


def test_bbox_contains_inside_and_outside():
    bbox = BBox(west=-121.0, south=35.0, east=-119.0, north=37.0)
    assert bbox.contains(-120.0, 36.0)
    assert not bbox.contains(-118.0, 36.0)


def test_los_geometry_validates_shapes():
    inc = np.zeros((3, 3))
    head = np.zeros((3, 3))
    los = np.zeros((3, 3, 3))
    LOSGeometry(incidence=inc, heading=head, los_unit=los)
    with pytest.raises(ValueError):
        LOSGeometry(incidence=inc, heading=np.zeros((4, 4)), los_unit=los)
    with pytest.raises(ValueError):
        LOSGeometry(incidence=inc, heading=head, los_unit=np.zeros((2, 3, 3)))


def test_product_sample_validates_displacement_shape():
    geom = LOSGeometry(
        incidence=np.zeros((2, 3)),
        heading=np.zeros((2, 3)),
        los_unit=np.zeros((3, 2, 3)),
    )
    meta = ProductMetadata(processor="UNIT", product_id="X")
    with pytest.raises(ValueError):
        ProductSample(
            dates=(),
            longitude=np.array([0.0, 1.0, 2.0]),
            latitude=np.array([0.0, 1.0]),
            displacement=np.zeros((1, 2, 3)),
            geometry=geom,
            metadata=meta,
        )


def test_select_aoi_indices_returns_inside_slice():
    lon = np.linspace(-121.0, -119.0, 5)
    lat = np.linspace(35.0, 37.0, 5)
    bbox = BBox(west=-120.5, south=35.5, east=-119.5, north=36.5)
    lat_slice, lon_slice = select_aoi_indices(lon, lat, bbox)
    assert lon[lon_slice].min() >= -120.5
    assert lon[lon_slice].max() <= -119.5
    assert lat[lat_slice].min() >= 35.5
    assert lat[lat_slice].max() <= 36.5


def test_select_aoi_indices_raises_when_outside():
    lon = np.linspace(-121.0, -119.0, 5)
    lat = np.linspace(35.0, 37.0, 5)
    bbox = BBox(west=10.0, south=0.0, east=11.0, north=1.0)
    with pytest.raises(ValueError):
        select_aoi_indices(lon, lat, bbox)


def test_reader_registry_resolves_known_names():
    names = available_readers()
    assert "opera_disp_s1" in names
    assert "mintpy" in names
    assert "miaplpy" in names
    assert "hyp3_sbas" in names
    assert "pygmtsar" in names


def test_reader_registry_rejects_duplicate_registration():
    registry = ReaderRegistry()
    registry.register("dummy", lambda **_: None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        registry.register("dummy", lambda **_: None)  # type: ignore[arg-type]


def test_reader_registry_unknown_name_raises():
    with pytest.raises(KeyError):
        resolve_reader("not_a_real_processor")


def test_opera_reader_constructor_validates_filenames(tmp_path):
    bad = tmp_path / "not_a_disp_s1_file.nc"
    bad.write_text("placeholder")
    with pytest.raises(ValueError):
        OperaDispS1Reader([bad])


def test_opera_reader_metadata_reports_frame_and_polarization(tmp_path):
    name = (
        "OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_20180114T015035Z_v1.0_"
        "20240101T000000Z.nc"
    )
    path = tmp_path / name
    path.write_text("placeholder")
    reader = OperaDispS1Reader([path])
    meta = reader.metadata()
    assert meta.processor == "OPERA_DISP-S1"
    assert meta.polarization == "VV"
    assert meta.extra["frame_id"] == "F08882"
    assert isinstance(reader, DeformationProductReader)


def test_opera_reader_polarization_filter(tmp_path):
    vv_name = (
        "OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_20180114T015035Z_v1.0_"
        "20240101T000000Z.nc"
    )
    vh_name = vv_name.replace("_VV_", "_VH_")
    (tmp_path / vv_name).write_text("placeholder")
    (tmp_path / vh_name).write_text("placeholder")
    reader = OperaDispS1Reader(
        [tmp_path / vv_name, tmp_path / vh_name],
        polarization_filter="VH",
    )
    assert reader.metadata().polarization == "VH"


def test_mintpy_reader_requires_existing_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        MintPyReader(tmp_path / "missing_ts.h5", tmp_path / "missing_geo.h5")
