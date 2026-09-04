from __future__ import annotations

import argparse
import faulthandler
import json
import os
from pathlib import Path

from .dvc_subprocess import execute_dvc_helper_operation


def _log_path() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home()))
    return base / "RAT VISION" / "logs" / "dvc-helper-crash.log"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ratvision-dvc-helper")
    parser.add_argument("operation", choices=["capture", "set"])
    parser.add_argument("--display", required=True)
    parser.add_argument("--level", type=int, default=None)
    parser.add_argument("--result-file", type=Path, required=True)
    return parser


def _write_result(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = _log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as crash_log:
        faulthandler.enable(crash_log, all_threads=True)
        try:
            result = execute_dvc_helper_operation(args.operation, args.display, args.level)
        except Exception as exc:
            _write_result(args.result_file, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})
            return 1
        _write_result(args.result_file, {"ok": True, "result": result})
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
