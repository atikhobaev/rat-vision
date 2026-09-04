from ratvision.release_config import ReleaseConfig
from ratvision.updates.github_client import ReleaseAsset, ReleaseInfo
from ratvision.updates.service import UpdateService, UpdateStatus


class FakeClient:
    def find_newer_release(self, current):
        return ReleaseInfo(
            version='1.2.0', tag='v1.2.0', prerelease=False, notes='Stable release',
            assets=(
                ReleaseAsset('update-manifest.json','https://example/manifest'),
                ReleaseAsset('RAT-VISION-Setup-v1.2.0.exe','https://example/setup'),
                ReleaseAsset('RAT-VISION-Portable-v1.2.0.zip','https://example/portable'),
            ),
        )
    def get_json(self, url):
        assert url == 'https://example/manifest'
        return {
            'version':'1.2.0','channel':'stable',
            'installer':{'asset':'RAT-VISION-Setup-v1.2.0.exe','sha256':'a'*64},
            'portable':{'asset':'RAT-VISION-Portable-v1.2.0.zip','sha256':'b'*64},
        }


def test_configured_beta_update_service_reports_newer_stable_release():
    service=UpdateService(ReleaseConfig('owner/repo'), client=FakeClient())
    result=service.check()
    assert result.status is UpdateStatus.AVAILABLE
    assert result.release.version == '1.2.0'
    assert result.manifest.version == '1.2.0'


class InconsistentPrereleaseClient:
    def find_newer_release(self, current):
        return ReleaseInfo(
            version='1.2.1-beta.1', tag='v1.2.1-beta.1', prerelease=False, notes='',
            assets=(ReleaseAsset('update-manifest.json','https://example/manifest'),),
        )

    def get_json(self, url):
        return {
            'version':'1.2.1-beta.1','channel':'beta',
            'installer':{'asset':'RAT-VISION-Setup-v1.2.1-beta.1.exe','sha256':'a'*64},
            'portable':{'asset':'RAT-VISION-Portable-v1.2.1-beta.1.zip','sha256':'b'*64},
        }


def test_update_service_rejects_release_prerelease_flag_mismatching_semver():
    service=UpdateService(ReleaseConfig('owner/repo'), client=InconsistentPrereleaseClient())
    result=service.check()
    assert result.status is UpdateStatus.ERROR
    assert 'prerelease mismatch' in result.message.lower()
