# RAT VISION Public Release Architecture Overview

RAT VISION public release work is intentionally split into three independently implementable subprojects:

1. **Public Release & Distribution** — repository presentation, Windows CI, Portable ZIP, Inno Setup installer, release assets, hashes, VirusTotal process and Codex publication handoff.
   - Spec: `docs/superpowers/specs/2026-09-04-rat-vision-public-release-design.md`

2. **GitHub Updater** — replace the placeholder update service with release discovery, hash verification and separate installer/portable update paths.
   - Spec: `docs/superpowers/specs/2026-09-04-rat-vision-github-updater-design.md`

3. **Analytics Without Own Server** — GitHub-native download/traffic metrics plus TelemetryDeck pseudonymous retention analytics, ON by default in configured builds with user opt-out.
   - Spec: `docs/superpowers/specs/2026-09-04-rat-vision-analytics-design.md`

## Implementation order

1. Public Release & Distribution
2. GitHub Updater
3. Analytics

Why this order:

- updater needs a stable release artifact/manifest contract;
- analytics should not block publication and can be configured after the public repository exists;
- the first deliverable is a repository/archive that Codex can publish and a reproducible release pipeline.

## Public release target

`v1.2.0-beta.1`

The beta label is intentional until broader Windows/NVIDIA hardware feedback is collected.
