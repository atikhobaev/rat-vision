from __future__ import annotations
from dataclasses import dataclass
import json, os
from pathlib import Path

DEFAULT_GITHUB_REPOSITORY='atikhobaev/rat-vision'
DEFAULT_TELEMETRYDECK_ENDPOINT='https://nom.telemetrydeck.com/v2/namespace'
DEFAULT_TELEMETRYDECK_NAMESPACE=''
DEFAULT_TELEMETRYDECK_APP_ID=''

def load_build_config() -> dict[str,str]:
    path=Path(__file__).resolve().parent/'resources'/'build_config.json'
    try:
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        return {str(k):str(v) for k,v in data.items() if v is not None}
    except Exception:
        return {}

@dataclass(frozen=True,slots=True)
class ReleaseConfig:
    repository: str=DEFAULT_GITHUB_REPOSITORY
    @property
    def configured(self)->bool: return bool(self.repository and 'OWNER/' not in self.repository and '/' in self.repository)
    @property
    def api_base(self)->str: return f'https://api.github.com/repos/{self.repository}'
    @classmethod
    def from_environment(cls)->'ReleaseConfig':
        built=load_build_config()
        value=os.environ.get('RATVISION_GITHUB_REPOSITORY',built.get('github_repository',DEFAULT_GITHUB_REPOSITORY)).strip()
        return cls(value)
