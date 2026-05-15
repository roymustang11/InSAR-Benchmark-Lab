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


def test_all_notebooks_are_valid_json():
    notebook_paths = sorted(Path("notebooks").glob("*.ipynb"))

    assert notebook_paths
    for path in notebook_paths:
        json.loads(path.read_text(encoding="utf-8"))
