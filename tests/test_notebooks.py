import json
from pathlib import Path


def _notebook_text(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", ""))
        for cell in notebook["cells"]
    )


def test_notebook_02_documents_opera_disp_s1_search_path():
    text = _notebook_text(Path("notebooks/02_hyp3_or_opera_to_timeseries.ipynb"))

    assert "OPERA_L3_DISP-S1_V1" in text
    assert "earthaccess.search_data" in text
    assert "RUN_LIVE_SEARCH" in text
    assert "RUN_AUTHENTICATED_INSPECTION" in text
    assert "granule_to_inventory_record" in text
    assert "extract_zarr_reference_variables" in text
    assert ".summary()" not in text


def test_notebook_03_documents_validation_workflow():
    text = _notebook_text(Path("notebooks/03_mintpy_timeseries_validation.ipynb"))

    assert "DEMONSTRATION_DATA" in text
    assert "This is not a real deformation result" in text
    assert "rmse" in text
    assert "velocity_difference" in text
    assert "GNSS" in text


def test_notebook_04_documents_uncertainty_and_reference_sensitivity():
    text = _notebook_text(Path("notebooks/04_uncertainty_and_reference_sensitivity.ipynb"))

    assert "DEMONSTRATION_DATA" in text
    assert "reference_candidates" in text
    assert "uncertainty_coverage" in text
    assert "mask_thresholds" in text


def test_notebook_05_documents_story_map_outputs():
    text = _notebook_text(Path("notebooks/05_deformation_story_map.ipynb"))

    assert "DEMONSTRATION_DATA" in text
    assert "velocity_grid" in text
    assert "benchmark_summary" in text
    assert "figure_panels" in text


def test_all_notebooks_are_valid_json():
    notebook_paths = sorted(Path("notebooks").glob("*.ipynb"))

    assert notebook_paths
    for path in notebook_paths:
        json.loads(path.read_text(encoding="utf-8"))
