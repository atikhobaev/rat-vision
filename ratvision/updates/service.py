from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json, os, tempfile, zipfile
from urllib.request import Request, urlopen
from ratvision import __version__
from ratvision.release_config import ReleaseConfig
from .github_client import GitHubReleaseClient, ReleaseInfo
from .manifest import UpdateManifest
from .edition import Edition, detect_edition
from .downloads import download_to_temp, verify_sha256, safe_extract_zip
from .versioning import ParsedVersion
from .apply import launch_installer, launch_portable_helper

class UpdateStatus(str,Enum):
    UNCONFIGURED='unconfigured'; UP_TO_DATE='up_to_date'; AVAILABLE='available'; ERROR='error'; STARTED='started'

@dataclass(frozen=True,slots=True)
class UpdateResult:
    status: UpdateStatus
    title: str
    message: str
    release: ReleaseInfo|None=None
    manifest: UpdateManifest|None=None

class UpdateService:
    def __init__(self, config: ReleaseConfig|None=None, *, client: GitHubReleaseClient|None=None):
        self.config=config or ReleaseConfig.from_environment(); self.client=client or GitHubReleaseClient(self.config)

    def check(self) -> UpdateResult:
        if not self.config.configured:
            return UpdateResult(UpdateStatus.UNCONFIGURED,'UPDATES NOT CONFIGURED','GitHub repository is not configured in this build yet.')
        try:
            release=self.client.find_newer_release(__version__)
            if release is None:
                return UpdateResult(UpdateStatus.UP_TO_DATE,'RAT VISION IS UP TO DATE',f'You are running v{__version__}.')
            manifest_url=release.asset_url('update-manifest.json')
            if not manifest_url: raise ValueError('Release is missing update-manifest.json')
            manifest=UpdateManifest.from_dict(self.client.get_json(manifest_url))
            if manifest.version != release.version: raise ValueError('Release/manifest version mismatch')
            semantic_prerelease=ParsedVersion.parse(release.version).is_prerelease
            if release.prerelease != semantic_prerelease:
                raise ValueError('Release prerelease mismatch')
            expected_channel='beta' if semantic_prerelease else 'stable'
            if manifest.channel != expected_channel:
                raise ValueError('Release/manifest channel mismatch')
            return UpdateResult(UpdateStatus.AVAILABLE,f'RAT VISION v{release.version} AVAILABLE',release.notes or 'A newer release is available.',release,manifest)
        except Exception as exc:
            return UpdateResult(UpdateStatus.ERROR,'UPDATE CHECK FAILED',str(exc))

    def prepare_and_launch(self, result: UpdateResult, app_dir: Path) -> UpdateResult:
        if result.status is not UpdateStatus.AVAILABLE or result.release is None or result.manifest is None:
            return UpdateResult(UpdateStatus.ERROR,'UPDATE NOT READY','No verified update is selected.')
        try:
            edition=detect_edition(app_dir)
            asset=result.manifest.portable if edition is Edition.PORTABLE else result.manifest.installer
            url=result.release.asset_url(asset.asset)
            if not url: raise ValueError(f'Release asset {asset.asset} was not found')
            downloaded=download_to_temp(url,suffix=Path(asset.asset).suffix)
            verify_sha256(downloaded,asset.sha256)
            if edition is Edition.INSTALLER:
                launch_installer(downloaded)
            else:
                stage=Path(tempfile.mkdtemp(prefix='ratvision-stage-'))
                safe_extract_zip(downloaded, stage)
                roots=[p for p in stage.iterdir() if p.is_dir()]
                payload=roots[0] if len(roots)==1 else stage
                launch_portable_helper(payload,app_dir,Path(app_dir)/'RAT VISION.exe',os.getpid())
            return UpdateResult(UpdateStatus.STARTED,'UPDATE STARTED',f'Updating to v{result.manifest.version}.')
        except Exception as exc:
            return UpdateResult(UpdateStatus.ERROR,'UPDATE FAILED',str(exc),result.release,result.manifest)
