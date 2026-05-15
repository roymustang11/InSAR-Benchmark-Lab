from datetime import date

import numpy as np
import pytest

from insar_benchmark_lab.timeseries import align_by_date, load_csv_timeseries


def test_load_csv_timeseries_reads_required_columns(tmp_path):
    csv_path = tmp_path / "station.csv"
    csv_path.write_text(
        "date,displacement_mm,sigma_mm\n"
        "2020-01-01,0.0,1.5\n"
        "2020-01-13,2.0,1.8\n",
        encoding="utf-8",
    )

    series = load_csv_timeseries(csv_path, uncertainty_column="sigma_mm", station_id="P123")

    assert series.station_id == "P123"
    assert series.dates == (date(2020, 1, 1), date(2020, 1, 13))
    assert np.allclose(series.displacement_mm, [0.0, 2.0])
    assert np.allclose(series.sigma_mm, [1.5, 1.8])


def test_load_csv_timeseries_rejects_missing_column(tmp_path):
    csv_path = tmp_path / "station.csv"
    csv_path.write_text("date,value\n2020-01-01,1.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required column: displacement_mm"):
        load_csv_timeseries(csv_path)


def test_align_by_date_returns_common_dates_in_order():
    left_dates = [date(2020, 1, 1), date(2020, 1, 13), date(2020, 1, 25)]
    right_dates = [date(2020, 1, 13), date(2020, 1, 25), date(2020, 2, 6)]

    common_dates, left_values, right_values = align_by_date(
        left_dates,
        [0.0, 2.0, 4.0],
        right_dates,
        [10.0, 20.0, 30.0],
    )

    assert common_dates == (date(2020, 1, 13), date(2020, 1, 25))
    assert np.allclose(left_values, [2.0, 4.0])
    assert np.allclose(right_values, [10.0, 20.0])


def test_align_by_date_rejects_no_overlap():
    with pytest.raises(ValueError, match="no overlapping dates"):
        align_by_date(
            [date(2020, 1, 1)],
            [1.0],
            [date(2021, 1, 1)],
            [2.0],
        )
