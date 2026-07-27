$ErrorActionPreference = "Stop"

function Resolve-GitExecutable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepositoryRoot
    )

    $command = Get-Command git -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $projectToolsRoot = Join-Path $RepositoryRoot "artifacts\tools"
    $candidate = Get-ChildItem -LiteralPath $projectToolsRoot -Directory -Filter "mingit-*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName "cmd\git.exe" } |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1

    if ($null -ne $candidate) {
        return $candidate
    }

    $toolsRoot = Join-Path $env:USERPROFILE ".local\tools"
    $candidate = Get-ChildItem -LiteralPath $toolsRoot -Directory -Filter "git-*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName "cmd\git.exe" } |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1

    if ($null -eq $candidate) {
        throw "Git was not found."
    }

    return $candidate
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$git = Resolve-GitExecutable -RepositoryRoot $repositoryRoot
$branch = (& $git -C $repositoryRoot branch --show-current).Trim()

if ([string]::IsNullOrWhiteSpace($branch)) {
    throw "The repository is not on a named branch."
}

& $git -C $repositoryRoot fetch origin
if ($LASTEXITCODE -ne 0) {
    throw "Fetch failed."
}

& $git -C $repositoryRoot pull --rebase --autostash origin $branch
if ($LASTEXITCODE -ne 0) {
    throw "Pull/rebase failed."
}

& $git -C $repositoryRoot push origin $branch
if ($LASTEXITCODE -ne 0) {
    throw "Push failed."
}
