from pathlib import Path

from PIL import Image

from ratvision.ui.assets import AssetManager


def test_missing_semantic_asset_returns_glyph_fallback(tmp_path):
    manager = AssetManager(root=None, base_dir=tmp_path)
    asset = manager.semantic("game", 24)
    assert asset.image is None
    assert asset.glyph == "🎮"


def test_unknown_semantic_asset_returns_neutral_fallback(tmp_path):
    manager = AssetManager(root=None, base_dir=tmp_path)
    asset = manager.semantic("not-a-real-key", 24)
    assert asset.image is None
    assert asset.glyph == "•"


def test_brand_mark_has_primary_and_small_size_variants():
    base = Path("ratvision/resources/brand")
    primary = Image.open(base / "rat_mark.png")
    small = Image.open(base / "rat_mark_small.png")
    assert primary.size[0] >= 256 and primary.size[1] >= 256
    assert small.size[0] <= 64 and small.size[1] <= 64
    assert primary.mode in {"RGBA", "LA"}
    assert small.mode in {"RGBA", "LA"}


def test_packaged_semantic_assets_include_core_navigation_icons():
    base = Path("ratvision/resources/emoji")
    expected = {
        "game.png",
        "target.png",
        "vision.png",
        "brightness.png",
        "palette.png",
        "display.png",
        "test_tube.png",
        "settings.png",
        "coffee.png",
        "rat.png",
        "arena.png",
        "hunt.png",
    }
    assert expected <= {path.name for path in base.glob("*.png")}


def test_semantic_brand_uses_approved_nvg_application_icon():
    assert AssetManager._SEMANTIC["brand"][0] == "brand/ratvision_icon.png"


def test_rat_vision_icon_master_uses_approved_green_nvg_and_transparent_corners():
    image = Image.open(Path("ratvision/resources/brand/ratvision_icon.png")).convert("RGBA")
    assert image.size[0] >= 512 and image.size[1] >= 512
    # Approved icon: bright green NVG lenses must be visible.
    pixels = image.load()
    green_pixels = sum(
        1
        for y in range(image.height)
        for x in range(image.width)
        for r, g, b, a in (pixels[x, y],)
        if a > 128 and g > 170 and g > r * 1.4 and g > b * 1.4
    )
    assert green_pixels > 100
    # Rounded black square should not leave opaque white corners in Windows Explorer.
    corners = [image.getpixel((0, 0)), image.getpixel((image.width - 1, 0)), image.getpixel((0, image.height - 1)), image.getpixel((image.width - 1, image.height - 1))]
    assert all(pixel[3] < 32 for pixel in corners)


def test_windows_ico_has_fully_transparent_corners_at_every_embedded_size():
    ico = Image.open(Path("ratvision/resources/brand/ratvision.ico"))
    for size in sorted(ico.info["sizes"]):
        frame = ico.ico.getimage(size).convert("RGBA")
        w, h = frame.size
        sample = [
            frame.getpixel((0, 0)),
            frame.getpixel((w - 1, 0)),
            frame.getpixel((0, h - 1)),
            frame.getpixel((w - 1, h - 1)),
        ]
        assert all(pixel[3] == 0 for pixel in sample), (size, sample)


def test_application_icon_transparent_pixels_have_no_white_matte_rgb():
    image = Image.open(Path("ratvision/resources/brand/ratvision_icon.png")).convert("RGBA")
    transparent = [pixel for pixel in image.get_flattened_data() if pixel[3] == 0]
    assert transparent
    assert all(max(pixel[:3]) <= 8 for pixel in transparent)


def test_application_icon_has_no_semiopaque_white_matte_on_rounded_edge():
    image = Image.open(Path("ratvision/resources/brand/ratvision_icon.png")).convert("RGBA")
    matte = [
        pixel for pixel in image.get_flattened_data()
        if 0 < pixel[3] < 255 and min(pixel[:3]) > 180
    ]
    assert not matte
