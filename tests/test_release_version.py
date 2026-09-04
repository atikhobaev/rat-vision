from pathlib import Path
import tomllib
from PIL import Image
from ratvision import __version__


def test_public_beta_version_is_consistent():
    data = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
    assert __version__ == '1.2.0-beta.1'
    assert data['project']['version'] == __version__


def test_start_icon_uses_most_of_canvas_without_opaque_corners():
    image = Image.open('ratvision/resources/brand/ratvision_icon.png').convert('RGBA')
    alpha_bbox = image.getchannel('A').getbbox()
    assert alpha_bbox is not None
    l, t, r, b = alpha_bbox
    assert (r-l) / image.width >= 0.94
    assert (b-t) / image.height >= 0.94
    corners = [image.getpixel((0,0)), image.getpixel((image.width-1,0)), image.getpixel((0,image.height-1)), image.getpixel((image.width-1,image.height-1))]
    assert all(a == 0 for *_rgb, a in corners)
