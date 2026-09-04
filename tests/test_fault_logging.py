from pathlib import Path

from ratvision.runtime_faults import install_fault_logging


class FakeFaultHandler:
    def __init__(self):
        self.calls = []

    def enable(self, *, file, all_threads):
        self.calls.append((file, all_threads))


class FakeRoot:
    report_callback_exception = None


def test_fault_logging_captures_tk_callback_traceback(tmp_path: Path):
    root = FakeRoot()
    fault_handler = FakeFaultHandler()
    handle = install_fault_logging(root, tmp_path / "crash.log", fault_handler=fault_handler)
    try:
        assert fault_handler.calls[0][1] is True
        try:
            raise RuntimeError("focus crash probe")
        except RuntimeError as exc:
            root.report_callback_exception(type(exc), exc, exc.__traceback__)
        handle.flush()
        text = (tmp_path / "crash.log").read_text(encoding="utf-8")
        assert "RuntimeError: focus crash probe" in text
    finally:
        handle.close()
