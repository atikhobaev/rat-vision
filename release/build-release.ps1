param(
  [string]$Version = '1.2.0-beta.1',
  [string]$Iscc = '',
  [string]$GitHubRepository = 'atikhobaev/rat-vision',
  [string]$TelemetryDeckNamespace = '',
  [string]$TelemetryDeckAppId = ''
)
$ErrorActionPreference='Stop'
$Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location $Root
$BuildConfigPath=Join-Path $Root 'ratvision\resources\build_config.json'
$OriginalBuildConfig = if (Test-Path $BuildConfigPath) { [IO.File]::ReadAllText($BuildConfigPath) } else { $null }
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

try {
  $BuildConfig = @{
    github_repository = $GitHubRepository
    telemetrydeck_endpoint = 'https://nom.telemetrydeck.com/v2/namespace'
    telemetrydeck_namespace = $TelemetryDeckNamespace
    telemetrydeck_app_id = $TelemetryDeckAppId
  } | ConvertTo-Json
  [IO.File]::WriteAllText($BuildConfigPath, $BuildConfig, $Utf8NoBom)

  $BuildScript=Join-Path $Root 'scripts\build-windows.ps1'
  & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $BuildScript
  if ($LASTEXITCODE -ne 0) { throw 'Application build failed' }

  $BuildPython=Join-Path $Root '.build-venv\Scripts\python.exe'
  if (-not (Test-Path $BuildPython)) { throw 'Private build Python was not found after application build' }
  $Dist=Join-Path $Root 'dist\RAT VISION'
  $Out=Join-Path $Root 'release\out'
  if (Test-Path $Out) { Remove-Item $Out -Recurse -Force }
  New-Item -ItemType Directory -Force $Out | Out-Null

  $Stage=Join-Path $Root 'release\stage'
  $PortableStage=Join-Path $Stage 'RAT VISION'
  if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
  New-Item -ItemType Directory -Force $PortableStage | Out-Null
  Copy-Item -Path (Join-Path $Dist '*') -Destination $PortableStage -Recurse -Force
  Set-Content -Path (Join-Path $PortableStage 'portable.flag') -Value 'RAT VISION portable edition' -Encoding ascii
  Copy-Item -Path (Join-Path $Root 'LICENSE') -Destination $PortableStage -Force
  Copy-Item -Path (Join-Path $Root 'LICENSES.md') -Destination $PortableStage -Force
  Copy-Item -Path (Join-Path $Root 'third_party') -Destination $PortableStage -Recurse -Force

  $Portable=Join-Path $Out "RAT-VISION-Portable-v$Version.zip"
  Compress-Archive -Path $PortableStage -DestinationPath $Portable -CompressionLevel Optimal

  if (-not $Iscc) {
    $Candidates=@(
      "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
      "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
      "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $Iscc=$Candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
  }
  if (-not $Iscc) { throw 'Inno Setup 6 (ISCC.exe) not found. Install it or pass -Iscc.' }
  & $Iscc "/DMyAppVersion=$Version" (Join-Path $Root 'installer\rat-vision.iss')
  if ($LASTEXITCODE -ne 0) { throw 'Inno Setup build failed' }

  $Installer=Join-Path $Out "RAT-VISION-Setup-v$Version.exe"
  if (-not (Test-Path $Installer)) { throw "Installer was not created: $Installer" }
  & $BuildPython -c "from pathlib import Path; from release.generate_manifest import write_release_metadata; write_release_metadata('$Version', Path(r'$Installer'), Path(r'$Portable'), Path(r'$Out'))"
  if ($LASTEXITCODE -ne 0) { throw 'Release manifest generation failed' }
  & $BuildPython -c "import json; from pathlib import Path; from release.validate_release import validate_release_contract; m=json.loads(Path(r'$Out\update-manifest.json').read_text()); validate_release_contract('v$Version','$Version',m)"
  if ($LASTEXITCODE -ne 0) { throw 'Release contract validation failed' }
  Write-Host "[OK] Release assets: $Out" -ForegroundColor Green
}
finally {
  if ($null -ne $OriginalBuildConfig) {
    [IO.File]::WriteAllText($BuildConfigPath, $OriginalBuildConfig, $Utf8NoBom)
  }
}
