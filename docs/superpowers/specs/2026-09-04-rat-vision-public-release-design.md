# RAT VISION Public Release & Distribution Design

**Status:** implemented for `v1.2.0-beta.1`
**Target public version:** `v1.2.0-beta.1`
**Product:** RAT VISION — automatic per-application display color profiles for Windows

## 1. Goal

Turn the current RAT VISION repository into a public-facing GitHub project that can be handed to Codex for publication with minimal manual decisions. The repository must present RAT VISION as a monitor/display-output utility, not as a cheat or game modification, and must publish both an installer and a portable build as GitHub Release assets.

## 2. Product positioning

The first screenful of the README must communicate the product in this order:

1. `🐀 RAT VISION` / `See what the rat sees.`
2. `🎮 Automatic per-game display profiles for Windows.`
3. `🛡️ NOT A CHEAT` explanation.
4. Primary use case: gamma and color correction for dark shooters and other applications.
5. Download actions for installer and portable versions.

Required wording/meaning:

- RAT VISION changes display output settings such as gamma, brightness, contrast, and NVIDIA Digital Vibrance.
- RAT VISION does not inject code, read or write game memory, modify game files, automate input, or interact with anti-cheat systems.
- RAT VISION observes the foreground executable name only to select the configured display profile.
- The principal use case is automatically switching to a brighter/different color profile for a shooter and restoring normal desktop colors after Alt-Tab or exit.
- A concise mental model should be included: `RAT VISION changes what your monitor displays — not what the game renders.`

The README should use many emoji as visual navigation, not decoration-only clutter.

## 3. Public release maturity

The first public release is `v1.2.0-beta.1`, not Stable.

Rationale:

- UI and automated tests are mature.
- Windows/NVIDIA hardware behavior has been exercised during development, but broader real-world hardware coverage is still limited.
- Beta labeling invites useful hardware reports without overstating maturity.

The README and release notes must clearly say `Public beta — Windows/NVIDIA hardware feedback welcome.`

## 4. Release artifacts

Every release must produce exactly these user-facing assets:

- `RAT-VISION-Setup-vX.Y.Z.exe`
- `RAT-VISION-Portable-vX.Y.Z.zip`
- `SHA256SUMS.txt`
- `update-manifest.json`

Optional internal CI artifacts may exist, but they must not replace the four release assets above.

### 4.1 Portable edition

The portable artifact contains a PyInstaller directory build, not a one-file self-extractor.

Expected layout:

```text
RAT VISION/
├── RAT VISION.exe
├── _internal/...
└── portable.flag
```

The app settings remain under `%APPDATA%\\RAT VISION`, so portable updates do not overwrite profiles/settings.

### 4.2 Installer edition

Use Inno Setup to create a per-user installer. Default install location:

```text
%LOCALAPPDATA%\\Programs\\RAT VISION
```

The installer must not require administrator privileges for the normal path.

Installer responsibilities:

- install RAT VISION files;
- create a Start Menu shortcut;
- optionally create a Desktop shortcut;
- register uninstall metadata;
- preserve `%APPDATA%\\RAT VISION` across upgrades/uninstall unless the user explicitly chooses to remove settings;
- support silent upgrade via `/VERYSILENT /NORESTART` for the updater.

## 5. Build and release workflow

### 5.1 CI workflow

`.github/workflows/ci.yml` runs on Windows for pushes and pull requests:

1. checkout;
2. install Python/build dependencies;
3. run full tests;
4. build the Windows application;
5. validate expected EXE/resources;
6. expose a CI artifact for inspection.

### 5.2 Release workflow

`.github/workflows/release.yml` triggers on tags matching `v*` and performs:

1. full test suite;
2. portable build;
3. Inno Setup installer build;
4. generate `SHA256SUMS.txt`;
5. generate `update-manifest.json`;
6. validate version consistency between tag, Python package, executable metadata, manifest and filenames;
7. create GitHub Release, marking versions containing a prerelease suffix such as `-beta.1` as GitHub prereleases;
8. upload the four public assets.

The release workflow must fail closed: a hash/manifest/version mismatch prevents release publication.

## 6. GitHub README structure

Required major sections:

- `# 🐀 RAT VISION`
- `🛡️ NOT A CHEAT`
- `🎯 What it is for`
- `✨ Features`
- `📸 Screenshots`
- `🚀 Download`
- `📦 Installer vs Portable`
- `🎮 Per-game profiles`
- `🌐 Global Profile`
- `🖥️ Multi-monitor`
- `🔄 Updates`
- `🧪 How it works`
- `🛡️ Security & VirusTotal`
- `⚙️ Installation`
- `🧑‍💻 Build from source`
- `📊 Anonymous analytics`
- `🗺️ Roadmap`
- `📜 Licenses`
- `☕ Support`

The README must include screenshots from `docs/images/` and highly visible Download links. During the public-beta phase, links must point to the current beta tag/release page because GitHub `releases/latest` does not select prereleases. After the first stable release exists, stable download links may use `releases/latest` and `releases/latest/download/<asset>`.

## 7. Security / VirusTotal process

For every public release, manually scan at least:

- installer EXE;
- main `RAT VISION.exe` from the portable build;
- portable ZIP.

The repository prepares placeholders and a checklist, but does not fake VirusTotal results. Real URLs are inserted only after the user/Codex uploads and scans the actual final artifacts.

Release notes must include SHA-256 for each public artifact and VirusTotal URLs when available.

## 8. Licensing / acknowledgements

User-facing application UI must not mention the prior repository.

Legal notices required by the licenses of reused/third-party code remain in `LICENSES.md` and any required license files. Public release preparation must not remove legally required attribution or license text.

## 9. Repository support documents

Create/update:

- `CHANGELOG.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `docs/RELEASE.md`
- `docs/UPDATE_PROTOCOL.md`
- `docs/ANALYTICS.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `CODEX_GITHUB_RELEASE.md`

`CODEX_GITHUB_RELEASE.md` is an explicit handoff checklist for Codex: audit, test, build, tag, release, upload assets, VirusTotal scan, paste URLs, verify download links, and verify updater behavior against the published release.

## 10. Public beta release notes

The first release notes should emphasize:

- public beta status;
- display-output-only behavior / no game modification;
- installer and portable choices;
- per-game and Global profiles;
- multi-monitor support;
- NVIDIA DVC isolation and gamma control;
- update system status;
- how to report hardware-specific issues.

## 11. Out of scope for the first public release

Do not add:

- Microsoft Store distribution;
- winget/chocolatey packages;
- hidden telemetry or analytics fields beyond the documented anonymous analytics contract;
- accounts/cloud sync;
- beta/nightly update channels;
- a custom update server;
- silent background updates without confirmation.
