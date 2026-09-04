from __future__ import annotations
import hashlib, json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(version: str, installer_path: Path, portable_path: Path) -> dict:
    channel = 'beta' if '-' in version else 'stable'
    return {
        'version': version,
        'channel': channel,
        'installer': {'asset': Path(installer_path).name, 'sha256': sha256_file(Path(installer_path))},
        'portable': {'asset': Path(portable_path).name, 'sha256': sha256_file(Path(portable_path))},
    }


def write_release_metadata(version: str, installer_path: Path, portable_path: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(version, installer_path, portable_path)
    manifest_path = output_dir / 'update-manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    sums_path = output_dir / 'SHA256SUMS.txt'
    rows = [
        f"{sha256_file(Path(installer_path))}  {Path(installer_path).name}",
        f"{sha256_file(Path(portable_path))}  {Path(portable_path).name}",
        f"{sha256_file(manifest_path)}  {manifest_path.name}",
    ]
    sums_path.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    return manifest_path, sums_path
