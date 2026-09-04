from __future__ import annotations

from ratvision.domain.models import VisualParameters
from .gamma import GammaController
from .dvc_subprocess import DvcSubprocessController


class WindowsColorBackend:
    def __init__(self, *, gamma=None, dvc=None):
        self.gamma = gamma or GammaController()
        self.dvc = dvc
        if self.dvc is None:
            try:
                self.dvc = DvcSubprocessController()
            except Exception:
                self.dvc = None
        self._dvc_unsupported: set[str] = set()

    def capture(self, display_id: str) -> None:
        self.gamma.capture(display_id)
        if self.dvc is not None and display_id not in self._dvc_unsupported:
            try:
                self.dvc.capture(display_id)
            except Exception:
                self._dvc_unsupported.add(display_id)

    def apply(self, display_id: str, params: VisualParameters) -> None:
        params = params.normalized()
        self.gamma.apply(display_id, params)
        if self.dvc is not None and display_id not in self._dvc_unsupported:
            try:
                self.dvc.set_level(display_id, params.saturation)
            except Exception:
                self._dvc_unsupported.add(display_id)

    def restore(self, display_id: str) -> None:
        self.gamma.restore(display_id)
        if self.dvc is not None:
            try:
                self.dvc.restore(display_id)
            except Exception:
                pass

    def restore_all(self) -> None:
        self.gamma.restore_all()
        if self.dvc is not None:
            try:
                self.dvc.restore_all()
            except Exception:
                pass

    def capabilities(self, display_id: str) -> dict[str, object]:
        saturation = False
        detail: dict[str, object] = {}
        if self.dvc is not None and display_id not in self._dvc_unsupported:
            try:
                detail = self.dvc.capabilities(display_id)
                saturation = bool(detail.get("supported", False))
            except Exception as exc:
                detail = {"supported": False, "reason": str(exc)}
        return {
            "brightness": True,
            "contrast": True,
            "gamma": True,
            "saturation": saturation,
            "saturation_detail": detail,
        }
