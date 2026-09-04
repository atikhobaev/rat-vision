from __future__ import annotations

import faulthandler
from pathlib import Path
import traceback


def install_fault_logging(root, log_path: Path, *, fault_handler=faulthandler):
    """Keep a persistent crash log for fatal native faults and Tk callback exceptions."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = log_path.open("a", encoding="utf-8", buffering=1)
    fault_handler.enable(file=handle, all_threads=True)

    def report_callback_exception(exc_type, exc_value, exc_traceback):
        handle.write("\n--- Tk callback exception ---\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=handle)
        handle.flush()

    root.report_callback_exception = report_callback_exception
    # Keep the file alive for as long as the Tk root exists.
    root._ratvision_fault_log = handle
    return handle
