# 🔄 Update Protocol

GitHub Releases is the only update distribution backend. Each release provides Installer and Portable artifacts, `SHA256SUMS.txt`, and `update-manifest.json`.

The app downloads metadata first, selects the eligible newer release, downloads the matching edition, verifies SHA-256, then asks the user before applying. A failed hash or download leaves the existing installation untouched.
