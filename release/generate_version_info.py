from __future__ import annotations
import argparse, re
from pathlib import Path


def numeric_file_version(version: str) -> tuple[int,int,int,int]:
    match=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:-beta\.(\d+))?',version)
    if not match: raise ValueError(f'Unsupported public version: {version}')
    return tuple(int(v or 0) for v in match.groups())  # type: ignore[return-value]


def render_version_info(version: str) -> str:
    a,b,c,d=numeric_file_version(version)
    return f'''VSVersionInfo(\n  ffi=FixedFileInfo(\n    filevers=({a}, {b}, {c}, {d}),\n    prodvers=({a}, {b}, {c}, {d}),\n    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)\n  ),\n  kids=[\n    StringFileInfo([StringTable('040904B0', [\n      StringStruct('CompanyName', 'RAT VISION'),\n      StringStruct('FileDescription', 'RAT VISION'),\n      StringStruct('FileVersion', '{version}'),\n      StringStruct('InternalName', 'RAT VISION'),\n      StringStruct('OriginalFilename', 'RAT VISION.exe'),\n      StringStruct('ProductName', 'RAT VISION'),\n      StringStruct('ProductVersion', '{version}')\n    ])]),\n    VarFileInfo([VarStruct('Translation', [1033, 1200])])\n  ]\n)\n'''


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument('--version',required=True); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(render_version_info(args.version),encoding='utf-8'); return 0

if __name__=='__main__': raise SystemExit(main())
