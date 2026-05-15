from datetime import date
from types import SimpleNamespace

import pytest

from disp_s1_eval.opera_access import (
    CachedDownload,
    build_disp_s1_search_query,
    cached_download,
    download_disp_s1_granules,
    earthaccess_fetcher,
    local_granule_inventory,
    search_disp_s1_granules,
)
from disp_s1_eval.processors import BBox


def test_build_disp_s1_search_query_uses_cmr_expected_fields():
    query = build_disp_s1_search_query(
        BBox(west=-121.0, south=35.0, east=-119.0, north=37.0),
        start=date(2020, 1, 1),
        end=date(2020, 2, 1),
        limit=25,
    )

    assert query["short_name"] == "OPERA_L3_DISP-S1_V1"
    assert query["bounding_box"] == (-121.0, 35.0, -119.0, 37.0)
    assert query["temporal"] == ("2020-01-01T00:00:00Z", "2020-02-01T23:59:59Z")
    assert query["count"] == 25


def test_cached_download_writes_bytes_and_reuses_existing_file(tmp_path):
    calls = []

    def fetcher(url: str) -> bytes:
        calls.append(url)
        return b"disp-s1-bytes"

    first = cached_download(
        "https://example.test/path/product.nc",
        tmp_path,
        fetcher=fetcher,
    )
    second = cached_download(
        "https://example.test/path/product.nc",
        tmp_path,
        fetcher=fetcher,
    )

    assert isinstance(first, CachedDownload)
    assert first.path == second.path
    assert first.sha256 == second.sha256
    assert first.size_bytes == len(b"disp-s1-bytes")
    assert first.path.read_bytes() == b"disp-s1-bytes"
    assert calls == ["https://example.test/path/product.nc"]


def test_cached_download_rejects_url_without_filename(tmp_path):
    with pytest.raises(ValueError, match="filename"):
        cached_download("https://example.test/", tmp_path, fetcher=lambda _: b"x")


def test_local_granule_inventory_parses_disp_s1_filenames(tmp_path):
    first = tmp_path / (
        "OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_"
        "20180114T015035Z_v1.0_20240101T000000Z.nc"
    )
    second = tmp_path / (
        "OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_"
        "20180126T015035Z_v1.0_20240101T000000Z.nc"
    )
    first.write_bytes(b"a")
    second.write_bytes(b"bb")

    inventory = local_granule_inventory([second, first])

    assert [row["secondary_datetime"] for row in inventory] == [
        "20180114T015035Z",
        "20180126T015035Z",
    ]
    assert inventory[0]["frame_id"] == "F08882"
    assert inventory[0]["sha256"]
    assert inventory[1]["size_bytes"] == 2


def test_search_disp_s1_granules_accepts_injected_search_function():
    class FakeGranule(dict):
        def data_links(self):
            return [
                "https://example.test/readme.txt",
                "https://example.test/OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_"
                "20180114T015035Z_v1.0_20240101T000000Z.nc",
            ]

    calls = []

    def fake_search(**kwargs):
        calls.append(kwargs)
        return [FakeGranule({"umm": {"GranuleUR": "G1"}})]

    records = search_disp_s1_granules(
        BBox(west=-121.0, south=35.0, east=-119.0, north=37.0),
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=3,
        search_fn=fake_search,
    )

    assert calls[0]["short_name"] == "OPERA_L3_DISP-S1_V1"
    assert records[0]["granule_id"] == "G1"
    assert records[0]["netcdf_link"].endswith(".nc")
    assert records[0]["frame_id"] == "F08882"


def test_download_disp_s1_granules_downloads_netcdf_links(tmp_path):
    records = [
        {
            "granule_id": "G1",
            "netcdf_link": (
                "https://example.test/OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_"
                "20180114T015035Z_v1.0_20240101T000000Z.nc"
            ),
        }
    ]

    downloads = download_disp_s1_granules(
        records,
        tmp_path,
        fetcher=lambda url: b"granule-bytes",
    )

    assert len(downloads) == 1
    assert downloads[0].path.exists()
    assert downloads[0].path.read_bytes() == b"granule-bytes"


def test_earthaccess_fetcher_uses_authenticated_session():
    calls = []

    class FakeResponse:
        status_code = 200
        content = b"authenticated-bytes"

        def raise_for_status(self):
            calls.append("raise_for_status")

    class FakeSession:
        def get(self, url, timeout):
            calls.append(("get", url, timeout))
            return FakeResponse()

    fake_earthaccess = SimpleNamespace(
        login=lambda strategy, persist: calls.append(("login", strategy, persist)),
        get_requests_https_session=lambda: FakeSession(),
    )

    payload = earthaccess_fetcher(
        "https://example.test/product.nc",
        earthaccess_module=fake_earthaccess,
        auth_strategy="netrc",
        timeout_seconds=12,
    )

    assert payload == b"authenticated-bytes"
    assert calls == [
        ("login", "netrc", False),
        ("get", "https://example.test/product.nc", 12),
        "raise_for_status",
    ]
