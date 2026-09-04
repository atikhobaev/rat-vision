from ratvision.domain.models import ForegroundProcess
from ratvision.platform.windows.foreground import WindowsForegroundProvider


class FakeUser32:
    def __init__(self):
        self.hook_calls = []
        self.unhook_calls = []

    def SetWinEventHook(self, event_min, event_max, module, callback, pid, tid, flags):
        self.hook_calls.append((event_min, event_max, callback, flags))
        return 12345

    def UnhookWinEvent(self, hook):
        self.unhook_calls.append(hook)
        return 1


def test_foreground_provider_retains_callback_and_unhooks():
    user32 = FakeUser32()
    native_wrappers = []

    def factory(py_callback):
        wrapper = object()
        native_wrappers.append((wrapper, py_callback))
        return wrapper

    provider = WindowsForegroundProvider(
        user32=user32,
        resolver=lambda hwnd: ForegroundProcess(77, "huntgame.exe", "Hunt"),
        callback_factory=factory,
    )
    seen = []
    provider.start(seen.append)
    assert provider._native_callback is native_wrappers[0][0]
    assert user32.hook_calls[0][0:2] == (3, 3)
    native_wrappers[0][1](None, 3, 999, 0, 0, 0, 0)
    assert seen[-1].executable == "huntgame.exe"
    provider.stop()
    assert user32.unhook_calls == [12345]
    assert provider._native_callback is None
