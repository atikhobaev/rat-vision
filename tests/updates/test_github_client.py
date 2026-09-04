from ratvision.release_config import ReleaseConfig
from ratvision.updates.github_client import GitHubReleaseClient

RELEASES=[
 {'tag_name':'v1.2.0-beta.2','draft':False,'prerelease':True,'body':'beta2','assets':[{'name':'update-manifest.json','browser_download_url':'https://x/m'}]},
 {'tag_name':'v1.2.0','draft':False,'prerelease':False,'body':'stable','assets':[{'name':'update-manifest.json','browser_download_url':'https://x/s'}]},
]


def test_beta_selects_newest_eligible_release_without_releases_latest():
    client=GitHubReleaseClient(ReleaseConfig('owner/repo'), json_get=lambda url: RELEASES)
    rel=client.find_newer_release('1.2.0-beta.1')
    assert rel.version == '1.2.0'
    assert rel.prerelease is False


def test_stable_does_not_accept_beta_tag_with_false_github_prerelease_flag():
    releases = [
        {'tag_name':'v1.3.0-beta.1','draft':False,'prerelease':False,'assets':[]},
    ]
    client=GitHubReleaseClient(ReleaseConfig('owner/repo'), json_get=lambda url: releases)
    assert client.find_newer_release('1.2.0') is None
