from pathlib import Path
import tomllib


def test_setuptools_package_discovery_is_limited_to_ratvision():
    data=tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
    find=data['tool']['setuptools']['packages']['find']
    assert find['include'] == ['ratvision*']
    assert 'release*' in find['exclude'] and 'installer*' in find['exclude']
