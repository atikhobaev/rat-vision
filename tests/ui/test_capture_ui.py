from pathlib import Path
import os

from PIL import Image
import pytest

from tools.capture_ui import capture_ui


pytestmark = pytest.mark.skipif(
    bool(os.environ.get("GITHUB_ACTIONS")),
    reason="GitHub's Windows runner display is narrower than the approved 1180px capture width",
)


def test_capture_ui_writes_approved_window_size(tmp_path):
    output = tmp_path / "night.png"
    capture_ui("night", output)
    with Image.open(output) as image:
        assert image.size == (1180, 760)


def test_capture_ui_cli_runs_from_repository_root(tmp_path):
    import subprocess, sys
    output = tmp_path / "day.png"
    completed = subprocess.run(
        [sys.executable, "tools/capture_ui.py", "--theme", "day", "--output", str(output)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.exists()
