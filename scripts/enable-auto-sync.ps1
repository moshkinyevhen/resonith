$ErrorActionPreference = "Stop"

function Resolve-GitExecutable {
    $command = Get-Command git -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $toolsRoot = Join-Path $env:USERPROFILE ".local\tools"
    $candidate = Get-ChildItem -LiteralPath $toolsRoot -Directory -Filter "git-*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName "cmd\git.exe" } |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1

    if ($null -eq $candidate) {
        throw "Git was not found. Install Git before enabling synchronization."
    }

    return $candidate
}

$git = Resolve-GitExecutable
$repositoryRoot = Split-Path -Parent $PSScriptRoot

& $git -C $repositoryRoot config core.hooksPath .githooks
if ($LASTEXITCODE -ne 0) {
    throw "Failed to configure Git hooks."
}

Write-Output "Automatic post-commit push is enabled for Resonith."

