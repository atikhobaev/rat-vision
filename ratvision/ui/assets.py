from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - Pillow is a declared runtime dependency
    Image = None
    ImageTk = None


@dataclass(frozen=True, slots=True)
class SemanticAsset:
    image: object | None
    glyph: str


class AssetManager:
    _SEMANTIC: dict[str, tuple[str | None, str]] = {
        "brand": ("brand/ratvision_icon.png", "🐀"),
        "game": ("emoji/game.png", "🎮"),
        "global": (None, "🌐"),
        "target": ("emoji/target.png", "🎯"),
        "vision": ("emoji/vision.png", "👁️"),
        "brightness": ("emoji/brightness.png", "☀️"),
        "contrast": (None, "◐"),
        "gamma": (None, "🌗"),
        "saturation": ("emoji/palette.png", "🎨"),
        "display": ("emoji/display.png", "🖥️"),
        "lab": ("emoji/test_tube.png", "🧪"),
        "settings": ("emoji/settings.png", "⚙️"),
        "add": (None, "➕"),
        "delete": (None, "🗑️"),
        "reset": (None, "🔄"),
        "diagnostics": (None, "📋"),
        "warning": (None, "⚠️"),
        "success": (None, "✅"),
        "coffee": ("emoji/coffee.png", "☕"),
        "rat": ("emoji/rat.png", "🐀"),
        "arena": ("emoji/arena.png", "⚔️"),
        "hunt": ("emoji/hunt.png", "🤠"),
    }

    def __init__(self, root: tk.Misc | None, base_dir: Path | None = None) -> None:
        self.root = root
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent / "resources"
        self._cache: dict[tuple[str, int, str | None], object] = {}

    def load_image(self, name: str, size: int, *, tint: str | None = None):
        path = self.base_dir / name
        if Image is None or not path.exists():
            return None
        image = Image.open(path).convert("RGBA")
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        if tint is not None:
            alpha = image.getchannel("A")
            tinted = Image.new("RGBA", image.size, tint)
            tinted.putalpha(alpha)
            image = tinted
        return image

    def get(self, name: str, size: int, *, tint: str | None = None):
        key = (name, int(size), tint)
        if key in self._cache:
            return self._cache[key]
        if self.root is None or ImageTk is None:
            return None
        image = self.load_image(name, size, tint=tint)
        if image is None:
            return None
        photo = ImageTk.PhotoImage(image, master=self.root)
        self._cache[key] = photo
        return photo

    def semantic(self, key: str, size: int = 20, *, tint: str | None = None) -> SemanticAsset:
        name, glyph = self._SEMANTIC.get(key, (None, "•"))
        image = self.get(name, size, tint=tint) if name else None
        return SemanticAsset(image=image, glyph=glyph)
