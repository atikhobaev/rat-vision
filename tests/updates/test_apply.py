from pathlib import Path
import subprocess

from ratvision.updates.apply import build_installer_command, build_portable_powershell


def test_installer_command_is_silent_and_requests_relaunch(tmp_path):
    exe=tmp_path/'setup.exe'
    cmd=build_installer_command(exe)
    assert str(exe) == cmd[0]
    assert '/VERYSILENT' in cmd and '/NORESTART' in cmd and '/RELAUNCH=1' in cmd


def test_portable_helper_script_waits_replaces_and_relaunches(tmp_path):
    text=build_portable_powershell(tmp_path/'stage', tmp_path/'app', tmp_path/'app'/'RAT VISION.exe', 123)
    lower=text.lower()
    assert 'wait-process' in lower
    assert 'copy-item' in lower
    assert 'start-process' in lower


def test_portable_helper_uses_backup_and_rollback_before_relaunch(tmp_path):
    text=build_portable_powershell(tmp_path/'stage',tmp_path/'app',tmp_path/'app'/'RAT VISION.exe',321).lower()
    assert 'update-backup' in text
    assert 'move-item' in text
    assert 'catch {' in text


def test_portable_helper_keeps_working_backup_after_successful_relaunch(tmp_path):
    app = tmp_path/'app'
    stage = tmp_path/'stage'
    app.mkdir()
    stage.mkdir()
    (app/'old.txt').write_text('working version')
    (stage/'new.txt').write_text('replacement version')
    script = tmp_path/'apply.ps1'
    script.write_text(
        build_portable_powershell(stage, app, Path('C:/Windows/System32/cmd.exe'), 999999),
        encoding='utf-8',
    )

    result = subprocess.run(
        ['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert (app/'new.txt').read_text() == 'replacement version'
    assert (tmp_path/'app.update-backup'/'old.txt').read_text() == 'working version'


def test_portable_helper_catch_restores_backup_when_replacement_fails(tmp_path):
    app = tmp_path/'app'
    missing_stage = tmp_path/'missing-stage'
    app.mkdir()
    (app/'old.txt').write_text('working version')
    script = tmp_path/'apply.ps1'
    script.write_text(
        build_portable_powershell(missing_stage, app, Path('C:/Windows/System32/cmd.exe'), 999999),
        encoding='utf-8',
    )

    result = subprocess.run(
        ['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
    assert (app/'old.txt').read_text() == 'working version'
    assert not (tmp_path/'app.update-backup').exists()


def test_portable_helper_leaves_current_app_untouched_when_stale_backup_cleanup_fails(tmp_path):
    app = tmp_path/'app'
    stage = tmp_path/'stage'
    stale_backup = tmp_path/'app.update-backup'
    app.mkdir()
    stage.mkdir()
    stale_backup.mkdir()
    (app/'current.txt').write_text('current working version')
    (stage/'new.txt').write_text('replacement version')
    (stale_backup/'stale.txt').write_text('stale partial backup')
    script = tmp_path/'apply.ps1'
    fail_stale_cleanup = r"""
function Remove-Item {
  param([string]$LiteralPath, [switch]$Recurse, [switch]$Force, [object]$ErrorAction)
  if ($LiteralPath -like '*.update-backup') { throw 'simulated stale-backup cleanup failure' }
  Microsoft.PowerShell.Management\Remove-Item -LiteralPath $LiteralPath -Recurse:$Recurse -Force:$Force -ErrorAction $ErrorAction
}
"""
    script.write_text(
        fail_stale_cleanup + build_portable_powershell(stage, app, Path('C:/Windows/System32/cmd.exe'), 999999),
        encoding='utf-8',
    )

    result = subprocess.run(
        ['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
    assert (app/'current.txt').read_text() == 'current working version'
    assert not (app/'stale.txt').exists()
    assert (stale_backup/'stale.txt').read_text() == 'stale partial backup'


def test_portable_helper_rolls_back_when_relaunch_fails(tmp_path):
    app = tmp_path/'app'
    stage = tmp_path/'stage'
    app.mkdir()
    stage.mkdir()
    (app/'old.txt').write_text('working version')
    (stage/'new.txt').write_text('replacement version')
    script = tmp_path/'apply.ps1'
    fail_relaunch = "function Start-Process { param([string]$FilePath) throw 'simulated relaunch failure' }`n"
    script.write_text(
        fail_relaunch + build_portable_powershell(stage, app, app/'RAT VISION.exe', 999999),
        encoding='utf-8',
    )

    result = subprocess.run(
        ['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
    assert (app/'old.txt').read_text() == 'working version'
    assert not (app/'new.txt').exists()
    assert not (tmp_path/'app.update-backup').exists()
