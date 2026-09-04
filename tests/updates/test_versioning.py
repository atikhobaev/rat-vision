from ratvision.updates.versioning import ParsedVersion, is_newer, release_is_eligible
import pytest


def test_semantic_beta_order_and_stable_promotion():
    assert is_newer('1.2.0-beta.2','1.2.0-beta.1')
    assert is_newer('1.2.0','1.2.0-beta.9')
    assert not is_newer('1.2.0-beta.1','1.2.0-beta.1')


def test_stable_build_ignores_prerelease_but_beta_accepts_it():
    assert not release_is_eligible('1.2.0','1.3.0-beta.1', prerelease=True)
    assert release_is_eligible('1.2.0-beta.1','1.2.0-beta.2', prerelease=True)


def test_release_metadata_must_match_semantic_prerelease_status():
    assert not release_is_eligible('1.2.0', '1.3.0-beta.1', prerelease=False)
    assert not release_is_eligible('1.2.0-beta.1', '1.2.0', prerelease=True)


@pytest.mark.parametrize('value', [
    '01.2.3',
    '1.02.3',
    '1.2.03',
    '1.2.3-01',
    '1.2.3-beta.01',
    '1.2.3-beta..1',
    '1.2.3-beta.',
])
def test_parse_rejects_malformed_semantic_versions(value):
    with pytest.raises(ValueError, match='Unsupported version'):
        ParsedVersion.parse(value)


def test_prerelease_identifiers_preserve_case_sensitive_semver_precedence():
    parsed=ParsedVersion.parse('1.2.3-Beta')
    assert parsed.prerelease == ((1, 'Beta'),)
    assert is_newer('1.2.3-beta', '1.2.3-Beta')
