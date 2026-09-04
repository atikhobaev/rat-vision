from __future__ import annotations
from dataclasses import dataclass
import json
from urllib.request import Request, urlopen
from ratvision.release_config import ReleaseConfig
from .versioning import release_is_eligible, ParsedVersion

@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    name: str
    url: str

@dataclass(frozen=True, slots=True)
class ReleaseInfo:
    version: str
    tag: str
    prerelease: bool
    notes: str
    assets: tuple[ReleaseAsset,...]

    def asset_url(self, name: str) -> str | None:
        return next((a.url for a in self.assets if a.name == name), None)

class GitHubReleaseClient:
    def __init__(self, config: ReleaseConfig, *, json_get=None):
        self.config=config; self._json_get=json_get or self._default_json_get

    @staticmethod
    def _default_json_get(url: str):
        request=Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'RAT-VISION-Updater'})
        with urlopen(request,timeout=8) as response:
            return json.loads(response.read().decode('utf-8'))

    def get_json(self,url:str): return self._json_get(url)

    def list_releases(self) -> list[ReleaseInfo]:
        rows=self._json_get(f'{self.config.api_base}/releases?per_page=20')
        result=[]
        for row in rows:
            if row.get('draft'): continue
            tag=str(row.get('tag_name','')); version=tag[1:] if tag.startswith('v') else tag
            try: ParsedVersion.parse(version)
            except ValueError: continue
            assets=tuple(ReleaseAsset(str(a.get('name','')),str(a.get('browser_download_url',''))) for a in row.get('assets') or [])
            result.append(ReleaseInfo(version,tag,bool(row.get('prerelease')),str(row.get('body') or ''),assets))
        return result

    def find_newer_release(self,current_version:str) -> ReleaseInfo | None:
        candidates=[r for r in self.list_releases() if release_is_eligible(current_version,r.version,prerelease=r.prerelease)]
        return max(candidates,key=lambda r: ParsedVersion.parse(r.version)._key(),default=None)
