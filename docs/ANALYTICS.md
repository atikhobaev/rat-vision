# 📊 Pseudonymous Usage Analytics

RAT VISION pseudonymous usage analytics are **ON by default** in builds configured with a TelemetryDeck public App ID and organization namespace. You can **opt out at any time** in Settings. RAT VISION does not operate its own analytics server.

If a build has no analytics configuration, no analytics requests are sent and the setting is hidden.

## ✅ Collected while analytics are enabled

- random anonymous installation UUID generated locally on the first analytics send;
- RAT VISION app version;
- Installer vs Portable edition;
- coarse Windows version;
- GPU vendor only (for example NVIDIA/Other);
- monitor count;
- `app_started` and at most one `daily_active` event per rolling 24 hours.

The pseudonymous installation UUID is not derived from hardware, Windows account, IP address or any device serial number. RAT VISION SHA-256 hashes it locally before transmission, and TelemetryDeck hashes the identifier again server-side. Turning analytics off retains the local UUID so that re-enabling does not create a fake new installation in retention statistics.

## ❌ Never collected

- Windows username;
- executable names or exact foreground-app history;
- game titles or profile names;
- file paths;
- monitor/GPU serial numbers or hardware IDs;
- account IDs, clipboard or input data.

The hosted analytics provider may derive approximate country from the network connection. RAT VISION does not send a raw IP property and does not store IP addresses in its own backend because there is no RAT VISION analytics backend.

Turning the Settings checkbox **OFF** stops future analytics events immediately. It does not disable RAT VISION features, profiles, updates or XRAT TRACING.
