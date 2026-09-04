from ratvision.platform.windows.startup import WindowsStartupBackend


class FakeRegistry:
    HKEY_CURRENT_USER = object()
    KEY_READ = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self):
        self.values = {}

    class Key:
        def __init__(self, registry): self.registry = registry
        def __enter__(self): return self
        def __exit__(self, *args): pass

    def OpenKey(self, *_args, **_kwargs): return self.Key(self)
    def QueryValueEx(self, _key, name):
        if name not in self.values: raise FileNotFoundError
        return self.values[name], self.REG_SZ
    def SetValueEx(self, _key, name, _reserved, _kind, value): self.values[name] = value
    def DeleteValue(self, _key, name):
        if name not in self.values: raise FileNotFoundError
        del self.values[name]


def test_startup_backend_sets_and_removes_run_entry():
    registry = FakeRegistry()
    backend = WindowsStartupBackend(command='"C:\\RatVision\\ratvision.exe"', registry=registry)
    assert backend.is_enabled() is False
    backend.set_enabled(True)
    assert backend.is_enabled() is True
    assert registry.values["RAT VISION"] == '"C:\\RatVision\\ratvision.exe"'
    backend.set_enabled(False)
    assert backend.is_enabled() is False
