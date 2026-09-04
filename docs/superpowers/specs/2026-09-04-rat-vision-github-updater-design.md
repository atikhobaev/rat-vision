# RAT VISION GitHub Updater Design

**Status:** implemented for `v1.2.0-beta.1`
**Target:** `v1.2.0-beta.1`

## 1. Goal

Replace the current `UPDATE PROTOCOL NOT CONNECTED` placeholder with a real update client that uses GitHub Releases as the only update distribution backend.

## 2. Update source

The application checks the configured public GitHub repository using GitHub Releases metadata. No authentication token is required for ordinary public release checks/downloads.

Repository identity is build configuration, not hard-coded throughout the UI. Define one canonical configuration value such as:

```text
GITHUB_REPOSITORY=OWNER/rat-vision
```

The publication handoff must set the real owner/repository before the first public build.

## 3. Release stream / prerelease behavior

There is no user-selectable channel machinery in the first implementation. The updater follows the release stream implied by the running version:

- a prerelease build such as `1.2.0-beta.1` may discover newer prereleases and stable releases;
- a stable build such as `1.2.0` ignores GitHub prereleases and considers stable releases only.

Because GitHub `releases/latest` excludes prereleases, beta builds must query the release list and select the newest eligible release rather than relying only on `/releases/latest`.

Settings displays `Public beta` for prerelease builds and `Stable` for stable builds. This is informational, not a user-selectable channel.

The app compares semantic versions and ignores releases that are not newer than the current version.

## 4. User experience

Settings → Updates shows:

- current version;
- last check result/time;
- `Check for updates`;
- new release summary if available;
- `Download & Update` and `Later` when a newer release exists.

Updates are never installed silently without a user action.

## 5. Manifest

Each GitHub Release includes `update-manifest.json`:

```json
{
  "version": "1.2.0-beta.1",
  "channel": "beta",
  "installer": {
    "asset": "RAT-VISION-Setup-v1.2.0-beta.1.exe",
    "sha256": "..."
  },
  "portable": {
    "asset": "RAT-VISION-Portable-v1.2.0-beta.1.zip",
    "sha256": "..."
  }
}
```

The updater rejects malformed manifests, mismatched versions, missing assets and hash mismatches.

## 6. Installation mode detection

Installer builds and portable builds must be distinguishable locally:

- portable build contains `portable.flag`;
- installed build does not.

The updater selects the matching asset automatically.

## 7. Installer update path

1. download installer to a temporary directory;
2. verify SHA-256;
3. ask user to confirm update;
4. start installer with `/VERYSILENT /NORESTART` and an argument/instruction that relaunches RAT VISION after upgrade;
5. close current process;
6. installer replaces program files while preserving `%APPDATA%\\RAT VISION`;
7. new version launches.

Any verification failure leaves the old installation untouched.

## 8. Portable update path

1. download portable ZIP to `%TEMP%`;
2. verify SHA-256;
3. extract into a temporary staging directory;
4. start a small update helper outside the application directory;
5. close RAT VISION;
6. helper replaces the portable program directory contents but preserves user settings outside that directory;
7. helper starts the new `RAT VISION.exe`;
8. helper removes temporary staging files when possible.

The helper must fail conservatively and keep a diagnostic log if replacement fails.

## 9. Network / error behavior

The updater must handle:

- offline/no network;
- GitHub rate limit / API error;
- release not found;
- missing manifest;
- download interruption;
- insufficient disk space where detectable;
- SHA-256 mismatch;
- installer/helper launch failure.

No updater failure may terminate the running RAT VISION session or alter existing program files before verification succeeds.

## 10. Security

- HTTPS only.
- Verify SHA-256 from manifest before executing/replacing anything.
- The release workflow generates manifest hashes from the same exact artifacts that are uploaded.
- Surface concise, understandable errors to the user and write detailed diagnostics to the existing logs directory.

## 11. Testing

Tests must cover:

- semantic version comparison;
- GitHub release parsing;
- manifest validation;
- installer vs portable asset selection;
- SHA-256 verification;
- interrupted/error download behavior;
- no-write-before-verification guarantee;
- helper command construction;
- UI states for up-to-date/new-version/error.

Network tests use fixtures/fakes; CI must not depend on the real GitHub API except for an optional post-release smoke check.
