param(
    [ValidateSet("python-fastapi", "javascript-express", "typescript-express", "javascript-nextjs", "typescript-nextjs", "java-spring-boot", "c")]
    [string]$Option,
    [switch]$WinGetOnly,
    [switch]$Help
)

if ($Help) {
    Write-Host "Run .\setup\setup.ps1 to choose a language from the menu."
    exit 0
}

if ($args.Count -gt 0) {
    Write-Host "Usage: .\setup\setup.ps1 [-Option folder]"
    exit 2
}

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Tools = Join-Path $Root ".tools"
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if ($WinGetOnly) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "Installing Windows Package Manager..."
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser | Out-Null
        Install-Module -Name Microsoft.WinGet.Client -Repository PSGallery -Force -Scope CurrentUser
        Import-Module Microsoft.WinGet.Client
        Repair-WinGetPackageManager -Force -Latest
    }
    exit 0
}

$Python = $null
$Probe = "import sys; print(sys.executable) if (3, 9) <= sys.version_info[:2] < (3, 14) else sys.exit(1)"

if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($Version in @("-3.12", "-3.13", "-3.11", "-3.10", "-3.9")) {
        try {
            $Candidate = & py $Version -c $Probe 2>$null
        } catch {
            continue
        }
        if ($LASTEXITCODE -eq 0 -and $Candidate) {
            $Python = "$Candidate".Trim()
            break
        }
    }
}

if (-not $Python) {
    foreach ($Name in @("python.exe", "python3.exe")) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($Command -and $Command.Source -notlike "*WindowsApps*") {
            try {
                $Candidate = & $Command.Source -c $Probe 2>$null
            } catch {
                continue
            }
            if ($LASTEXITCODE -eq 0 -and $Candidate) {
                $Python = "$Candidate".Trim()
                break
            }
        }
    }
}

if (-not $Python) {
    $env:UV_INSTALL_DIR = Join-Path $Tools "uv"
    $env:UV_NO_MODIFY_PATH = "1"
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $Tools "python"
    $env:UV_PYTHON_BIN_DIR = Join-Path $Tools "bin"
    $Uv = Join-Path $env:UV_INSTALL_DIR "uv.exe"

    if (-not (Test-Path $Uv)) {
        Write-Host "Installing the Python bootstrap tool..."
        $Installer = Join-Path $Tools "install-uv.ps1"
        Invoke-WebRequest -UseBasicParsing -Uri "https://astral.sh/uv/install.ps1" -OutFile $Installer
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Installer
        if ($LASTEXITCODE -ne 0) { throw "Python bootstrap installation failed." }
    }

    & $Uv python install 3.12
    if ($LASTEXITCODE -ne 0) { throw "Python installation failed." }

    $Python = (& $Uv python find --managed-python 3.12).Trim()
    if ($LASTEXITCODE -ne 0) { throw "The installed Python could not be found." }
}

$SetupArguments = @((Join-Path $Root "setup.py"))

if ($Option) {
    $SetupArguments += $Option.ToLowerInvariant()
}

& $Python @SetupArguments
if ($LASTEXITCODE -ne 0) { throw "Setup did not finish. Read the error above and rerun." }

. (Join-Path $Tools "activate.ps1")

$SelectedFolder = (Get-Content -Raw (Join-Path $Tools "selected-folder.txt")).Trim()
Set-Location -LiteralPath (Join-Path (Split-Path -Parent $Root) $SelectedFolder)
