from __future__ import annotations
import re


def validate_release_contract(tag: str, version: str, manifest: dict) -> None:
    if tag != f'v{version}':
        raise ValueError(f'tag/version mismatch: {tag} vs {version}')
    if manifest.get('version') != version:
        raise ValueError('manifest version mismatch')
    expected_channel = 'beta' if '-' in version else 'stable'
    if manifest.get('channel') != expected_channel:
        raise ValueError('manifest channel mismatch')
    for key, prefix, suffix in (
        ('installer', 'RAT-VISION-Setup-v', '.exe'),
        ('portable', 'RAT-VISION-Portable-v', '.zip'),
    ):
        row = manifest.get(key) or {}
        if row.get('asset') != f'{prefix}{version}{suffix}':
            raise ValueError(f'{key} filename mismatch')
        digest = row.get('sha256','')
        if not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
            raise ValueError(f'{key} SHA256 invalid')
