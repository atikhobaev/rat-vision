# RAT VISION First Public Beta Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate, package, publish, and live-verify RAT VISION `v1.2.0-beta.1` as a GitHub public pre-release.

**Architecture:** Preserve the prepared application architecture and treat the archive handoff plus repository documentation as the release specification. Work in ordered audit gates: source and legal review, automated tests, Windows packaging, artifact integrity, repository publication, and post-publication updater validation.

**Tech Stack:** Python 3.13, pytest, PyInstaller, Inno Setup, PowerShell, GitHub Actions, GitHub Releases.

**Spec:** `CODEX_GITHUB_RELEASE.md` and the supplied first-public-release request.

## Global Constraints

- Release version is exactly `v1.2.0-beta.1` and must be a public GitHub pre-release.
- RAT VISION is presented as a Windows color profile manager, never as a cheat.
- Preserve LGPL and all required third-party attribution.
- Anonymous analytics are enabled by default and are user-disableable (opt-out).
- Do not commit credentials, local identifiers, caches, logs, or build environments.
- Release hashes and VirusTotal URLs must never be invented.
- Do not claim completion before live verification passes with zero test failures.

---

### Task 1: Import and audit the prepared source

**Files:**
- Import: all archive members except the outer `CODEX-PUBLISH` ZIP
- Review: `CODEX_GITHUB_RELEASE.md`, required root documents, `docs/`, `.github/workflows/`, `installer/`, `release/`, and `scripts/`

**Interfaces:**
- Consumes: prepared release archive
- Produces: clean Git working tree containing auditable release sources

- [ ] Validate archive member paths against absolute paths and parent traversal.
- [ ] Extract into an isolated staging directory.
- [ ] Read every required handoff, specification, plan, workflow, installer, release, and script file.
- [ ] Copy reviewed source into the repository root without replacing `.git`.
- [ ] Run secret, user-path, cache, and unwanted-artifact scans.

### Task 2: Verify application behavior and release metadata

**Files:**
- Verify/modify as evidence requires: application modules, tests, documentation, workflows, installer scripts, and release scripts

**Interfaces:**
- Consumes: imported source and documented release contract
- Produces: version-consistent, tested source with truthful public documentation

- [ ] Create a clean Python environment and install the package/build dependencies.
- [ ] Run the complete pytest suite and require zero failures.
- [ ] Run `compileall`, YAML parsing, version consistency, analytics, export-profile, updater, and ZIP traversal checks.
- [ ] Audit README links, badges, product positioning, licenses, analytics disclosure, icons, CI, and release workflow.
- [ ] For any confirmed defect, add or identify a failing test, make the smallest fix, and rerun the relevant test before the full suite.

### Task 3: Build and validate Windows release assets

**Files:**
- Produce: `RAT-VISION-Setup-v1.2.0-beta.1.exe`
- Produce: `RAT-VISION-Portable-v1.2.0-beta.1.zip`
- Produce: `SHA256SUMS.txt`
- Produce: `update-manifest.json`

**Interfaces:**
- Consumes: verified source, PyInstaller configuration, Inno Setup script
- Produces: four release assets with mutually consistent filenames and hashes

- [ ] Build the real Windows executable and inspect PyInstaller output.
- [ ] Assemble the portable distribution with `portable.flag` and no forbidden files.
- [ ] Build the Inno Setup installer and verify install-path/update flags statically and, where safe, operationally.
- [ ] Calculate real SHA-256 hashes and generate the manifest only from built assets.
- [ ] Extract the portable ZIP and verify contents, executable, runtime/resources, updater support, and forbidden-file absence.

### Task 4: Publish repository and pre-release

**Files:**
- Commit: reviewed source and release-support files
- Tag: `v1.2.0-beta.1`
- Upload: four generated release assets

**Interfaces:**
- Consumes: clean audited tree and validated assets
- Produces: GitHub repository commit, tag, Actions result, and public pre-release

- [ ] Review Git diff and untracked files, excluding the source handoff ZIP and local build environments.
- [ ] Commit and push `main` to `https://github.com/atikhobaev/rat-vision.git`.
- [ ] Verify CI passes for the published commit.
- [ ] Create and push tag `v1.2.0-beta.1`.
- [ ] Create a GitHub pre-release with truthful emoji release notes and upload the validated assets.

### Task 5: Live release verification and handoff

**Files:**
- Verify remotely: release page and downloadable assets
- Report: repository/release URLs, SHAs, CI, analytics configuration, and manual VirusTotal work

**Interfaces:**
- Consumes: published pre-release metadata and assets
- Produces: evidence-backed completion report

- [ ] Download each published asset and compare hashes with `SHA256SUMS.txt` and `update-manifest.json`.
- [ ] Test updater resolution against the published GitHub release metadata.
- [ ] Confirm the release is public and marked pre-release, not stable.
- [ ] Confirm `TELEMETRYDECK_NAMESPACE` and `TELEMETRYDECK_APP_ID` repository-variable status.
- [ ] List the exact files for manual VirusTotal scanning and the documentation locations for resulting URLs.
- [ ] Apply `verification-before-completion` and report only claims supported by fresh command output.
