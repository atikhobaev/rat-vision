from pathlib import Path


def test_inno_installer_is_per_user_and_update_safe():
    text = Path('installer/rat-vision.iss').read_text(encoding='utf-8').lower()
    assert 'privilegesrequired=lowest' in text
    assert '{localappdata}\\programs\\rat vision' in text
    assert '{group}\\rat vision' in text
    assert 'desktopicon' in text
    assert 'rat vision.exe' in text
    assert '{appdata}\\rat vision' not in text or 'delete' not in text


def test_public_distributions_include_legal_notices():
    from pathlib import Path
    assert Path('LICENSE').exists()
    text=Path('installer/rat-vision.iss').read_text(encoding='utf-8')
    release=Path('release/build-release.ps1').read_text(encoding='utf-8')
    assert '..\\LICENSE' in text and 'LICENSES.md' in text
    assert "Join-Path $Root 'LICENSE'" in release and 'LICENSES.md' in release
    assert 'third_party\\licenses' in text
    assert "Join-Path $Root 'third_party'" in release
    for notice in ('CPython-LICENSE.txt', 'Tcl-Tk-license.terms'):
        assert Path('third_party/licenses', notice).exists()


def test_release_workflow_publishes_hashes_from_the_actual_build():
    workflow = Path('.github/workflows/release.yml').read_text(encoding='utf-8')
    assert 'RELEASE_NOTES.generated.md' in workflow
    assert 'SHA256SUMS.txt' in workflow
    assert 'body_path: release/out/RELEASE_NOTES.generated.md' in workflow
