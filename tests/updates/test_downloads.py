from pathlib import Path
import hashlib
import pytest
from ratvision.updates.downloads import verify_sha256


def test_hash_verification_accepts_exact_file_and_rejects_mismatch(tmp_path):
    p=tmp_path/'x.bin'; p.write_bytes(b'abc')
    good=hashlib.sha256(b'abc').hexdigest()
    verify_sha256(p,good)
    with pytest.raises(ValueError): verify_sha256(p,'0'*64)


def test_safe_zip_extraction_rejects_parent_traversal(tmp_path):
    import zipfile
    from ratvision.updates.downloads import safe_extract_zip
    archive=tmp_path/'bad.zip'
    with zipfile.ZipFile(archive,'w') as zf:
        zf.writestr('../escape.txt','bad')
    with pytest.raises(ValueError):
        safe_extract_zip(archive,tmp_path/'stage')


@pytest.mark.parametrize('member', [
    r'..\escape.txt',
    r'\escape.txt',
    r'C:\escape.txt',
    r'\\server\share\escape.txt',
    r'safe/..\../escape.txt',
    '/escape.txt',
])
def test_safe_zip_extraction_rejects_windows_and_mixed_unsafe_paths(tmp_path, member):
    import zipfile
    from ratvision.updates.downloads import safe_extract_zip
    archive=tmp_path/'bad.zip'
    with zipfile.ZipFile(archive,'w') as zf:
        zf.writestr(member,'bad')
    destination=tmp_path/'stage'
    with pytest.raises(ValueError, match='Unsafe path'):
        safe_extract_zip(archive,destination)
    assert not destination.exists()


def test_safe_zip_validates_every_entry_before_creating_destination(tmp_path):
    import zipfile
    from ratvision.updates.downloads import safe_extract_zip
    archive=tmp_path/'partly-bad.zip'
    with zipfile.ZipFile(archive,'w') as zf:
        zf.writestr('safe/file.txt','good')
        zf.writestr('../escape.txt','bad')
    destination=tmp_path/'stage'
    with pytest.raises(ValueError, match='Unsafe path'):
        safe_extract_zip(archive,destination)
    assert not destination.exists()
