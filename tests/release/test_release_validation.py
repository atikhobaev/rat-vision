import pytest
from release.validate_release import validate_release_contract


def test_release_contract_accepts_matching_beta():
    validate_release_contract('v1.2.0-beta.1', '1.2.0-beta.1', {
        'version':'1.2.0-beta.1','channel':'beta',
        'installer':{'asset':'RAT-VISION-Setup-v1.2.0-beta.1.exe','sha256':'a'*64},
        'portable':{'asset':'RAT-VISION-Portable-v1.2.0-beta.1.zip','sha256':'b'*64},
    })


def test_release_contract_rejects_mismatch():
    with pytest.raises(ValueError):
        validate_release_contract('v1.2.0', '1.2.0-beta.1', {'version':'1.2.0-beta.1'})


def test_release_builder_keeps_portable_flag_out_of_installer_source():
    from pathlib import Path
    text = Path('release/build-release.ps1').read_text(encoding='utf-8')
    assert "$PortableStage" in text
    assert "Set-Content -Path (Join-Path $PortableStage 'portable.flag')" in text
    assert "Set-Content -Path (Join-Path $Dist 'portable.flag')" not in text


def test_release_builder_uses_private_build_python_after_one_click_build():
    from pathlib import Path
    text=Path('release/build-release.ps1').read_text(encoding='utf-8')
    assert '.build-venv\\Scripts\\python.exe' in text
    assert '& python -c' not in text


def test_release_builder_embeds_repository_and_optional_telemetrydeck_config():
    from pathlib import Path
    text=Path('release/build-release.ps1').read_text(encoding='utf-8')
    assert 'GitHubRepository' in text and 'build_config.json' in text
    assert 'TelemetryDeckNamespace' in text
    assert 'TelemetryDeckAppId' in text


def test_release_builder_cleans_output_before_building_assets():
    from pathlib import Path
    text=Path('release/build-release.ps1').read_text(encoding='utf-8')
    assert 'Remove-Item $Out -Recurse -Force' in text


def test_release_builder_restores_placeholder_build_config_after_packaging():
    from pathlib import Path
    text=Path('release/build-release.ps1').read_text(encoding='utf-8')
    assert 'OriginalBuildConfig' in text
    assert 'finally {' in text
