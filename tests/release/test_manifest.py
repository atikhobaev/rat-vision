from pathlib import Path
import json
from release.generate_manifest import build_manifest, sha256_file, write_release_metadata


def test_build_manifest_has_exact_public_assets_and_beta_channel(tmp_path):
    installer = tmp_path / 'RAT-VISION-Setup-v1.2.0-beta.1.exe'; installer.write_bytes(b'installer')
    portable = tmp_path / 'RAT-VISION-Portable-v1.2.0-beta.1.zip'; portable.write_bytes(b'portable')
    manifest = build_manifest('1.2.0-beta.1', installer, portable)
    assert manifest['version'] == '1.2.0-beta.1'
    assert manifest['channel'] == 'beta'
    assert manifest['installer']['asset'] == installer.name
    assert manifest['portable']['asset'] == portable.name
    assert manifest['installer']['sha256'] == sha256_file(installer)


def test_write_release_metadata_creates_manifest_and_sha256s(tmp_path):
    installer = tmp_path / 'RAT-VISION-Setup-v1.2.0-beta.1.exe'; installer.write_bytes(b'a')
    portable = tmp_path / 'RAT-VISION-Portable-v1.2.0-beta.1.zip'; portable.write_bytes(b'b')
    manifest_path, sums_path = write_release_metadata('1.2.0-beta.1', installer, portable, tmp_path)
    assert json.loads(manifest_path.read_text())['portable']['asset'] == portable.name
    text = sums_path.read_text()
    assert installer.name in text and portable.name in text
