from __future__ import annotations
from enum import Enum
from pathlib import Path
class Edition(str,Enum): INSTALLER='installer'; PORTABLE='portable'
def detect_edition(app_dir: Path) -> Edition:
    return Edition.PORTABLE if (Path(app_dir)/'portable.flag').exists() else Edition.INSTALLER
