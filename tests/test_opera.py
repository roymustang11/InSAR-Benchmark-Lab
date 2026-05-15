import pytest

from disp_s1_eval.opera import (
    OPERA_DISP_S1_SHORT_NAME,
    classify_opera_link,
    extract_zarr_reference_variables,
    granule_to_inventory_record,
    links_by_kind,
    parse_opera_disp_s1_filename,
)


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
