from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import ImageGrab

from ratvision.app import create_simulation_app
from ratvision.domain.models import ThemeMode


def capture_ui(theme: str, output: Path) -> Path:
    mode = ThemeMode(theme)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ratvision-capture-") as tmp:
        settings_path = Path(tmp) / "settings.json"
        root, _controller, _window = create_simulation_app(
            settings_path=settings_path,
            theme_override=mode,
        )
        try:
            root.geometry("1180x760+0+0")
            root.update_idletasks()
            root.update()
            width = root.winfo_width()
            height = root.winfo_height()
            if sys.platform == "win32":
                # Capture the HWND directly so this also works when the desktop
                # surface is unavailable (for example on a Windows CI runner).
                image = ImageGrab.grab(window=root.winfo_id())
            else:
                x = root.winfo_rootx()
                y = root.winfo_rooty()
                image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            image.save(output)
        finally:
            root.destroy()
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture RAT VISION simulation UI")
    parser.add_argument("--theme", choices=("night", "day"), default="night")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    capture_ui(args.theme, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
