from pathlib import Path


def test_codex_handoff_has_complete_publication_checklist():
    text = Path('CODEX_GITHUB_RELEASE.md').read_text(encoding='utf-8').lower()
    for word in ['audit','test','build','tag','release','upload','virustotal','sha256','updater','download']:
        assert word in text


def test_codex_handoff_matches_default_on_opt_out_analytics_contract():
    text = Path('CODEX_GITHUB_RELEASE.md').read_text(encoding='utf-8').lower()
    assert 'on by default' in text
    assert 'opt out' in text
    assert 'off by default' not in text
    assert 'before opt-in' not in text
