# RAT VISION visual resources

RAT VISION uses original product branding plus embedded semantic emoji-style PNGs so the interface does not depend on the host Windows emoji font.

## Brand artwork

`brand/rat_mark.png` and `brand/rat_mark_small.png` are original RAT VISION assets derived from the approved stencil-rat concept for this project. They are not game assets and do not reproduce the TerraGroup or Battlestate Games logos.

`brand/ratvision_icon.png` is the 1024×1024 master application icon and `brand/ratvision.ico` is the Windows multi-size ICO embedded into `RAT VISION.exe` during packaging.

## Semantic emoji-style assets

The PNGs in `emoji/` are project-local rendered derivatives of glyphs from **Noto Color Emoji**, with a small project-added shadow treatment for consistent UI presentation. Noto Color Emoji is distributed under the SIL Open Font License 1.1. The font file itself is not bundled with RAT VISION.

The project intentionally does **not** bundle Apple emoji artwork. The target is a polished, dimensional emoji-like visual language while keeping distributable assets legally independent from Apple artwork.

Every essential action also has a textual label and a deterministic Unicode fallback in `ratvision.ui.assets.AssetManager`.

`brand/ratvision_icon.png` is the single approved NVG-rat master used by the EXE, window icon, header and tray renderer. `brand/ratvision.ico` contains 16/24/32/48/64/128/256 px Windows frames with transparent corners.
