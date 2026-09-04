from __future__ import annotations
from dataclasses import dataclass
import re

_RE = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

@dataclass(frozen=True, slots=True)
class ParsedVersion:
    major: int
    minor: int
    patch: int
    prerelease: tuple[tuple[int, object], ...] = ()

    @classmethod
    def parse(cls, value: str) -> "ParsedVersion":
        match=_RE.fullmatch(value.strip())
        if not match: raise ValueError(f"Unsupported version: {value}")
        pre=[]
        if match.group(4):
            for part in match.group(4).split('.'):
                if part.isdigit():
                    if len(part) > 1 and part.startswith('0'):
                        raise ValueError(f"Unsupported version: {value}")
                    pre.append((0,int(part)))
                else:
                    pre.append((1,part))
        return cls(int(match.group(1)),int(match.group(2)),int(match.group(3)),tuple(pre))

    @property
    def is_prerelease(self) -> bool: return bool(self.prerelease)

    def _key(self):
        # Stable sorts after any prerelease of the same core.
        return (self.major,self.minor,self.patch, 1 if not self.prerelease else 0, self.prerelease)

    def __lt__(self, other: "ParsedVersion") -> bool: return self._key() < other._key()
    def __le__(self, other: "ParsedVersion") -> bool: return self._key() <= other._key()


def is_newer(candidate: str, current: str) -> bool:
    return ParsedVersion.parse(current) < ParsedVersion.parse(candidate)


def release_is_eligible(current: str, candidate: str, *, prerelease: bool) -> bool:
    cur=ParsedVersion.parse(current)
    candidate_version=ParsedVersion.parse(candidate)
    if candidate_version.is_prerelease != prerelease: return False
    if not cur.is_prerelease and candidate_version.is_prerelease: return False
    return is_newer(candidate,current)
