# 🤖 CODEX — Publish RAT VISION to GitHub

Use this checklist after receiving the prepared repository archive.

## 1. 🔍 Audit
- Confirm the configured repository remains `atikhobaev/rat-vision`.
- Review `LICENSES.md`; do not remove required license notices.
- Confirm no secrets, TelemetryDeck account credentials or personal paths are committed.

## 2. ✅ Test
- Run the full test suite.
- Run `python -m compileall -q ratvision`.
- Confirm the public version is `1.2.0-beta.1` everywhere.

## 3. 🏗️ Build
- Ensure Inno Setup 6 is available.
- Run `release/build-release.ps1 -Version 1.2.0-beta.1`.
- Confirm exactly: Setup EXE, Portable ZIP, `SHA256SUMS.txt`, `update-manifest.json`.

## 4. 🐙 Repository + tag
- Push repository to GitHub.
- Verify Windows CI is green.
- Create/push tag `v1.2.0-beta.1`.

## 5. 🚀 Release
- Let the release workflow create a GitHub prerelease.
- Verify all four release assets upload successfully.
- Download each asset from GitHub and verify SHA256 again.

## 6. 🦠 VirusTotal
- Scan the published Setup EXE.
- Extract Portable ZIP and scan the exact published `RAT VISION.exe`.
- Scan the published Portable ZIP.
- Add the real VirusTotal URLs to release notes/README. Never reuse an old scan URL.

## 7. 🔄 Updater smoke test
- Verify the public `atikhobaev/rat-vision` value before the release build.
- From an older beta build, check for updates.
- Verify discovery, download, SHA256 validation and edition selection.

## 8. 📥 Final download verification
- In a logged-out browser, open the README and release page.
- Download Installer and Portable assets.
- Verify names/version/icons and successful launch.

## 9. 📊 Analytics
- Analytics are ON by default in configured builds. Users can opt out at any time in Settings.
- Set the public TelemetryDeck organization namespace and App ID as GitHub Actions repository variables.
- Verify analytics are ON by default in configured builds, the Settings control is visible, and switching it OFF stops future events immediately.

## 10. 📊 TelemetryDeck setup
- Create a TelemetryDeck Windows app if retention analytics are desired.
- Put only the public organization namespace and App ID into GitHub Actions repository variables.
- Do not commit TelemetryDeck account credentials or Personal Access Tokens.
- Confirm Settings shows the analytics checkbox only in a configured build.
- Confirm it is ON by default, can be turned OFF at any time, and no events are emitted after opt-out.
- Configure DAU/WAU/MAU and D1/D7/D30 retention per `docs/ANALYTICS_DASHBOARD.md`.

## 11. 🏷️ Suggested repository metadata
- Description: `🐀 Automatic per-game gamma & color profiles for Windows. No injection. No game memory access. Just display output.`
- Topics: `windows`, `gamma`, `color-correction`, `gaming`, `display`, `nvidia`, `python`, `tkinter`, `open-source`.
- Confirm README/build configuration consistently uses `atikhobaev/rat-vision` before tagging.
