from __future__ import annotations
from pathlib import Path
import subprocess, tempfile


def build_installer_command(installer: Path) -> list[str]:
    return [str(Path(installer)), '/VERYSILENT', '/NORESTART', '/CLOSEAPPLICATIONS', '/RELAUNCH=1']


def build_portable_powershell(stage_dir: Path, app_dir: Path, exe_path: Path, pid: int) -> str:
    def q(path): return str(Path(path)).replace("'","''")
    backup = str(Path(app_dir).with_name(Path(app_dir).name + '.update-backup'))
    return f"""$ErrorActionPreference='Stop'
$pidToWait={int(pid)}
Wait-Process -Id $pidToWait -ErrorAction SilentlyContinue
$stage='{q(stage_dir)}'
$app='{q(app_dir)}'
$backup='{q(backup)}'
$backupCreated=$false
try {{
  if (Test-Path -LiteralPath $backup) {{ Remove-Item -LiteralPath $backup -Recurse -Force }}
  Move-Item -LiteralPath $app -Destination $backup
  $backupCreated=$true
  New-Item -ItemType Directory -Force -Path $app | Out-Null
  Copy-Item -Path (Join-Path $stage '*') -Destination $app -Recurse -Force
  Start-Process -FilePath '{q(exe_path)}'
  Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
}} catch {{
  if ($backupCreated) {{
    if (Test-Path -LiteralPath $app) {{ Remove-Item -LiteralPath $app -Recurse -Force -ErrorAction SilentlyContinue }}
    if (Test-Path -LiteralPath $backup) {{ Move-Item -LiteralPath $backup -Destination $app }}
  }}
  throw
}}
"""


def launch_installer(installer: Path) -> None:
    subprocess.Popen(build_installer_command(installer), close_fds=True)


def launch_portable_helper(stage_dir: Path, app_dir: Path, exe_path: Path, pid: int) -> Path:
    helper=Path(tempfile.gettempdir())/f'ratvision-update-{pid}.ps1'
    helper.write_text(build_portable_powershell(stage_dir,app_dir,exe_path,pid),encoding='utf-8')
    subprocess.Popen(['powershell.exe','-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',str(helper)],close_fds=True)
    return helper
