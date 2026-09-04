from __future__ import annotations
from dataclasses import dataclass
import re
from .versioning import ParsedVersion

_SHA=re.compile(r"^[0-9a-fA-F]{64}$")

@dataclass(frozen=True, slots=True)
class ManifestAsset:
    asset: str
    sha256: str

@dataclass(frozen=True, slots=True)
class UpdateManifest:
    version: str
    channel: str
    installer: ManifestAsset
    portable: ManifestAsset

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateManifest":
        version=str(data.get('version','')).strip(); channel=str(data.get('channel','')).strip()
        if not version or channel not in {'beta','stable'}: raise ValueError('Invalid update manifest header')
        parsed_version=ParsedVersion.parse(version)
        expected_channel='beta' if parsed_version.is_prerelease else 'stable'
        if channel != expected_channel: raise ValueError('Manifest channel mismatch')
        def asset(name: str) -> ManifestAsset:
            row=data.get(name) or {}; filename=str(row.get('asset','')).strip(); digest=str(row.get('sha256','')).lower()
            if not filename or not _SHA.fullmatch(digest): raise ValueError(f'Invalid {name} asset')
            expected = f'RAT-VISION-Setup-v{version}.exe' if name == 'installer' else f'RAT-VISION-Portable-v{version}.zip'
            if filename != expected: raise ValueError(f'{name} asset/version mismatch')
            return ManifestAsset(filename,digest)
        return cls(version,channel,asset('installer'),asset('portable'))
