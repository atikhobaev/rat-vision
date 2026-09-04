from __future__ import annotations

import platform
from typing import Any


class DiagnosticsCollector:
    def __init__(self, controller):
        self.controller = controller

    def collect(self) -> dict[str, Any]:
        foreground = getattr(self.controller, "current_foreground", None)
        displays = []
        for display in getattr(self.controller, "displays", []):
            capabilities = {}
            backend = getattr(self.controller, "color_backend", None)
            if backend is not None:
                try:
                    capabilities = dict(backend.capabilities(display.id))
                except Exception:
                    capabilities = {"error": "capability query failed"}
            displays.append(
                {
                    "id": display.id,
                    "name": display.name,
                    "resolution": f"{display.width}x{display.height}",
                    "refresh_hz": display.refresh_hz,
                    "primary": display.primary,
                    "online": display.online,
                    "capabilities": capabilities,
                }
            )
        return {
            "version": str(getattr(self.controller, "version", "unknown")),
            "platform": str(getattr(self.controller, "platform_name", platform.system())),
            "python": platform.python_version(),
            "xrat_enabled": bool(getattr(getattr(self.controller, "settings", None), "global_enabled", False)),
            "foreground_process": getattr(foreground, "executable", "") if foreground else "",
            "foreground_pid": getattr(foreground, "pid", 0) if foreground else 0,
            "display_count": len(displays),
            "displays": displays,
        }

    def format_text(self) -> str:
        data = self.collect()
        lines = [
            f"RAT VISION v{data['version']}",
            f"Platform: {data['platform']}",
            f"Python: {data['python']}",
            f"XRAT: {'ENABLED' if data['xrat_enabled'] else 'DISABLED'}",
            f"Foreground: {data['foreground_process'] or '(none)'} (PID {data['foreground_pid']})",
            f"Displays: {data['display_count']}",
        ]
        for display in data["displays"]:
            lines.append(
                f"- {display['id']} | {display['name']} | {display['resolution']} | "
                f"{'PRIMARY' if display['primary'] else 'SECONDARY'} | "
                f"{'ONLINE' if display['online'] else 'OFFLINE'} | {display['capabilities']}"
            )
        return "\n".join(lines)
