from ratvision.domain.models import VisualParameters
from ratvision.platform.windows.gamma import GammaController, calculate_lut


def test_default_lut_is_identity_curve():
    lut = calculate_lut(VisualParameters(0.5, 0.5, 1.0, 0))
    assert len(lut) == 256
    assert [lut[i] for i in (0, 1, 64, 128, 192, 255)] == [0, 257, 16448, 32896, 49344, 65535]
    assert all(a <= b for a, b in zip(lut, lut[1:]))


def test_non_default_lut_matches_upstream_formula_samples():
    lut = calculate_lut(VisualParameters(0.6, 0.7, 1.2, 55))
    assert [lut[i] for i in (0, 1, 64, 128, 192, 255)] == [0, 202, 21970, 39345, 55255, 65535]


class FakeGammaApi:
    def __init__(self):
        self.ramps = {"D1": (tuple(range(256)),) * 3, "D2": (tuple(reversed(range(256))),) * 3}
        self.set_calls = []

    def get_ramp(self, display_id):
        return self.ramps[display_id]

    def set_ramp(self, display_id, ramp):
        self.set_calls.append((display_id, ramp))
        self.ramps[display_id] = ramp
        return True


def test_gamma_controller_restores_independent_display_baselines():
    api = FakeGammaApi()
    controller = GammaController(api=api)
    controller.capture("D1")
    controller.capture("D2")
    baseline1 = controller.baselines["D1"]
    baseline2 = controller.baselines["D2"]
    controller.apply("D1", VisualParameters(0.6, 0.5, 1.0, 0))
    controller.apply("D2", VisualParameters(0.4, 0.5, 1.0, 0))
    controller.restore("D1")
    controller.restore("D2")
    assert api.set_calls[-2:] == [("D1", baseline1), ("D2", baseline2)]


def test_gamma_controller_reapplies_until_restore():
    import time
    api = FakeGammaApi()
    controller = GammaController(api=api, reapply_interval=0.01)
    controller.apply("D1", VisualParameters(0.6, 0.5, 1.0, 0))
    time.sleep(0.035)
    applied_before_restore = len(api.set_calls)
    assert applied_before_restore >= 2
    controller.restore("D1")
    calls_after_restore = len(api.set_calls)
    time.sleep(0.025)
    assert len(api.set_calls) == calls_after_restore
