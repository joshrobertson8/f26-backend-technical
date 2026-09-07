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

