import threading
import hashlib
import json

from ratvision.domain.models import AppSettings
from ratvision.analytics.service import AnalyticsConfig, AnalyticsService


def test_telemetry_is_on_by_default_and_generates_random_id_on_first_send():
    sent=[]
    settings=AppSettings()
    svc=AnalyticsService(AnalyticsConfig('namespace', 'app-id'), transport=sent.append, clock=lambda: 1000)
    assert settings.analytics_enabled is True
    assert settings.analytics_install_id is None
    assert svc.app_started(settings, {'app_version':'1'}) is True
    assert settings.analytics_install_id
    assert sent[0]['type'] == 'RATVISION.appStarted'
    assert sent[0]['appID'] == 'app-id'
    assert sent[0]['clientUser'] == hashlib.sha256(settings.analytics_install_id.encode()).hexdigest()
    assert sent[0]['payload']['RATVISION.appVersion'] == '1'


def test_user_can_opt_out_and_existing_install_id_is_retained():
    sent=[]
    settings=AppSettings(analytics_enabled=True, analytics_install_id='stable-id')
    svc=AnalyticsService(AnalyticsConfig('namespace', 'app-id'), transport=sent.append, clock=lambda: 1000)
    svc.set_consent(settings, False)
    assert settings.analytics_enabled is False
    assert settings.analytics_install_id == 'stable-id'
    assert svc.app_started(settings, {'app_version':'1'}) is False
    assert svc.daily_active(settings, {'app_version':'1'}) is False
    assert sent == []


def test_reenabling_reuses_existing_install_id():
    sent=[]
    settings=AppSettings(analytics_enabled=False, analytics_install_id='stable-id')
    svc=AnalyticsService(AnalyticsConfig('namespace', 'app-id'), transport=sent.append, clock=lambda: 1000)
    svc.set_consent(settings, True)
    assert settings.analytics_install_id == 'stable-id'
    assert svc.app_started(settings, {'app_version':'1'}) is True
    assert sent[0]['clientUser'] == hashlib.sha256(b'stable-id').hexdigest()


def test_daily_active_is_limited_to_once_per_24_hours():
    sent=[]; now=[100000.0]; settings=AppSettings(analytics_enabled=True, analytics_install_id='id')
    svc=AnalyticsService(AnalyticsConfig('namespace', 'app-id'), transport=sent.append, clock=lambda: now[0])
    assert svc.daily_active(settings, {'app_version':'1'}) is True
    assert svc.daily_active(settings, {'app_version':'1'}) is False
    now[0]+=24*3600+1
    assert svc.daily_active(settings, {'app_version':'1'}) is True
    assert [p['type'] for p in sent] == ['RATVISION.dailyActive','RATVISION.dailyActive']


def test_default_async_transport_drops_stale_event_after_opt_out_and_reenable(monkeypatch):
    queued = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    real_thread = threading.Thread
    network_calls = []

    class BlockedThread:
        def __init__(self, *, target, args, name, daemon):
            def run():
                queued.set()
                assert release.wait(2)
                try:
                    target(*args)
                finally:
                    finished.set()
            self._thread = real_thread(target=run, name=name, daemon=daemon)

        def start(self):
            self._thread.start()

    monkeypatch.setattr('ratvision.analytics.service.threading.Thread', BlockedThread)
    monkeypatch.setattr('ratvision.analytics.service.urlopen', lambda *args, **kwargs: network_calls.append(args))
    settings = AppSettings(analytics_enabled=True, analytics_install_id='stable-id')
    svc = AnalyticsService(AnalyticsConfig('namespace', 'app-id'))

    assert svc.app_started(settings, {'app_version': '1'}) is True
    assert queued.wait(2)
    svc.set_consent(settings, False)
    svc.set_consent(settings, True)
    assert settings.analytics_install_id == 'stable-id'
    release.set()
    assert finished.wait(2)

    assert network_calls == []


def test_telemetrydeck_url_contains_namespace_and_payload_is_an_array(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return None
        def read(self, _size): return b''

    def fake_urlopen(request, timeout):
        captured['url'] = request.full_url
        captured['body'] = request.data
        captured['timeout'] = timeout
        return Response()

    monkeypatch.setattr('ratvision.analytics.service.urlopen', fake_urlopen)
    settings = AppSettings(analytics_install_id='stable-id')
    svc = AnalyticsService(AnalyticsConfig('io.github.atikhobaev.ratvision', 'app-id'))
    svc._post({'appID': 'app-id'}, settings, 0)

    assert captured['url'] == 'https://nom.telemetrydeck.com/v2/namespace/io.github.atikhobaev.ratvision/'
    assert captured['body'] == b'[{"appID":"app-id"}]'


def test_raw_install_identifier_is_never_serialized():
    sent=[]
    raw_id='11111111-2222-4333-8444-555555555555'
    settings=AppSettings(analytics_install_id=raw_id)
    svc=AnalyticsService(AnalyticsConfig('namespace', 'app-id'), transport=sent.append)
    assert svc.app_started(settings, {'app_version':'1.2.0-beta.1'}) is True
    assert raw_id not in json.dumps(sent[0])
