# RAT VISION Analytics Without Own Server Design

**Status:** implemented for `v1.2.0-beta.1`
**Target:** public beta architecture; telemetry feature may ship in `v1.2.0-beta.1` only if configured and tested

## 1. Goal

Collect enough product data to answer:

- how many people download Installer vs Portable;
- where repository visitors come from;
- approximately which countries active users are in;
- how many installations continue to use RAT VISION over time;
- which versions remain active;

without operating a custom RAT VISION analytics server.

## 2. Two data layers

### 2.1 GitHub-native metrics

GitHub remains authoritative for distribution metrics:

- release asset `download_count` separately for Installer and Portable;
- repository views/unique visitors;
- clones/unique cloners;
- top referrers;
- popular repository content.

GitHub traffic is limited to the recent traffic window and does not provide active-application retention, so it is not sufficient alone.

### 2.2 Opt-out application analytics

Use TelemetryDeck for product analytics. Do not run a RAT VISION-owned VPS/backend.

TelemetryDeck application configuration is public build configuration:

```text
TELEMETRYDECK_NAMESPACE=<public organization namespace>
TELEMETRYDECK_APP_ID=<public app ID>
```

If configuration is absent, telemetry is unavailable and the app continues normally.

## 3. Consent model

Telemetry is **ON by default** when analytics build configuration is present.

Settings includes:

`📊 Share anonymous usage statistics`

Tooltip/details explain exactly what is collected and what is never collected.

The user may opt out at any time. Once disabled, no future analytics event may be emitted until the setting is re-enabled.

Turning the option OFF stops future events immediately.

## 4. Anonymous installation identity

On the first analytics send, generate a random UUID `install_id` and store it in RAT VISION settings. It is not derived from hardware, Windows account, IP address or any device serial number.

The UUID is SHA-256 hashed locally before transmission and is used only to measure pseudonymous active installations and retention. TelemetryDeck hashes the identifier again server-side.

Resetting/removing application settings naturally creates a new anonymous installation identity. Turning analytics OFF does not delete the UUID, so re-enabling preserves retention continuity.

## 5. Allowed events/properties

Minimum useful event set:

### `app_started`

Properties:

- app version;
- edition: `installer` or `portable`;
- Windows major version/build bucket;
- GPU vendor only (`NVIDIA`, `AMD`, `Intel`, `Other`);
- monitor count;

### `daily_active`

Sent at most once per rolling 24 hours per installation.

Properties:

- app version;
- edition;
- Windows version bucket.

This event is the basis for DAU/WAU/MAU and retention.

### Optional coarse feature events

Only if later proven useful:

- `profile_created` with no profile/game name;
- `global_profile_enabled`;
- `update_installed` with from/to version;
- `tutorial_completed`.

Do not track every click or high-frequency UI interaction.

## 6. Forbidden data

Never send:

- Windows username;
- email/name;
- IP address as an application property;
- file paths;
- executable names;
- configured process names;
- profile names;
- game titles;
- Steam/Epic/account IDs;
- monitor serial numbers;
- GPU serial/hardware IDs;
- machine GUID;
- clipboard/input data;
- exact foreground application history.

Approximate country may be derived by the hosted analytics service from the connection. RAT VISION does not persist or transmit a raw IP property itself.

## 7. Transparency

Create `docs/ANALYTICS.md` and a concise README privacy section that list every event/property.

The Settings UI links or exposes `What is collected?` details.

The implementation must make telemetry code easy to audit: one small analytics service with a narrow event schema, not analytics calls scattered across UI files.

## 8. Reliability / performance

Analytics is best-effort and non-blocking.

- It must never delay startup or profile switching.
- Network failures are silently ignored after optional debug logging.
- Events should be sent asynchronously with short timeouts.
- `daily_active` is rate-limited locally to at most once per 24 hours.
- No retry loop may wake the app repeatedly or spam the service.

## 9. Metrics to create in TelemetryDeck

Prepare dashboard instructions for:

- DAU / WAU / MAU;
- D1 / D7 / D30 retention;
- active versions;
- Installer vs Portable active installations;
- country distribution;
- update adoption over time.

GitHub dashboard/checklist separately records:

- Setup downloads;
- Portable downloads;
- repository traffic/referrers.

## 10. Privacy and beta rollout

Preferred beta behavior:

- analytics code is present and tested;
- telemetry is ON by default when configured and has a clear Settings opt-out;
- the setting is shown only when TelemetryDeck configuration is present in the build;
- public beta README clearly states that anonymous usage analytics are enabled by default in configured builds and can be turned off at any time.

This gives early retention data while keeping collection narrowly scoped, transparent and immediately disableable.
