from pathlib import Path

from ratvision.controller import AppController
from ratvision.domain.models import AppSettings, DisplayInfo, ForegroundProcess, GameProfile
from ratvision.persistence.settings_store import SettingsStore
from ratvision.platform.simulation import (
    SimulationColorBackend,
    SimulationDisplayProvider,
    SimulationForegroundProvider,
    SimulationStartupBackend,
    SimulationTrayBackend,
)


class FakeRoot:
    def __init__(self, order=None):
        self.after_calls = []
        self.destroyed = False
        self.order = order if order is not None else []

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))
        return len(self.after_calls)

    def destroy(self):
        self.order.append("destroy")
        self.destroyed = True

    def clipboard_clear(self): pass
    def clipboard_append(self, _text): pass
    def update_idletasks(self): pass


class OrderedColor(SimulationColorBackend):
    def __init__(self, order):
        super().__init__(); self.order=order
    def restore_all(self):
        self.order.append("restore")
        super().restore_all()


class OrderedForeground(SimulationForegroundProvider):
    def __init__(self, order):
        super().__init__(); self.order=order
    def stop(self):
        self.order.append("stop_foreground")
        super().stop()


class OrderedTray(SimulationTrayBackend):
    def __init__(self, order):
        super().__init__(); self.order=order
    def stop(self):
        self.order.append("stop_tray")
        super().stop()


def make_controller(tmp_path: Path, root=None, *, order=None):
    root = root or FakeRoot(order)
    displays = [DisplayInfo("D1", "Main", 2560, 1440, 165.0, True, True)]
    settings = AppSettings(profiles=[GameProfile(id="p", name="Game", processes=["game.exe"], display_ids=["D1"])])
    store = SettingsStore(tmp_path / "settings.json")
    store.save(settings)
    foreground = OrderedForeground(order) if order is not None else SimulationForegroundProvider()
    color = OrderedColor(order) if order is not None else SimulationColorBackend()
    tray = OrderedTray(order) if order is not None else SimulationTrayBackend()
    return AppController(
        root=root,
        settings_store=store,
        display_provider=SimulationDisplayProvider(displays),
        foreground_provider=foreground,
        color_backend=color,
        tray_backend=tray,
        startup_backend=SimulationStartupBackend(),
        platform_name="simulation",
        open_url=lambda _url: None,
    )


def test_global_toggle_updates_settings_tray_and_persistence(tmp_path):
    controller = make_controller(tmp_path)
    controller.start_services()
    controller.set_global_enabled(False)
    assert controller.settings.global_enabled is False
    assert controller.tray_backend.enabled is False
    assert controller.settings_store.load(controller.displays).global_enabled is False


def test_foreground_callback_is_marshaled_through_main_thread_pump(tmp_path):
    root = FakeRoot()
    controller = make_controller(tmp_path, root)
    controller.start_services()
    controller.foreground_provider.focus("game.exe")
    assert len(root.after_calls) == 1
    delay, callback = root.after_calls[0]
    assert delay == controller._ui_pump_interval_ms
    active_before = controller.profile_service.get(controller.activation.active_profile_id)
    assert active_before.builtin_id == "global"
    callback()
    assert controller.activation.active_profile_id == "p"


def test_shutdown_restores_before_destroying_root(tmp_path):
    order = []
    root = FakeRoot(order)
    controller = make_controller(tmp_path, root, order=order)
    controller.start_services()
    controller.shutdown()
    assert order.index("stop_foreground") < order.index("restore") < order.index("stop_tray") < order.index("destroy")


def test_background_foreground_event_is_queued_until_main_thread_pump(tmp_path):
    import threading

    root = FakeRoot()
    controller = make_controller(tmp_path, root)
    controller.start_services()
    assert len(root.after_calls) == 1  # one main-thread UI pump only

    thread = threading.Thread(target=lambda: controller.foreground_provider.focus("game.exe"))
    thread.start(); thread.join()

    # Background callback must not call Tk/root.after directly.
    assert len(root.after_calls) == 1
    active_before = controller.profile_service.get(controller.activation.active_profile_id)
    assert active_before.builtin_id == "global"

    _delay, pump = root.after_calls[0]
    pump()
    assert controller.activation.active_profile_id == "p"


def test_profile_toggle_persists_and_reevaluates_current_foreground(tmp_path):
    controller = make_controller(tmp_path)
    controller.current_foreground = ForegroundProcess(1, "game.exe", "Game")
    controller.activation.on_foreground(controller.current_foreground)
    assert controller.activation.active_profile_id == "p"

    controller.set_profile_enabled("p", False)

    assert controller.profile_service.get("p").enabled is False
    active = controller.profile_service.get(controller.activation.active_profile_id)
    assert active.builtin_id == "global"
    loaded = controller.settings_store.load(controller.displays)
    assert controller.profile_service.get("p").enabled is False
    assert loaded.profiles[1].enabled is False


def test_services_apply_global_profile_even_before_first_foreground_event(tmp_path):
    controller = make_controller(tmp_path)
    assert controller.activation.active_profile_id is None
    controller.start_services()
    # start_services runs on Tk/main thread, so the process-independent fallback can apply immediately.
    active = controller.profile_service.get(controller.activation.active_profile_id)
    assert active.builtin_id == "global"
