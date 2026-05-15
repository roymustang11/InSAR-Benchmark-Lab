from datetime import date

import numpy as np
import pytest

from disp_s1_eval.gnss import (
    CollocationStrategy,
    collocate_gaussian,
    collocate_nearest,
    collocate_weighted_window,
    download_station_holdings,
    ngl_tenv3_url,
    parse_tenv3,
    parse_station_holdings,
    project_enu_covariance_to_los,
    project_enu_to_los,
    resolve_collocation,
    select_stations_for_aoi,
)
from disp_s1_eval.processors import BBox


_SAMPLE_TENV3 = (
    "P056 18JAN01 2018.0014 58119 1980 1 -120.0 "
    "-2360000 0.001 4170000 0.002 100 0.003 0.000 0.0010 0.0010 0.0030 0.10 0.05 -0.20\n"
    "P056 18JAN02 2018.0041 58120 1980 2 -120.0 "
    "-2360000 0.002 4170000 0.001 100 0.005 0.000 0.0010 0.0010 0.0030 0.10 0.05 -0.20\n"
    "P056 18JAN03 2018.0068 58121 1980 3 -120.0 "
    "-2360000 0.003 4170000 0.000 100 0.007 0.000 0.0010 0.0010 0.0030 0.10 0.05 -0.20\n"
)


def test_parse_tenv3_returns_three_epochs():
    series = parse_tenv3(_SAMPLE_TENV3.splitlines(), longitude=-120.0, latitude=36.5)
    assert len(series.dates) == 3
    assert series.dates[0] == date(2018, 1, 1)
    assert series.station.station_id == "P056"
    assert series.east_mm.shape == (3,)


def test_parse_tenv3_centers_components_to_zero_mean():
    series = parse_tenv3(_SAMPLE_TENV3.splitlines())
    assert pytest.approx(0.0, abs=1e-9) == float(np.mean(series.east_mm))
    assert pytest.approx(0.0, abs=1e-9) == float(np.mean(series.north_mm))
    assert pytest.approx(0.0, abs=1e-9) == float(np.mean(series.up_mm))


def test_covariance_is_symmetric_and_positive_semidefinite():
    series = parse_tenv3(_SAMPLE_TENV3.splitlines())
    cov = series.covariance(0)
    assert cov.shape == (3, 3)
    assert np.allclose(cov, cov.T)
    eigenvalues = np.linalg.eigvalsh(cov)
    assert eigenvalues.min() > -1e-12


def test_parse_tenv3_raises_on_empty():
    with pytest.raises(ValueError):
        parse_tenv3(["# header only\n", "site YYMMMDD\n"])


def test_project_enu_to_los_for_pure_vertical_motion():
    enu = np.array([0.0, 0.0, 5.0])
    los_unit = np.array([0.3, -0.1, np.sqrt(1.0 - 0.09 - 0.01)])
    los = project_enu_to_los(enu, los_unit)
    expected = los_unit[2] * 5.0
    assert los == pytest.approx(expected)


def test_project_enu_covariance_to_los_returns_scalar_for_3x3():
    cov = np.diag([4.0, 9.0, 16.0])
    los_unit = np.array([0.5, 0.5, np.sqrt(0.5)])
    var_los = project_enu_covariance_to_los(cov, los_unit)
    expected = 0.25 * 4.0 + 0.25 * 9.0 + 0.5 * 16.0
    assert var_los == pytest.approx(expected)


def test_project_enu_covariance_supports_batch():
    cov = np.broadcast_to(np.diag([1.0, 1.0, 1.0]), (4, 3, 3)).copy()
    los_unit = np.tile(np.array([0.0, 0.0, 1.0]), (4, 1))
    out = project_enu_covariance_to_los(cov, los_unit)
    assert out.shape == (4,)
    assert np.allclose(out, 1.0)


def test_collocate_nearest_picks_within_window():
    g_dates = [date(2020, 1, 1), date(2020, 1, 7), date(2020, 1, 13)]
    g_values = [1.0, 2.0, 3.0]
    insar_dates = [date(2020, 1, 8)]
    out = collocate_nearest(g_dates, g_values, insar_dates, max_offset_days=3)
    assert out[0] == pytest.approx(2.0)


def test_collocate_nearest_returns_nan_outside_window():
    g_dates = [date(2020, 1, 1)]
    g_values = [5.0]
    insar_dates = [date(2020, 2, 1)]
    out = collocate_nearest(g_dates, g_values, insar_dates, max_offset_days=3)
    assert np.isnan(out[0])


def test_collocate_weighted_window_average_is_unbiased_for_constant_series():
    g_dates = [date(2020, 1, d) for d in range(1, 15)]
    g_values = [5.0] * 14
    out = collocate_weighted_window(g_dates, g_values, [date(2020, 1, 7)], half_window_days=5)
    assert out[0] == pytest.approx(5.0)


def test_collocate_gaussian_matches_constant_signal():
    g_dates = [date(2020, 1, d) for d in range(1, 31)]
    g_values = [3.5] * 30
    out = collocate_gaussian(g_dates, g_values, [date(2020, 1, 15)], sigma_days=5.0)
    assert out[0] == pytest.approx(3.5)


def test_resolve_collocation_returns_correct_function():
    assert resolve_collocation("nearest") is collocate_nearest
    assert resolve_collocation("weighted_window") is collocate_weighted_window
    assert resolve_collocation(CollocationStrategy.GAUSSIAN_SMOOTHING) is collocate_gaussian


def test_parse_station_holdings_reads_station_coordinates_and_epoch_count():
    holdings = parse_station_holdings(
        [
            "# station latitude longitude start end epochs\n",
            "P056 36.5000 -120.1000 2018-01-01 2023-12-31 2000\n",
            "ABCD 40.0000 -118.0000 2020-01-01 2020-12-31 250\n",
        ]
    )

    assert len(holdings) == 2
    assert holdings[0].station_id == "P056"
    assert holdings[0].latitude == pytest.approx(36.5)
    assert holdings[0].longitude == pytest.approx(-120.1)
    assert holdings[0].n_epochs == 2000


def test_parse_station_holdings_reads_native_ngl_dataholdings_format():
    holdings = parse_station_holdings(
        [
            "Sta Lat(deg) Long(deg) Hgt(m) X(m) Y(m) Z(m) Dtbeg Dtend Dtmod NumSol StaOrigName\n",
            "P056 36.1234 -120.1234 100.0 -1 -2 -3 2018-01-01 2026-05-02 2026-05-10 2500\n",
        ]
    )

    assert len(holdings) == 1
    assert holdings[0].station_id == "P056"
    assert holdings[0].latitude == pytest.approx(36.1234)
    assert holdings[0].longitude == pytest.approx(-120.1234)
    assert holdings[0].start == date(2018, 1, 1)
    assert holdings[0].end == date(2026, 5, 2)
    assert holdings[0].n_epochs == 2500


def test_parse_station_holdings_normalizes_0_360_longitudes():
    holdings = parse_station_holdings(
        [
            "P056 36.1234 239.8766 2018-01-01 2026-05-02 2500\n",
        ]
    )

    assert holdings[0].longitude == pytest.approx(-120.1234)


def test_download_station_holdings_writes_fetcher_content(tmp_path):
    path = download_station_holdings(
        tmp_path / "DataHoldings.txt",
        fetcher=lambda url: b"Sta Lat(deg) Long(deg)\n",
    )

    assert path.exists()
    assert "Sta Lat" in path.read_text(encoding="utf-8")


def test_ngl_tenv3_url_uses_current_igs20_layout():
    assert ngl_tenv3_url("P056", reference_frame="IGS20") == (
        "https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/P056.tenv3"
    )
    assert ngl_tenv3_url("P056", reference_frame="NA") == (
        "https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/NA/P056.NA.tenv3"
    )


def test_select_stations_for_aoi_filters_by_bounds_time_and_epochs():
    holdings = parse_station_holdings(
        [
            "KEEP 36.0 -120.0 2018-01-01 2023-12-31 2000\n",
            "OUTS 38.0 -120.0 2018-01-01 2023-12-31 2000\n",
            "TIME 36.1 -120.1 2010-01-01 2011-01-01 2000\n",
            "EPOC 36.2 -120.2 2018-01-01 2023-12-31 50\n",
        ]
    )

    selected = select_stations_for_aoi(
        holdings,
        BBox(west=-121.0, south=35.0, east=-119.0, north=37.0),
        start=date(2018, 1, 1),
        end=date(2023, 12, 31),
        min_epochs=200,
    )

    assert [station.station_id for station in selected] == ["KEEP"]
