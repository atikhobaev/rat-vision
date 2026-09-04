$ErrorActionPreference = 'Stop'
$ProgressPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location $Root
$VersionText = Get-Content (Join-Path $Root 'ratvision\version.py') -Raw
if ($VersionText -notmatch '__version__\s*=\s*"([^"]+)"') { throw 'Could not read RAT VISION version' }
$AppVersion = $Matches[1]

$Log = Join-Path $Root 'build.log'
$RuntimeDir = Join-Path $Root '.runtime'
$DownloadsDir = Join-Path $RuntimeDir 'downloads'
$PythonVersion = '3.13.15'
$PythonInstallerName = "python-$PythonVersion-amd64.exe"
$PythonInstaller = Join-Path $DownloadsDir $PythonInstallerName
$PythonInstallerUrl = "https://www.python.org/ftp/python/$PythonVersion/$PythonInstallerName"
$PythonInstallerSha256 = 'edec09c4853aeae9ac36efb8c9f95b6b8e2fee65eee56d9767a8b7c69c574403'
$PythonDir = Join-Path $RuntimeDir "cpython-$PythonVersion"
$PrivatePython = Join-Path $PythonDir 'python.exe'
$VenvDir = Join-Path $Root '.build-venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$PytestTempDir = Join-Path $Root '.test-tmp-build'
$TclLibrary = Join-Path $PythonDir 'tcl\tcl8.6'
$TkLibrary = Join-Path $PythonDir 'tcl\tk8.6'

New-Item -ItemType Directory -Force -Path $RuntimeDir, $DownloadsDir | Out-Null
if (Test-Path $Log) { Remove-Item $Log -Force }

Start-Transcript -Path $Log -Force | Out-Null

function Write-Step([int]$Number, [int]$Total, [string]$Message) {
    Write-Host "[$Number/$Total] $Message" -ForegroundColor Cyan
}

function Assert-LastExitCode([string]$Action) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Action failed with exit code $LASTEXITCODE"
    }
}

function Test-PrivatePythonRuntime {
    if (-not (Test-Path $PrivatePython)) {
        return $false
    }
    & $PrivatePython -c "import struct,sys,tkinter as tk; r=tk.Tk(); r.withdraw(); r.update_idletasks(); print('Python', sys.version); print('Pointer bits:', struct.calcsize('P')*8); print('Tk', tk.TkVersion); r.destroy(); raise SystemExit(0 if sys.version_info[:2] == (3,13) and struct.calcsize('P') == 8 else 1)"
    return ($LASTEXITCODE -eq 0)
}

try {
    Write-Host "RAT VISION v$AppVersion portable build bootstrap" -ForegroundColor White
    Write-Host "Project: $Root"
    Write-Host "Log:     $Log"
    Write-Host ''

    Write-Step 1 6 'Preparing private build directories...'
    $env:PYTHONUTF8 = '1'
    # Python 3.13 on Windows can intermittently resolve Tcl/Tk through the venv incorrectly.
    # Pin both libraries to the private base interpreter for every child process.
    $env:TCL_LIBRARY = $TclLibrary
    $env:TK_LIBRARY = $TkLibrary

    Write-Step 2 6 'Preparing private CPython 3.13 x64 with Tcl/Tk...'
    $PythonReady = Test-PrivatePythonRuntime
    if (-not $PythonReady) {
        if (Test-Path $PythonDir) {
            Write-Host 'Existing private Python is incomplete; replacing it...'
            Remove-Item $PythonDir -Recurse -Force
        }

        $NeedDownload = $true
        if (Test-Path $PythonInstaller) {
            $ExistingHash = (Get-FileHash -Path $PythonInstaller -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($ExistingHash -eq $PythonInstallerSha256) {
                $NeedDownload = $false
                Write-Host "Using cached official CPython installer: $PythonInstaller"
            } else {
                Write-Host 'Cached Python installer hash is wrong; downloading a clean copy...'
                Remove-Item $PythonInstaller -Force
            }
        }

        if ($NeedDownload) {
            Write-Host "Downloading official CPython $PythonVersion x64 installer from python.org..."
            Invoke-WebRequest -Uri $PythonInstallerUrl -OutFile $PythonInstaller -UseBasicParsing
        }

        $DownloadedHash = (Get-FileHash -Path $PythonInstaller -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($DownloadedHash -ne $PythonInstallerSha256) {
            throw "CPython installer SHA256 mismatch. Expected $PythonInstallerSha256 but got $DownloadedHash"
        }

        $InstallerArgs = @(
            '/quiet',
            'InstallAllUsers=0',
            "TargetDir=`"$PythonDir`"",
            'Include_launcher=0',
            'InstallLauncherAllUsers=0',
            'PrependPath=0',
            'Include_doc=0',
            'Include_debug=0',
            'Include_test=0',
            'Include_pip=1',
            'Include_tcltk=1'
        )
        $InstallProcess = Start-Process -FilePath $PythonInstaller -ArgumentList $InstallerArgs -Wait -PassThru
        if ($InstallProcess.ExitCode -ne 0) {
            throw "Official CPython installer failed with exit code $($InstallProcess.ExitCode)"
        }

        # The CPython bundle enters maintenance mode when this exact version is
        # already registered for the user. In that case it exits successfully
        # but keeps the existing install location and ignores our TargetDir.
        # Seed the project-local runtime from that verified official install.
        if (-not (Test-Path $PrivatePython)) {
            $PythonRegistryKey = "HKCU:\Software\Python\PythonCore\3.13\InstallPath"
            $RegisteredPython = if (Test-Path $PythonRegistryKey) {
                (Get-Item -LiteralPath $PythonRegistryKey).GetValue('')
            } else { $null }
            $RegisteredPythonExe = if ($RegisteredPython) { Join-Path $RegisteredPython 'python.exe' } else { $null }
            if ($RegisteredPythonExe -and (Test-Path $RegisteredPythonExe)) {
                $RegisteredTcl = Join-Path $RegisteredPython 'tcl\tcl8.6'
                $RegisteredTk = Join-Path $RegisteredPython 'tcl\tk8.6'
                $env:TCL_LIBRARY = $RegisteredTcl
                $env:TK_LIBRARY = $RegisteredTk
                & $RegisteredPythonExe -c "import struct,sys,tkinter as tk; r=tk.Tk(); r.withdraw(); r.update_idletasks(); r.destroy(); raise SystemExit(0 if sys.version_info[:3] == (3,13,15) and struct.calcsize('P') == 8 else 1)"
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Reusing registered official CPython runtime: $RegisteredPython"
                    New-Item -ItemType Directory -Force $PythonDir | Out-Null
                    Copy-Item -Path (Join-Path $RegisteredPython '*') -Destination $PythonDir -Recurse -Force
                    $env:TCL_LIBRARY = $TclLibrary
                    $env:TK_LIBRARY = $TkLibrary
                }
            }
        }

        if (-not (Test-PrivatePythonRuntime)) {
            throw 'Private CPython installed, but Tkinter/Tcl-Tk validation failed'
        }
    } else {
        Write-Host "Using existing private CPython with working Tkinter: $PrivatePython"
    }

    $TclInit = Join-Path $TclLibrary 'init.tcl'
    $TkInit = Join-Path $TkLibrary 'tk.tcl'
    if (-not (Test-Path $TclInit)) { throw "Tcl init.tcl was not found at $TclInit" }
    if (-not (Test-Path $TkInit)) { throw "Tk tk.tcl was not found at $TkInit" }

    Write-Step 3 6 'Creating isolated build environment...'
    & $PrivatePython -m venv --clear $VenvDir
    Assert-LastExitCode 'Virtual environment creation'
    if (-not (Test-Path $VenvPython)) {
        throw "Virtual environment Python was not found at $VenvPython"
    }

    & $VenvPython -c "import struct,sys,tkinter as tk; r=tk.Tk(); r.withdraw(); r.update_idletasks(); print('Python', sys.version); print('Pointer bits:', struct.calcsize('P')*8); print('Tk', tk.TkVersion); r.destroy(); raise SystemExit(0 if sys.version_info[:2] == (3,13) and struct.calcsize('P') == 8 else 1)"
    Assert-LastExitCode 'Python 3.13 x64 + Tkinter verification'

    Write-Step 4 6 'Installing RAT VISION dependencies and build tools...'
    & $VenvPython -m pip install --disable-pip-version-check -e '.[dev]' pyinstaller
    Assert-LastExitCode 'Dependency installation'

    Write-Step 5 6 'Running tests...'
    # Avoid stale or inaccessible user-level pytest temp directories on Windows.
    if (Test-Path $PytestTempDir) { Remove-Item $PytestTempDir -Recurse -Force }
    # Keep non-GUI tests together, but run every Tk test in a fresh Python process.
    # This avoids a known Python 3.13/Windows Tcl/Tk failure after repeated Tk() teardown/recreate cycles.
    & $VenvPython -m pytest -q --basetemp=$PytestTempDir --ignore=tests/ui --ignore=tests/test_app_smoke.py
    Assert-LastExitCode 'Core test suite'

    $GuiNodeIds = & $VenvPython -m pytest --collect-only -q --basetemp=$PytestTempDir tests/ui tests/test_app_smoke.py
    Assert-LastExitCode 'GUI test collection'
    $GuiNodeIds = @($GuiNodeIds | Where-Object { $_ -match '::' })
    if ($GuiNodeIds.Count -eq 0) { throw 'No GUI tests were collected' }
    foreach ($NodeId in $GuiNodeIds) {
        Write-Host "GUI test: $NodeId"
        & $VenvPython -m pytest -q --basetemp=$PytestTempDir $NodeId
        Assert-LastExitCode "GUI test $NodeId"
    }

    Write-Step 6 6 'Building portable executable...'
    $VersionInfo = Join-Path $Root 'release\version_info.txt'
    & $VenvPython (Join-Path $Root 'release\generate_version_info.py') --version $AppVersion --output $VersionInfo
    Assert-LastExitCode 'Windows version metadata generation'
    & $VenvPython -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --name 'RAT VISION' `
        --icon 'ratvision\resources\brand\ratvision.ico' `
        --version-file $VersionInfo `
        --paths '.' `
        --add-data 'ratvision\resources;ratvision\resources' `
        'ratvision\__main__.py'
    Assert-LastExitCode 'PyInstaller packaging'

    $Exe = Join-Path $Root 'dist\RAT VISION\RAT VISION.exe'
    if (-not (Test-Path $Exe)) {
        throw "Build reported success but executable was not found at $Exe"
    }

    Write-Host ''
    Write-Host '[OK] Portable build is ready.' -ForegroundColor Green
    Write-Host "Executable: $Exe"
    Write-Host 'The .runtime and .build-venv folders are build-only and can be deleted after packaging.'
    exit 0
}
catch {
    Write-Host ''
    Write-Host '[ERROR] Build stopped.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ''
    Write-Host "Full log: $Log" -ForegroundColor Yellow
    exit 1
}
finally {
    try { Stop-Transcript | Out-Null } catch { }
}
