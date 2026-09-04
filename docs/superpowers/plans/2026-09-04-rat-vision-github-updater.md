# RAT VISION GitHub Updater Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace the disconnected update placeholder with a safe GitHub Releases updater for Installer and Portable editions.

**Architecture:** A pure-Python GitHub release client discovers eligible releases and validates the release manifest. Downloads are staged and SHA-256 verified before any mutation. Installed editions launch the verified Inno installer; portable editions launch a detached helper that replaces files after RAT VISION exits.

**Tech Stack:** Python 3.13 stdlib (`urllib`, `hashlib`, `json`, `subprocess`, `tempfile`), GitHub Releases API, Tkinter UI.

**Spec:** `docs/superpowers/specs/2026-09-04-rat-vision-github-updater-design.md`

## Global Constraints

- No silent update installation without explicit user action.
- Public GitHub repository identity is one canonical build configuration value.
- Beta builds can discover newer prereleases and stable releases; stable builds ignore prereleases.
- No program file is modified before SHA-256 verification succeeds.
- Updater failures must not terminate the running app.

---

### Task 1: Release configuration and semantic versions

**Files:**
- Create: `ratvision/release_config.py`
- Create: `ratvision/updates/versioning.py`
- Test: `tests/updates/test_versioning.py`
- Test: `tests/updates/test_release_config.py`

**Interfaces:**
- Produces: `ReleaseConfig`, `ParsedVersion`, `is_newer(candidate, current)`, prerelease eligibility logic.

- [x] Write RED tests for `1.2.0-beta.2 > 1.2.0-beta.1`, stable > beta, stable ignores beta, and unconfigured repository.
- [x] Implement minimal parser/config and re-run tests.

### Task 2: GitHub release discovery and manifest validation

**Files:**
- Create: `ratvision/updates/github_client.py`
- Create: `ratvision/updates/manifest.py`
- Test: `tests/updates/test_github_client.py`
- Test: `tests/updates/test_manifest.py`

**Interfaces:**
- Produces: `ReleaseInfo`, `UpdateManifest`, eligible-release selection from JSON fixtures.

- [x] Write RED tests using fixture dictionaries; no real network.
- [x] Implement parsing, prerelease selection, manifest validation and asset lookup.
- [x] Re-run tests.

### Task 3: Secure download/staging and edition detection

**Files:**
- Create: `ratvision/updates/downloads.py`
- Create: `ratvision/updates/edition.py`
- Test: `tests/updates/test_downloads.py`
- Test: `tests/updates/test_edition.py`

**Interfaces:**
- Produces: `detect_edition(app_dir)`, `download_to_temp(url)`, `verify_sha256(path, expected)`.

- [x] Write RED tests for `portable.flag`, installer fallback, hash match/mismatch and cleanup.
- [x] Implement minimal secure staging and re-run tests.

### Task 4: Installer and portable apply plans

**Files:**
- Create: `ratvision/updates/apply.py`
- Create: `ratvision/updates/portable_helper.py`
- Modify: `ratvision/app.py`
- Test: `tests/updates/test_apply.py`
- Test: `tests/updates/test_portable_helper.py`

**Interfaces:**
- Produces: installer command builder; portable replacement plan; `--portable-update-helper` CLI path that runs before Tk creation.

- [x] Write RED tests for exact commands and no-write-before-verified invariant.
- [x] Implement apply plans/helper with diagnostics and re-run tests.

### Task 5: UpdateService state machine and Settings UI

**Files:**
- Replace: `ratvision/updates/service.py`
- Modify: `ratvision/updates/__init__.py`
- Modify: `ratvision/controller.py`
- Modify: `ratvision/ui/settings_view.py`
- Test: `tests/updates/test_service.py`
- Test: `tests/ui/test_settings_view.py`

**Interfaces:**
- Produces: `check()`, asynchronous-safe UI result states, user-triggered `download_and_update()`.

- [x] Write RED tests for unconfigured/up-to-date/update-available/error states and beta label.
- [x] Implement service and Settings presentation; network work must not block profile switching.
- [x] Re-run targeted and full tests.
