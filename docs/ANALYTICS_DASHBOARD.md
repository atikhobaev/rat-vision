# 📈 Analytics Dashboard Setup

## 🐙 GitHub-native metrics
- Release asset `download_count` for Setup vs Portable.
- Insights → Traffic: views, unique visitors, clones, unique cloners, referrers (recent GitHub traffic window).

## 📊 TelemetryDeck
Create insights for:
- DAU / WAU / MAU from `RATVISION.dailyActive`;
- D1 / D7 / D30 retention keyed by anonymous install UUID;
- active RAT VISION versions from `RATVISION.appVersion`;
- Installer vs Portable active installations from `RATVISION.edition`;
- approximate country distribution;
- update adoption (`RATVISION.updateInstalled`) when that optional event is enabled later.

The release build uses the public organization namespace and App ID. Never commit TelemetryDeck account credentials or Personal Access Tokens.
