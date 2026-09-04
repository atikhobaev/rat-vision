# RAT VISION Public Release & Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Prepare RAT VISION `v1.2.0-beta.1` for a polished public GitHub release with Windows CI, Portable ZIP, Inno Setup installer, hashes, manifest, documentation, and a Codex publication handoff.

**Architecture:** Keep the existing PyInstaller directory build as the canonical application payload. A PowerShell release builder stages a Portable ZIP and invokes Inno Setup for a per-user installer; GitHub Actions reuses that contract on Windows and publishes four release assets from tags. Public documentation positions RAT VISION as a display-output utility and clearly distinguishes it from cheats/game modification.

**Tech Stack:** Python 3.13, PyInstaller, PowerShell, Inno Setup 6, GitHub Actions, SHA-256.

**Spec:** `docs/superpowers/specs/2026-09-04-rat-vision-public-release-design.md`

## Global Constraints

- Public beta version is exactly `1.2.0-beta.1` / tag `v1.2.0-beta.1`.
- User-facing release assets are Setup EXE, Portable ZIP, `SHA256SUMS.txt`, and `update-manifest.json`.
- Normal installer path is per-user and must not require administrator privileges.
- User-facing UI must not mention the prior repository; required legal notices stay in `LICENSES.md`.
- Do not fabricate VirusTotal URLs or scan results.
- README must explicitly state that RAT VISION changes display output and does not inject/read/write game memory or modify game files.

---

### Task 1: Release metadata and larger public icons

**Files:**
- Modify: `pyproject.toml`
- Modify: `ratvision/version.py`
- Modify: `ratvision/ui/assets.py`
- Modify: `ratvision/ui/tray_assets.py`
- Create: `tools/build_release_icons.py`
- Test: `tests/test_release_version.py`
- Test: `tests/ui/test_assets.py`
- Test: `tests/ui/test_tray_assets.py`

**Interfaces:**
- Produces: `__version__ == "1.2.0-beta.1"`; regenerated `ratvision_icon.png`, `ratvision.ico`; larger Start/EXE/taskbar and tray artwork.

- [x] **Step 1: Write failing tests** asserting beta version consistency and minimum foreground occupancy for EXE and 16 px tray art.
- [x] **Step 2: Run tests to verify RED** with `xvfb-run -a python -m pytest -q tests/test_release_version.py tests/ui/test_assets.py tests/ui/test_tray_assets.py`.
- [x] **Step 3: Implement icon builder** that crops the approved NVG master tightly, preserves transparent rounded corners, emits the 7 ICO sizes, and creates tray-specific close crops.
- [x] **Step 4: Set version** in `pyproject.toml` and `ratvision/version.py` to `1.2.0-beta.1`.
- [x] **Step 5: Re-run targeted tests** and confirm PASS.

### Task 2: Deterministic release artifact builder

**Files:**
- Create: `release/build-release.ps1`
- Create: `release/generate_manifest.py`
- Create: `release/validate_release.py`
- Modify: `scripts/build-windows.ps1`
- Test: `tests/release/test_manifest.py`
- Test: `tests/release/test_release_validation.py`

**Interfaces:**
- Produces: `release/out/RAT-VISION-Portable-v<version>.zip`, `SHA256SUMS.txt`, `update-manifest.json` and a staged installer input directory.

- [x] **Step 1: Write failing manifest tests** for exact filenames, SHA-256 values and beta channel.
- [x] **Step 2: Verify RED** with `python -m pytest -q tests/release/test_manifest.py tests/release/test_release_validation.py`.
- [x] **Step 3: Implement `generate_manifest.py`** with `sha256_file(path)`, `build_manifest(version, installer_path, portable_path)` and deterministic JSON output.
- [x] **Step 4: Implement `validate_release.py`** to reject version/tag/filename/manifest mismatches.
- [x] **Step 5: Implement `build-release.ps1`** to run the existing Windows build, add `portable.flag`, zip the complete `dist\RAT VISION` directory, and call the manifest/hash generator.
- [x] **Step 6: Re-run targeted tests** and confirm PASS.

### Task 3: Per-user Inno Setup installer

**Files:**
- Create: `installer/rat-vision.iss`
- Modify: `release/build-release.ps1`
- Test: `tests/release/test_installer_script.py`

**Interfaces:**
- Produces: `RAT-VISION-Setup-v1.2.0-beta.1.exe`; silent upgrade compatible with `/VERYSILENT /NORESTART`.

- [x] **Step 1: Write failing structural tests** asserting `PrivilegesRequired=lowest`, `{localappdata}\Programs\RAT VISION`, Start Menu shortcut, optional desktop task, uninstall metadata, and no deletion of `%APPDATA%\RAT VISION`.
- [x] **Step 2: Verify RED**.
- [x] **Step 3: Write `rat-vision.iss`** with AppVersion passed through `/DMyAppVersion=<version>` and staged files from `dist\RAT VISION`.
- [x] **Step 4: Update release builder** to locate `ISCC.exe` and fail with a clear message if Inno Setup is absent.
- [x] **Step 5: Re-run installer tests**.

### Task 4: GitHub CI and tag-release workflows

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/release.yml`
- Test: `tests/release/test_github_workflows.py`

**Interfaces:**
- Produces: Windows CI artifact for every push/PR and four public GitHub Release assets for `v*` tags.

- [x] **Step 1: Write failing workflow tests** for `windows-latest`, Python 3.13, test execution, release build, prerelease flag, and upload of all four assets.
- [x] **Step 2: Verify RED**.
- [x] **Step 3: Implement `ci.yml`** using `actions/checkout@v4`, `actions/setup-python@v5`, dependency installation, tests, `scripts/build-windows.ps1`, and artifact upload.
- [x] **Step 4: Implement `release.yml`** with tag/version validation, Inno Setup install, release build, `softprops/action-gh-release` prerelease publication, and exact asset paths.
- [x] **Step 5: Re-run workflow tests**.

### Task 5: Public GitHub documentation and support templates

**Files:**
- Replace: `README.md`
- Create: `CHANGELOG.md`
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Create: `docs/RELEASE.md`
- Create: `docs/UPDATE_PROTOCOL.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create/update images under: `docs/images/`
- Test: `tests/release/test_public_docs.py`

**Interfaces:**
- Produces: public-facing repository documentation with emoji-heavy navigation and explicit NOT-A-CHEAT explanation.

- [x] **Step 1: Write failing documentation tests** for required sections and prohibited misleading wording.
- [x] **Step 2: Verify RED**.
- [x] **Step 3: Build `docs/images/`** from the approved screenshots and icon assets already present in the project/session.
- [x] **Step 4: Rewrite README** with the required sections, download placeholders, beta warning, screenshots, display-output explanation and installer/portable guidance.
- [x] **Step 5: Add changelog/security/contributing/release/update docs and issue/PR templates**.
- [x] **Step 6: Re-run documentation tests**.

### Task 6: VirusTotal and Codex publication handoff

**Files:**
- Create: `CODEX_GITHUB_RELEASE.md`
- Modify: `docs/RELEASE.md`
- Test: `tests/release/test_codex_handoff.py`

**Interfaces:**
- Produces: exact manual/Codex checklist for publishing the repository, creating tag `v1.2.0-beta.1`, uploading assets, scanning final files, inserting real VT URLs, and testing downloads/updater.

- [x] **Step 1: Write failing handoff test** for audit/test/build/tag/release/upload/VT/verify steps.
- [x] **Step 2: Verify RED**.
- [x] **Step 3: Write the handoff** with placeholders only for GitHub owner/repository and real VirusTotal URLs.
- [x] **Step 4: Re-run handoff tests and full suite**.
