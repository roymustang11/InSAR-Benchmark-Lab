from pathlib import Path

import pytest

from insar_benchmark_lab.config import StudyAreaConfig, load_study_area_config


def test_load_study_area_config(tmp_path):
    config_path = tmp_path / "study.yml"
    config_path.write_text(
        """
name: Central Valley Subsidence
slug: central-valley-subsidence
application: subsidence
region:
  west: -121.0
  south: 35.0
  east: -119.0
  north: 37.0
time_window:
  start: "2018-01-01"
  end: "2023-12-31"
reference:
  method: stable-area
  notes: Use a documented low-deformation area outside the main bowl.
data_sources:
  insar:
    - OPERA DISP-S1
    - ASF HyP3
  gnss:
    - Nevada Geodetic Laboratory
""",
        encoding="utf-8",
    )

    config = load_study_area_config(config_path)

    assert isinstance(config, StudyAreaConfig)
    assert config.slug == "central-valley-subsidence"
    assert config.region["west"] == pytest.approx(-121.0)
    assert config.time_window["start"] == "2018-01-01"
    assert "OPERA DISP-S1" in config.data_sources["insar"]


def test_config_rejects_missing_required_field(tmp_path):
    config_path = tmp_path / "bad.yml"
    config_path.write_text("name: Missing Slug\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required field: slug"):
        load_study_area_config(config_path)


def test_config_rejects_invalid_bbox_order(tmp_path):
    config_path = tmp_path / "bad_bbox.yml"
    config_path.write_text(
        """
name: Bad Box
slug: bad-box
application: subsidence
region:
  west: -119.0
  south: 35.0
  east: -121.0
  north: 37.0
time_window:
  start: "2018-01-01"
  end: "2023-12-31"
reference:
  method: stable-area
  notes: invalid
data_sources:
  insar: []
  gnss: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="region west must be less than east"):
        load_study_area_config(config_path)


def test_config_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        load_study_area_config(Path("does-not-exist.yml"))
