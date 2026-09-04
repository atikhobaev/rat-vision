from ratvision.updates.edition import Edition, detect_edition


def test_portable_flag_selects_portable_otherwise_installer(tmp_path):
    assert detect_edition(tmp_path) is Edition.INSTALLER
    (tmp_path/'portable.flag').write_text('x')
    assert detect_edition(tmp_path) is Edition.PORTABLE
