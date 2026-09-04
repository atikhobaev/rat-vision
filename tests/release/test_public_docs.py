from pathlib import Path


def test_readme_positions_rat_vision_as_display_output_not_cheat():
    text = Path('README.md').read_text(encoding='utf-8')
    required = ['🐀 RAT VISION','🛡️ NOT A CHEAT','🎯 What it is for','✨ Features','📸 Screenshots','🚀 Download','📦 Installer vs Portable','🌐 Global Profile','🖥️ Multi-monitor','🔄 Updates','🛡️ Security & VirusTotal','📊 Anonymous analytics','☕ Support']
    for phrase in required:
        assert phrase in text
    lower = text.lower()
    assert 'changes what your monitor displays' in lower
    assert 'does not inject' in lower
    assert 'game memory' in lower
    assert 'gamma' in lower


def test_public_support_documents_exist():
    for name in ['CHANGELOG.md','SECURITY.md','CONTRIBUTING.md','docs/RELEASE.md','docs/UPDATE_PROTOCOL.md','.github/ISSUE_TEMPLATE/bug_report.yml','.github/ISSUE_TEMPLATE/feature_request.yml','.github/PULL_REQUEST_TEMPLATE.md']:
        assert Path(name).exists(), name


def test_analytics_doc_is_explicit_opt_out_and_forbids_sensitive_fields():
    text=Path('docs/ANALYTICS.md').read_text(encoding='utf-8').lower()
    assert 'on by default' in text and 'opt out' in text
    readme=Path('README.md').read_text(encoding='utf-8').lower()
    assert 'enabled by default' in readme and 'turn it off' in readme
    for phrase in ('executable names','profile names','file paths','windows username'):
        assert phrase in text


def test_readme_has_prominent_beta_download_links_and_release_notes_exist():
    text=Path('README.md').read_text(encoding='utf-8')
    assert '⬇️ DOWNLOAD WINDOWS INSTALLER' in text
    assert '⬇️ DOWNLOAD PORTABLE ZIP' in text
    notes=Path('release/RELEASE_NOTES.md').read_text(encoding='utf-8')
    assert 'Public beta' in notes and 'Display output, not a cheat' in notes
