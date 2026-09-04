# 🚀 RAT VISION Release Procedure

1. ✅ Verify working tree and run the full test suite.
2. 🔢 Ensure tag, `ratvision/version.py`, `pyproject.toml`, filenames and manifest use the same version.
3. 🪟 Build Installer and 📦 Portable assets with `release/build-release.ps1`.
4. 🔐 Verify `SHA256SUMS.txt` and `update-manifest.json`.
5. 🐙 Push tag `vX.Y.Z`; GitHub Actions publishes the four public assets.
6. 🦠 Download the published assets again and scan Installer EXE, Portable `RAT VISION.exe`, and Portable ZIP with VirusTotal.
7. 📝 Add the real VirusTotal URLs to release notes/README; never fabricate them.
8. 🔄 Test update discovery/download against the published release.
9. 📥 Verify all public download links from a logged-out browser.
