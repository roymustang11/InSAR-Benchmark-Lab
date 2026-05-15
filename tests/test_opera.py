import pytest
import numpy as np

from disp_s1_eval.opera import (
    OPERA_DISP_S1_SHORT_NAME,
    classify_opera_link,
    extract_zarr_reference_variables,
    granule_to_inventory_record,
    links_by_kind,
    parse_opera_disp_s1_filename,
)
from disp_s1_eval.processors import BBox, OperaDispS1Reader


PRODUCT_URL = (
    "https://datapool.asf.alaska.edu/DISP/OPERA-S1/"
    "OPERA_L3_DISP-S1_IW_F38502_VV_20170707T135945Z_20180103T135947Z_"
    "v1.0_20250618T101604Z.nc"
)


def test_parse_opera_disp_s1_filename_from_url():
    product = parse_opera_disp_s1_filename(PRODUCT_URL)

    assert product.short_name == OPERA_DISP_S1_SHORT_NAME
    assert product.mode == "IW"
    assert product.frame_id == "F38502"
    assert product.polarization == "VV"
    assert product.reference_datetime == "20170707T135945Z"
    assert product.secondary_datetime == "20180103T135947Z"
    assert product.product_version == "v1.0"
    assert product.processing_datetime == "20250618T101604Z"
    assert product.extension == ".nc"


def test_parse_opera_disp_s1_filename_rejects_unexpected_name():
    with pytest.raises(ValueError, match="not an OPERA DISP-S1 filename"):
        parse_opera_disp_s1_filename("not_an_opera_product.nc")


def test_classify_opera_links():
    assert classify_opera_link(PRODUCT_URL) == "netcdf"
    assert classify_opera_link(PRODUCT_URL.replace(".nc", ".zarr.json.gz")) == "zarr_reference"
    assert (
        classify_opera_link(
            "https://example.test/OPERA_L3_DISP-S1_IW_F38502_VV_short_wavelength_displacement.zarr.json.gz"
        )
        == "short_wavelength_zarr_reference"
    )
    assert classify_opera_link("https://example.test/readme.txt") == "other"


def test_links_by_kind_groups_links():
    grouped = links_by_kind(
        [
            PRODUCT_URL,
            PRODUCT_URL.replace(".nc", ".zarr.json.gz"),
            "https://example.test/OPERA_L3_DISP-S1_IW_F38502_VV_short_wavelength_displacement.zarr.json.gz",
        ]
    )

    assert grouped["netcdf"] == [PRODUCT_URL]
    assert len(grouped["zarr_reference"]) == 1
    assert len(grouped["short_wavelength_zarr_reference"]) == 1


def test_extract_zarr_reference_variables_from_kerchunk_refs():
    reference = {
        "version": 1,
        "refs": {
            ".zgroup": "{}",
            "displacement/.zarray": "{}",
            "displacement/0.0.0": ["file.nc", 0, 10],
            "temporal_coherence/.zarray": "{}",
            "spatial_ref/.zattrs": "{}",
            "metadata/processing/.zattrs": "{}",
        },
    }

    assert extract_zarr_reference_variables(reference) == [
        "displacement",
        "spatial_ref",
        "temporal_coherence",
    ]


def test_granule_to_inventory_record_handles_current_earthaccess_shape():
    class FakeGranule(dict):
        def data_links(self):
            return [
                PRODUCT_URL,
                PRODUCT_URL.replace(".nc", ".zarr.json.gz"),
            ]

    granule = FakeGranule(
        {
            "umm": {
                "GranuleUR": "OPERA_L3_DISP-S1_IW_F38502_VV_20170707T135945Z_20180103T135947Z_v1.0_20250618T101604Z",
                "CollectionReference": {"ShortName": OPERA_DISP_S1_SHORT_NAME, "Version": "1"},
                "TemporalExtent": {
                    "RangeDateTime": {
                        "BeginningDateTime": "2017-07-07T13:59:45Z",
                        "EndingDateTime": "2018-01-03T13:59:47Z",
                    }
                },
            },
            "size": 408.7,
        }
    )

    record = granule_to_inventory_record(granule)

    assert record["granule_id"].startswith("OPERA_L3_DISP-S1")
    assert record["short_name"] == OPERA_DISP_S1_SHORT_NAME
    assert record["netcdf_link"] == PRODUCT_URL
    assert record["zarr_reference_link"].endswith(".zarr.json.gz")
    assert record["frame_id"] == "F38502"


def test_opera_reader_selects_projected_xy_grid(tmp_path):
    xr = pytest.importorskip("xarray")
    pyproj = pytest.importorskip("pyproj")
    crs = pyproj.CRS.from_epsg(32611)
    transformer = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x_values, _ = transformer.transform([-120.1, -120.0, -119.9], [36.0, 36.0, 36.0])
    _, y_values = transformer.transform([-120.0, -120.0, -120.0], [35.9, 36.0, 36.1])
    path = tmp_path / (
        "OPERA_L3_DISP-S1_IW_F08882_VV_20171220T000000Z_"
        "20180101T000000Z_v1.0_20240101T000000Z.nc"
    )
    ds = xr.Dataset(
        data_vars={
            "spatial_ref": ((), 0, {"crs_wkt": crs.to_wkt()}),
            "displacement": (("y", "x"), np.ones((3, 3), dtype=float)),
            "temporal_coherence": (("y", "x"), np.full((3, 3), 0.8, dtype=float)),
        },
        coords={"x": x_values, "y": y_values},
    )
    ds.to_netcdf(path, engine="scipy")

    sample = OperaDispS1Reader([path]).load(
        BBox(west=-120.05, south=35.95, east=-119.95, north=36.05)
    )

    assert sample.displacement.shape == (1, 1, 1)
    assert sample.geometry.los_unit.shape == (3, 1, 1)
    assert sample.longitude[0] == pytest.approx(-120.0, abs=0.02)
    assert sample.latitude[0] == pytest.approx(36.0, abs=0.02)
