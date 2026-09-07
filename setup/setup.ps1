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

