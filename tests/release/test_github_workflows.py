from pathlib import Path


def test_ci_and_release_workflows_have_windows_build_contract():
    ci = Path('.github/workflows/ci.yml').read_text(encoding='utf-8')
    rel = Path('.github/workflows/release.yml').read_text(encoding='utf-8')
    for text in (ci, rel):
        assert 'windows-latest' in text
        assert '3.13' in text
    assert 'build-windows' in ci
    assert 'build-release' in rel
    assert 'RAT-VISION-Setup-v' in rel
    assert 'RAT-VISION-Portable-v' in rel
    assert 'SHA256SUMS.txt' in rel
    assert 'update-manifest.json' in rel
    assert 'prerelease' in rel.lower()


def test_windows_builder_embeds_version_metadata_in_exe():
    from pathlib import Path
    text=Path('scripts/build-windows.ps1').read_text(encoding='utf-8')
    assert 'generate_version_info.py' in text
    assert '--version-file $VersionInfo' in text
