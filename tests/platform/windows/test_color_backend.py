from ratvision.domain.models import VisualParameters
from ratvision.platform.windows.color_backend import WindowsColorBackend


class FakeGamma:
    def __init__(self): self.calls = []
    def capture(self, display): self.calls.append(("capture", display))
    def apply(self, display, params): self.calls.append(("apply", display, params))
    def restore(self, display): self.calls.append(("restore", display))
    def restore_all(self): self.calls.append(("restore_all",))


class FakeDvc:
    def __init__(self, supported=True): self.supported = supported; self.calls=[]
    def capture(self, display):
        self.calls.append(("capture", display))
        if not self.supported: raise RuntimeError("unsupported")
    def set_level(self, display, level):
        self.calls.append(("set", display, level))
        if not self.supported: raise RuntimeError("unsupported")
    def restore(self, display): self.calls.append(("restore", display))
    def restore_all(self): self.calls.append(("restore_all",))
    def capabilities(self, display): return {"supported": self.supported}


def test_color_backend_keeps_gamma_working_when_dvc_is_unsupported():
    gamma = FakeGamma(); dvc = FakeDvc(False)
    backend = WindowsColorBackend(gamma=gamma, dvc=dvc)
    params = VisualParameters(0.6, 0.7, 1.2, 80)
    backend.capture("D1")
    backend.apply("D1", params)
    assert ("apply", "D1", params) in gamma.calls
    caps = backend.capabilities("D1")
    assert caps["gamma"] is True
    assert caps["saturation"] is False


def test_color_backend_restore_all_restores_both_mechanisms():
    gamma = FakeGamma(); dvc = FakeDvc(True)
    backend = WindowsColorBackend(gamma=gamma, dvc=dvc)
    backend.restore_all()
    assert gamma.calls[-1] == ("restore_all",)
    assert dvc.calls[-1] == ("restore_all",)
