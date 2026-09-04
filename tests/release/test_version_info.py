from release.generate_version_info import numeric_file_version, render_version_info


def test_beta_version_maps_to_windows_numeric_file_version_and_keeps_public_string():
    assert numeric_file_version('1.2.0-beta.1') == (1,2,0,1)
    text=render_version_info('1.2.0-beta.1')
    assert "filevers=(1, 2, 0, 1)" in text
    assert "ProductVersion', '1.2.0-beta.1'" in text
