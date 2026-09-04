import pytest
from ratvision.updates.manifest import UpdateManifest


def test_manifest_parses_matching_public_assets():
    m=UpdateManifest.from_dict({'version':'1.2.1','channel':'stable','installer':{'asset':'RAT-VISION-Setup-v1.2.1.exe','sha256':'a'*64},'portable':{'asset':'RAT-VISION-Portable-v1.2.1.zip','sha256':'b'*64}})
    assert m.version == '1.2.1'
    assert m.portable.asset.endswith('.zip')


def test_manifest_rejects_bad_hash():
    with pytest.raises(ValueError):
        UpdateManifest.from_dict({'version':'1.2.1','channel':'stable','installer':{'asset':'x','sha256':'bad'},'portable':{'asset':'y','sha256':'b'*64}})


def test_manifest_rejects_asset_filename_for_other_version():
    with pytest.raises(ValueError):
        UpdateManifest.from_dict({'version':'1.2.1','channel':'stable','installer':{'asset':'RAT-VISION-Setup-v1.2.0.exe','sha256':'a'*64},'portable':{'asset':'RAT-VISION-Portable-v1.2.1.zip','sha256':'b'*64}})


@pytest.mark.parametrize(
    ('version', 'channel'),
    [('1.2.1-beta.1', 'stable'), ('1.2.1', 'beta')],
)
def test_manifest_rejects_channel_mismatching_semantic_version(version, channel):
    with pytest.raises(ValueError, match='channel mismatch'):
        UpdateManifest.from_dict({
            'version':version,
            'channel':channel,
            'installer':{'asset':f'RAT-VISION-Setup-v{version}.exe','sha256':'a'*64},
            'portable':{'asset':f'RAT-VISION-Portable-v{version}.zip','sha256':'b'*64},
        })
