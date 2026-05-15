import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from experiments.E01_central_valley_disp_s1_vs_gnss.run import (
    main,
    resolve_gnss_stations,
    resolve_opera_records,
    resolve_opera_granule_paths,
)


def test_e01_dry_run_writes_manifest_and_summary(tmp_path):
    config_path = Path("experiments/E01_central_valley_disp_s1_vs_gnss/config.yml")
    output = tmp_path / "results"

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--output",
            str(output),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    manifest_path = output / "manifest.json"
    summary_path = output / "summary.md"
    figures_dir = output / "figures"
    assert manifest_path.exists()
    assert summary_path.exists()
    assert figures_dir.is_dir()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["experiment"] == "E01_central_valley_disp_s1_vs_gnss"
    assert manifest["framework_version"]
    assert "config_sha256" in manifest
    assert manifest["config"]["processor"]["name"] == "opera_disp_s1"

    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Central Valley" in summary_text
    assert "opera_disp_s1" in summary_text


def test_e01_wet_run_writes_real_artifacts_from_local_fixtures(tmp_path):
    xr = pytest.importorskip("xarray")

    granule_paths = _write_opera_fixture_granules(tmp_path, xr)
    tenv3_path = _write_tenv3_fixture(tmp_path)
    config_path = _write_local_e01_config(tmp_path, granule_paths, tenv3_path)
    output = tmp_path / "results"

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert (output / "manifest.json").exists()
    assert (output / "per_station.csv").exists()
    assert (output / "skipped_stations.csv").exists()
    assert (output / "aggregate.json").exists()
    assert (output / "sensitivity.json").exists()
    assert (output / "station_timeseries" / "TEST.csv").exists()
    assert (output / "figures" / "station_TEST_timeseries.png").exists()
    assert (output / "figures" / "residual_histogram.png").exists()
    assert (output / "figures" / "opera_displacement_map.png").exists()
    assert (output / "figures" / "opera_coherence_map.png").exists()
    assert (output / "figures" / "station_coverage_map.png").exists()
    assert (output / "figures" / "station_residual_map.png").exists()
    assert (output / "figures" / "multi_station_timeseries.png").exists()
    assert (output / "figures" / "sensitivity_summary.png").exists()

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_mode"] == "wet"
    assert manifest["inputs"]["opera_granules"][0]["sha256"]
    assert manifest["inputs"]["gnss_stations"][0]["station_id"] == "TEST"

    aggregate = json.loads((output / "aggregate.json").read_text(encoding="utf-8"))
    assert aggregate["n_epochs"] == 3
    assert aggregate["n_stations"] == 1
    assert aggregate["n_collocated_pairs"] == 3
    assert aggregate["median_abs_residual_mm"] < 2.0
    assert aggregate["station_rmse_median_mm"] < 2.0
    assert aggregate["rmse_mm"] < 2.0
    assert aggregate["bootstrap"]["rmse_mm"]["upper"] >= aggregate["bootstrap"]["rmse_mm"]["lower"]
    sensitivity = json.loads((output / "sensitivity.json").read_text(encoding="utf-8"))
    variants = {row["variant"] for row in sensitivity["variants"]}
    assert {
        "primary",
        "collocation_weighted_window",
        "collocation_gaussian_smoothing",
        "coherence_threshold_0.7",
        "reference_stable_window",
    }.issubset(variants)

    per_station = (output / "per_station.csv").read_text(encoding="utf-8")
    assert "insar_trend_mm_per_year,gnss_trend_mm_per_year,trend_difference_mm_per_year" in per_station
    assert "TEST,3," in per_station


def test_e01_wet_run_records_skipped_stations(tmp_path):
    xr = pytest.importorskip("xarray")

    granule_paths = _write_opera_fixture_granules(tmp_path, xr)
    tenv3_path = _write_tenv3_fixture(tmp_path)
    skipped_tenv3 = tmp_path / "SKIP.tenv3"
    skipped_tenv3.write_text(
        "\n".join(
            [
                "SKIP 19JAN01 2019.0014 58484 1980 1 -120.0 "
                "0 0.000 0 0.000 0 0.000 0.000 0.0010 0.0010 0.0010 0.00 0.00 0.00",
                "SKIP 19JAN13 2019.0342 58496 1981 6 -120.0 "
                "0 0.000 0 0.000 0 -0.010 0.000 0.0010 0.0010 0.0010 0.00 0.00 0.00",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config_path = _write_local_e01_config(tmp_path, granule_paths, tenv3_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["gnss"]["stations"].append(
        {
            "station_id": "SKIP",
            "longitude": -120.0,
            "latitude": 36.0,
            "tenv3_path": str(skipped_tenv3),
        }
    )
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    output = tmp_path / "results"

    exit_code = main(["--config", str(config_path), "--output", str(output)])

    assert exit_code == 0
    aggregate = json.loads((output / "aggregate.json").read_text(encoding="utf-8"))
    assert aggregate["n_stations"] == 1
    assert aggregate["n_skipped_stations"] == 1
    skipped = (output / "skipped_stations.csv").read_text(encoding="utf-8")
    assert "SKIP" in skipped


def test_resolve_opera_granule_paths_uses_existing_cache_when_requested(tmp_path):
    granule = tmp_path / (
        "OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_"
        "20180114T015035Z_v1.0_20240101T000000Z.nc"
    )
    granule.write_bytes(b"existing")
    config = {
        "processor": {
            "cache_dir": str(tmp_path),
            "use_existing": True,
        }
    }

    paths = resolve_opera_granule_paths(config, use_existing=True, limit_granules=None)

    assert paths == [granule]


def test_resolve_opera_granule_paths_filters_existing_cache_by_frame(tmp_path):
    wanted = tmp_path / (
        "OPERA_L3_DISP-S1_IW_F09155_VV_20170823T020611Z_"
        "20180102T020611Z_v1.0_20250409T004744Z.nc"
    )
    other = tmp_path / (
        "OPERA_L3_DISP-S1_IW_F38502_VV_20170707T135945Z_"
        "20180103T135947Z_v1.0_20250618T101604Z.nc"
    )
    wanted.write_bytes(b"wanted")
    other.write_bytes(b"other")
    config = {
        "processor": {
            "cache_dir": str(tmp_path),
            "use_existing": True,
            "frame_id": "F09155",
        }
    }

    paths = resolve_opera_granule_paths(config, use_existing=True, limit_granules=None)

    assert paths == [wanted]


def test_resolve_opera_granule_paths_downloads_when_no_local_paths(tmp_path):
    config = {
        "processor": {
            "cache_dir": str(tmp_path),
            "download_records": [
                {
                    "granule_id": "G1",
                    "netcdf_link": (
                        "https://example.test/OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_"
                        "20180114T015035Z_v1.0_20240101T000000Z.nc"
                    ),
                }
            ],
        }
    }

    paths = resolve_opera_granule_paths(
        config,
        use_existing=False,
        limit_granules=1,
        fetcher=lambda url: b"downloaded",
    )

    assert len(paths) == 1
    assert paths[0].exists()
    assert paths[0].read_bytes() == b"downloaded"


def test_resolve_opera_records_uses_injected_search_function():
    config = {
        "study_area": {
            "region": {"west": -121.0, "south": 35.0, "east": -119.0, "north": 37.0},
            "time_window": {"start": "2023-01-01", "end": "2023-01-31"},
        },
        "processor": {"search_limit": 1},
    }

    records = resolve_opera_records(
        config,
        limit_granules=1,
        search_fn=lambda **_: [
            {
                "umm": {
                    "GranuleUR": "G1",
                    "CollectionReference": {"ShortName": "OPERA_L3_DISP-S1_V1"},
                },
                "size": 1,
                "data_links": lambda: [],
            }
        ],
    )

    assert len(records) == 1
    assert records[0]["granule_id"] == "G1"


def test_resolve_opera_records_filters_configured_frame():
    config = {
        "processor": {
            "frame_id": "F09155",
            "download_records": [
                {"granule_id": "A", "frame_id": "F38502"},
                {"granule_id": "B", "frame_id": "F09155"},
            ],
        },
    }

    records = resolve_opera_records(config)

    assert [record["granule_id"] for record in records] == ["B"]


def test_resolve_gnss_stations_uses_station_ids_holdings_and_cache(tmp_path):
    tenv3 = _write_tenv3_fixture(tmp_path)
    holdings_path = tmp_path / "holdings.txt"
    holdings_path.write_text(
        "TEST 36.0 -120.0 2018-01-01 2018-01-31 3\n",
        encoding="utf-8",
    )
    config = {
        "study_area": {
            "region": {"west": -120.2, "south": 35.8, "east": -119.8, "north": 36.2},
            "time_window": {"start": "2018-01-01", "end": "2018-01-31"},
        },
        "gnss": {
            "source": "NGL",
            "reference_frame": "IGS14",
            "cache_dir": str(tmp_path),
            "holdings_path": str(holdings_path),
            "stations": ["TEST"],
        },
    }

    stations = resolve_gnss_stations(config, use_existing=True)

    assert len(stations) == 1
    assert stations[0]["station_id"] == "TEST"
    assert stations[0]["longitude"] == pytest.approx(-120.0)
    assert stations[0]["latitude"] == pytest.approx(36.0)
    assert stations[0]["tenv3_path"] == tenv3


def test_resolve_gnss_stations_applies_station_limit_to_auto_selection(tmp_path):
    first = _write_tenv3_fixture(tmp_path)
    second = tmp_path / "ABCD.tenv3"
    second.write_text(first.read_text(encoding="utf-8").replace("TEST", "ABCD"), encoding="utf-8")
    holdings_path = tmp_path / "holdings.txt"
    holdings_path.write_text(
        "\n".join(
            [
                "TEST 36.0 -120.0 2018-01-01 2018-01-31 3",
                "ABCD 36.1 -120.1 2018-01-01 2018-01-31 3",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config = {
        "study_area": {
            "region": {"west": -120.2, "south": 35.8, "east": -119.8, "north": 36.2},
            "time_window": {"start": "2018-01-01", "end": "2018-01-31"},
        },
        "gnss": {
            "source": "NGL",
            "reference_frame": "IGS20",
            "cache_dir": str(tmp_path),
            "holdings_path": str(holdings_path),
            "min_epochs": 1,
            "stations": [],
        },
    }

    stations = resolve_gnss_stations(config, use_existing=True, limit_stations=1)

    assert len(stations) == 1


def test_e01_download_only_writes_opera_inventory(tmp_path):
    cache_dir = tmp_path / "opera"
    cache_dir.mkdir()
    granule = cache_dir / (
        "OPERA_L3_DISP-S1_IW_F08882_VV_20180102T015035Z_"
        "20180114T015035Z_v1.0_20240101T000000Z.nc"
    )
    granule.write_bytes(b"existing")
    config = {
        "name": "E01 Download Only Fixture",
        "slug": "E01_download_only_fixture",
        "study_area": {
            "region": {"west": -120.2, "south": 35.8, "east": -119.8, "north": 36.2},
            "time_window": {"start": "2018-01-01", "end": "2018-01-31"},
        },
        "processor": {
            "name": "opera_disp_s1",
            "cache_dir": str(cache_dir),
        },
        "gnss": {"source": "NGL", "reference_frame": "IGS14", "stations": []},
        "collocation": {"strategy": "nearest", "max_offset_days": 3},
    }
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    output = tmp_path / "results"

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--output",
            str(output),
            "--download-only",
            "--use-existing",
            "--limit-granules",
            "1",
        ]
    )

    assert exit_code == 0
    inventory = json.loads((output / "opera_inventory.json").read_text(encoding="utf-8"))
    assert len(inventory["granules"]) == 1
    assert inventory["granules"][0]["frame_id"] == "F08882"
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_mode"] == "download_only"


def test_e01_station_inventory_only_writes_filtered_station_csv(tmp_path):
    holdings_path = tmp_path / "holdings.txt"
    holdings_path.write_text(
        "\n".join(
            [
                "Sta Lat(deg) Long(deg) Hgt(m) X(m) Y(m) Z(m) Dtbeg Dtend Dtmod NumSol",
                "KEEP 36.0 -120.0 0 -1 -2 -3 2018-01-01 2026-05-02 2026-05-10 2500",
                "OUTS 39.0 -120.0 0 -1 -2 -3 2018-01-01 2026-05-02 2026-05-10 2500",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config = {
        "name": "E01 Station Inventory Fixture",
        "slug": "E01_station_inventory_fixture",
        "study_area": {
            "region": {"west": -121.0, "south": 35.0, "east": -119.0, "north": 37.0},
            "time_window": {"start": "2018-01-01", "end": "2023-12-31"},
        },
        "processor": {"name": "opera_disp_s1"},
        "gnss": {
            "source": "NGL",
            "reference_frame": "IGS14",
            "holdings_path": str(holdings_path),
            "min_epochs": 200,
            "stations": [],
        },
        "collocation": {"strategy": "nearest", "max_offset_days": 3},
    }
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    output = tmp_path / "results"

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--output",
            str(output),
            "--station-inventory-only",
        ]
    )

    assert exit_code == 0
    station_inventory = (output / "gnss_station_inventory.csv").read_text(encoding="utf-8")
    assert "station_id,latitude,longitude,start,end,n_epochs" in station_inventory
    assert "KEEP,36.0000,-120.0000,2018-01-01,2026-05-02,2500" in station_inventory
    assert "OUTS" not in station_inventory


def test_e01_coverage_only_writes_station_coverage_table(tmp_path):
    xr = pytest.importorskip("xarray")

    granule_paths = _write_opera_fixture_granules(tmp_path, xr)
    holdings_path = tmp_path / "holdings.txt"
    holdings_path.write_text(
        "\n".join(
            [
                "INSI 36.0 -120.0 2018-01-01 2018-01-31 20",
                "MISS 36.8 -120.8 2018-01-01 2018-01-31 20",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config = {
        "name": "E01 Coverage Fixture",
        "slug": "E01_coverage_fixture",
        "study_area": {
            "region": {"west": -120.9, "south": 35.8, "east": -119.8, "north": 36.9},
            "time_window": {"start": "2018-01-01", "end": "2018-01-31"},
        },
        "processor": {
            "name": "opera_disp_s1",
            "granule_paths": [str(path) for path in granule_paths],
            "apply_atmospheric_correction": False,
            "polarization_filter": "VV",
        },
        "gnss": {
            "source": "NGL",
            "reference_frame": "IGS20",
            "holdings_path": str(holdings_path),
            "min_epochs": 1,
            "stations": [],
        },
        "collocation": {"strategy": "nearest", "max_offset_days": 3},
        "masking": {"neighborhood_size": 1},
    }
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    output = tmp_path / "results"

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--output",
            str(output),
            "--coverage-only",
        ]
    )

    assert exit_code == 0
    coverage = (output / "station_coverage.csv").read_text(encoding="utf-8")
    assert "station_id,latitude,longitude,total_pixels,valid_pixels,status" in coverage
    assert "INSI,36.0000,-120.0000,1,1,covered" in coverage
    assert "MISS,36.8000,-120.8000,1,0,outside_product_grid" in coverage


def test_e01_gnss_download_only_writes_station_inventory_from_cached_tenv3(tmp_path):
    tenv3 = _write_tenv3_fixture(tmp_path)
    holdings_path = tmp_path / "holdings.txt"
    holdings_path.write_text(
        "TEST 36.0 -120.0 2018-01-01 2018-01-31 3\n",
        encoding="utf-8",
    )
    config = {
        "name": "E01 GNSS Download Fixture",
        "slug": "E01_gnss_download_fixture",
        "study_area": {
            "region": {"west": -120.2, "south": 35.8, "east": -119.8, "north": 36.2},
            "time_window": {"start": "2018-01-01", "end": "2018-01-31"},
        },
        "processor": {"name": "opera_disp_s1"},
        "gnss": {
            "source": "NGL",
            "reference_frame": "IGS14",
            "cache_dir": str(tmp_path),
            "holdings_path": str(holdings_path),
            "min_epochs": 1,
            "stations": [],
        },
        "collocation": {"strategy": "nearest", "max_offset_days": 3},
    }
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    output = tmp_path / "results"

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--output",
            str(output),
            "--gnss-download-only",
            "--use-existing",
            "--limit-stations",
            "1",
        ]
    )

    assert exit_code == 0
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_mode"] == "gnss_download_only"
    inventory = (output / "gnss_station_inventory.csv").read_text(encoding="utf-8")
    assert "TEST,36.0000,-120.0000,2018-01-01,2018-01-31,3" in inventory
    assert tenv3.exists()


def _write_opera_fixture_granules(tmp_path, xr):
    lat = np.array([35.9, 36.0, 36.1], dtype=float)
    lon = np.array([-120.1, -120.0, -119.9], dtype=float)
    los_east = np.full((3, 3), 0.0, dtype=float)
    los_north = np.full((3, 3), 0.0, dtype=float)
    displacements_m = [0.0, -0.010, -0.020]
    dates = ["20180101T000000Z", "20180113T000000Z", "20180125T000000Z"]
    paths = []
    for idx, (secondary, displacement_m) in enumerate(zip(dates, displacements_m, strict=True)):
        name = (
            "OPERA_L3_DISP-S1_IW_F08882_VV_20171220T000000Z_"
            f"{secondary}_v1.0_20240101T000000Z.nc"
        )
        path = tmp_path / name
        ds = xr.Dataset(
            data_vars={
                "displacement": (("latitude", "longitude"), np.full((3, 3), displacement_m)),
                "displacement_uncertainty": (("latitude", "longitude"), np.full((3, 3), 0.001)),
                "coherence": (("latitude", "longitude"), np.full((3, 3), 0.85)),
                "los_east": (("latitude", "longitude"), los_east),
                "los_north": (("latitude", "longitude"), los_north),
            },
            coords={"latitude": lat, "longitude": lon},
            attrs={"fixture_index": idx},
        )
        ds.to_netcdf(path, engine="scipy")
        paths.append(path)
    return paths


def _write_tenv3_fixture(tmp_path):
    path = tmp_path / "TEST.tenv3"
    path.write_text(
        "\n".join(
            [
                "TEST 18JAN01 2018.0014 58119 1980 1 -120.0 "
                "0 0.000 0 0.000 0 0.000 0.000 0.0010 0.0010 0.0010 0.00 0.00 0.00",
                "TEST 18JAN13 2018.0342 58131 1981 6 -120.0 "
                "0 0.000 0 0.000 0 -0.010 0.000 0.0010 0.0010 0.0010 0.00 0.00 0.00",
                "TEST 18JAN25 2018.0671 58143 1983 4 -120.0 "
                "0 0.000 0 0.000 0 -0.020 0.000 0.0010 0.0010 0.0010 0.00 0.00 0.00",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_local_e01_config(tmp_path, granule_paths, tenv3_path):
    config = {
        "name": "E01 Local Fixture DISP-S1 vs GNSS",
        "slug": "E01_local_fixture",
        "study_area": {
            "region": {"west": -120.2, "south": 35.8, "east": -119.8, "north": 36.2},
            "time_window": {"start": "2018-01-01", "end": "2018-01-31"},
            "stable_subwindow": {"start": "2018-01-01", "end": "2018-01-31"},
        },
        "processor": {
            "name": "opera_disp_s1",
            "granule_paths": [str(path) for path in granule_paths],
            "apply_atmospheric_correction": False,
            "polarization_filter": "VV",
        },
        "gnss": {
            "source": "local_tenv3",
            "reference_frame": "IGS14",
            "stations": [
                {
                    "station_id": "TEST",
                    "longitude": -120.0,
                    "latitude": 36.0,
                    "tenv3_path": str(tenv3_path),
                }
            ],
        },
        "collocation": {"strategy": "nearest", "max_offset_days": 0},
        "masking": {"coherence_threshold": 0.5, "neighborhood_size": 1},
        "reference_point_bootstrap": {
            "n_draws": 10,
            "quantile_low": 0.025,
            "quantile_high": 0.975,
        },
        "random_seed": 7,
    }
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path
