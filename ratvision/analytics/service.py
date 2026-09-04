from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, os, threading, time, uuid
from urllib.request import Request, urlopen
from ratvision.release_config import (
    DEFAULT_TELEMETRYDECK_APP_ID,
    DEFAULT_TELEMETRYDECK_ENDPOINT,
    DEFAULT_TELEMETRYDECK_NAMESPACE,
    load_build_config,
)
from .schema import sanitize_properties

@dataclass(frozen=True, slots=True)
class AnalyticsConfig:
    namespace: str = DEFAULT_TELEMETRYDECK_NAMESPACE
    app_id: str = DEFAULT_TELEMETRYDECK_APP_ID
    endpoint: str = DEFAULT_TELEMETRYDECK_ENDPOINT

    @property
    def configured(self) -> bool:
        return bool(self.namespace.strip() and self.app_id.strip())

    @classmethod
    def from_environment(cls) -> 'AnalyticsConfig':
        built=load_build_config()
        return cls(
            os.environ.get('RATVISION_TELEMETRYDECK_NAMESPACE', built.get('telemetrydeck_namespace', DEFAULT_TELEMETRYDECK_NAMESPACE)).strip(),
            os.environ.get('RATVISION_TELEMETRYDECK_APP_ID', built.get('telemetrydeck_app_id', DEFAULT_TELEMETRYDECK_APP_ID)).strip(),
            os.environ.get('RATVISION_TELEMETRYDECK_ENDPOINT', built.get('telemetrydeck_endpoint', DEFAULT_TELEMETRYDECK_ENDPOINT)).strip() or DEFAULT_TELEMETRYDECK_ENDPOINT,
        )

class AnalyticsService:
    def __init__(self, config: AnalyticsConfig|None=None, *, transport=None, clock=None):
        self.config=config or AnalyticsConfig.from_environment()
        self._transport=transport
        self._clock=clock or time.time
        self._consent_generation=0
        self._session_id=str(uuid.uuid4())

    @property
    def configured(self) -> bool: return self.config.configured

    def set_consent(self, settings, enabled: bool) -> None:
        enabled=bool(enabled)
        if bool(settings.analytics_enabled) != enabled:
            self._consent_generation += 1
        settings.analytics_enabled=enabled
        if enabled and not settings.analytics_install_id:
            settings.analytics_install_id=str(uuid.uuid4())

    def app_started(self, settings, properties: dict[str,object]) -> bool:
        return self._capture(settings,'app_started',properties)

    def daily_active(self, settings, properties: dict[str,object]) -> bool:
        if not self._can_send(settings): return False
        now=float(self._clock())
        last=settings.analytics_last_daily_active
        if last is not None and now-float(last) < 24*3600: return False
        if self._capture(settings,'daily_active',properties):
            settings.analytics_last_daily_active=now
            return True
        return False

    def _can_send(self, settings) -> bool:
        if not self.configured or not bool(settings.analytics_enabled):
            return False
        if not settings.analytics_install_id:
            settings.analytics_install_id = str(uuid.uuid4())
        return True

    def _capture(self, settings, event: str, properties: dict[str,object]) -> bool:
        if not self._can_send(settings): return False
        event_type = {
            'app_started': 'RATVISION.appStarted',
            'daily_active': 'RATVISION.dailyActive',
            'profile_created': 'RATVISION.profileCreated',
            'global_profile_enabled': 'RATVISION.globalProfileEnabled',
            'update_installed': 'RATVISION.updateInstalled',
            'tutorial_completed': 'RATVISION.tutorialCompleted',
        }.get(event, f'RATVISION.{event}')
        safe_properties = sanitize_properties(event, properties)
        # Stable, documented names are easier to query than mechanically
        # flattened snake_case keys.
        telemetry_properties = {
            {
                'app_version': 'RATVISION.appVersion',
                'edition': 'RATVISION.edition',
                'windows_version': 'RATVISION.windowsVersion',
                'gpu_vendor': 'RATVISION.gpuVendor',
                'monitor_count': 'RATVISION.monitorCount',
                'from_version': 'RATVISION.fromVersion',
                'to_version': 'RATVISION.toVersion',
            }.get(key, f'RATVISION.{key}'): value
            for key, value in safe_properties.items()
        }
        payload={
            'appID': self.config.app_id,
            'clientUser': hashlib.sha256(settings.analytics_install_id.encode('utf-8')).hexdigest(),
            'sessionID': self._session_id,
            'type': event_type,
            'payload': telemetry_properties,
        }
        if self._transport is not None:
            self._transport(payload)
        else:
            self._transport_async(payload, settings, self._consent_generation)
        return True

    def _transport_async(self, payload: dict, settings, consent_generation: int) -> None:
        threading.Thread(
            target=self._post,
            args=(payload, settings, consent_generation),
            name='ratvision-analytics',
            daemon=True,
        ).start()

    def _post(self, payload: dict, settings, consent_generation: int) -> None:
        try:
            body=json.dumps([payload],separators=(',',':')).encode('utf-8')
            url=f"{self.config.endpoint.rstrip('/')}/{self.config.namespace}/"
            req=Request(url,data=body,headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'RAT-VISION-Analytics'},method='POST')
            if not bool(settings.analytics_enabled) or self._consent_generation != consent_generation:
                return
            with urlopen(req,timeout=3) as response: response.read(1)
        except Exception:
            pass
