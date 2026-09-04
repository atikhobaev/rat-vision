from pathlib import Path


def test_readme_hierarchy_leads_with_product_and_downloads_before_detailed_trust_block():
    text = Path('README.md').read_text(encoding='utf-8')
    ordered = [
        '# 🐀 RAT VISION',
        '## 🚀 Download',
        '## 🖥️ RAT VISION in action',
        '## ✨ Features',
        '## 🎯 Typical usage',
        '## 🧪 How it works',
        '## 🛡️ NOT A CHEAT',
        '## 🖥️ Multi-monitor',
        '## 🔄 Updates',
        '## 📊 Pseudonymous usage analytics',
        '## 🛡️ Security & VirusTotal',
        '## 🧑‍💻 Build from source',
        '## ☕ Support',
        '## 📜 Licenses',
    ]
    positions = [text.index(phrase) for phrase in ordered]
    assert positions == sorted(positions)
    assert text.count('Display utility only — no injection, no memory access, no game modification.') == 1
    assert text.count('docs/images/support-the-lab-banner.png') == 1
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
