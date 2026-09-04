from __future__ import annotations
from pathlib import Path, PurePosixPath, PureWindowsPath
import hashlib, tempfile, os, zipfile
from urllib.request import Request, urlopen


def verify_sha256(path: Path, expected: str) -> None:
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest.lower()!=expected.lower(): raise ValueError('Downloaded update failed SHA-256 verification')


def download_to_temp(url: str, *, suffix: str = '', opener=None) -> Path:
    opener=opener or urlopen
    request=Request(url,headers={'User-Agent':'RAT-VISION-Updater'})
    fd,name=tempfile.mkstemp(prefix='ratvision-update-',suffix=suffix)
    os.close(fd)
    Path(name).unlink(missing_ok=True)
    try:
        with opener(request,timeout=15) as response, open(name,'wb') as out:
            while True:
                chunk=response.read(1024*1024)
                if not chunk: break
                out.write(chunk)
        return Path(name)
    except Exception:
        Path(name).unlink(missing_ok=True); raise


def safe_extract_zip(archive: Path, destination: Path) -> Path:
    archive=Path(archive); destination=Path(destination)
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            posix_path=PurePosixPath(member.filename)
            windows_path=PureWindowsPath(member.filename)
            if (
                posix_path.is_absolute()
                or windows_path.is_absolute()
                or windows_path.root
                or windows_path.anchor
                or windows_path.drive
                or '..' in posix_path.parts
                or '..' in windows_path.parts
            ):
                raise ValueError(f'Unsafe path in update archive: {member.filename}')
        destination.mkdir(parents=True,exist_ok=True)
        zf.extractall(destination)
    return destination
