# RAT VISION Analytics Without Own Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add transparent, opt-out pseudonymous product analytics using TelemetryDeck with telemetry ON by default in configured builds and preserving GitHub-native download statistics.

**Architecture:** One narrow analytics service owns the event schema and network transport. The analytics enabled flag and anonymous install identity live in settings; configured builds start enabled, while disabling the setting blocks all future events. Events are best-effort, low-frequency and sent off the UI thread.

**Tech Stack:** Python 3.13 stdlib HTTP/JSON/threading, TelemetryDeck Ingest API v2, GitHub release download_count/Traffic documentation.

**Spec:** `docs/superpowers/specs/2026-09-04-rat-vision-analytics-design.md`

## Global Constraints

- Telemetry is ON by default when TelemetryDeck build configuration is present.
- User opt-out stops all future events immediately.
- Never send executable names, profile/game names, file paths, usernames, serial numbers or exact foreground history.
- `daily_active` is emitted at most once per rolling 24 hours.
- Missing analytics configuration makes telemetry unavailable without affecting application behavior.

---

### Task 1: Consent/settings schema

**Files:**
- Modify: `ratvision/domain/models.py`
- Modify: `ratvision/persistence/settings_store.py`
- Modify: `ratvision/persistence/migration.py`
- Test: `tests/test_settings_store.py`
- Test: `tests/test_migration.py`

**Interfaces:**
- Produces: `analytics_enabled`, `analytics_install_id`, `analytics_last_daily_active` persisted fields.

- [x] Write RED tests for default ON, UUID persistence, opt-out behavior and backward-compatible migration.
- [x] Implement fields/store support and re-run tests.

### Task 2: Narrow analytics service

**Files:**
- Create: `ratvision/analytics/__init__.py`
- Create: `ratvision/analytics/service.py`
- Create: `ratvision/analytics/schema.py`
- Test: `tests/analytics/test_service.py`
- Test: `tests/analytics/test_schema.py`

**Interfaces:**
- Produces: `AnalyticsService.set_consent()`, `app_started()`, `daily_active()`, allow-listed properties only.

- [x] Write RED tests proving forbidden keys are rejected/never emitted and 24h throttling works.
- [x] Implement non-blocking stdlib transport with short timeout and re-run tests.

### Task 3: Controller integration and Settings transparency

**Files:**
- Modify: `ratvision/controller.py`
- Modify: `ratvision/ui/settings_view.py`
- Create: `docs/ANALYTICS.md`
- Test: `tests/analytics/test_controller_integration.py`
- Test: `tests/ui/test_settings_view.py`
- Test: `tests/release/test_public_docs.py`

**Interfaces:**
- Produces: visible `📊 Share anonymous usage statistics` checkbox only when configured, `What is collected?` explanation, app-start/daily-active integration.

- [x] Write RED tests for hidden-when-unconfigured and ON-by-default behavior.
- [x] Implement controller/UI/docs integration and re-run tests.

### Task 4: TelemetryDeck/GitHub dashboard handoff

**Files:**
- Create: `docs/ANALYTICS_DASHBOARD.md`
- Modify: `CODEX_GITHUB_RELEASE.md`
- Test: `tests/release/test_codex_handoff.py`

**Interfaces:**
- Produces: setup instructions for the TelemetryDeck namespace/App ID, DAU/WAU/MAU, D1/D7/D30 retention, versions/edition/country dashboards, and GitHub download/traffic checks.

- [x] Write RED documentation checks.
- [x] Write dashboard/handoff instructions with no secrets committed.
- [x] Re-run full suite.
