import json
from pathlib import Path

from experiments.E01_central_valley_disp_s1_vs_gnss.run import main


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
