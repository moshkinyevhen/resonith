param(
    [string]$Destination
)

$ErrorActionPreference = 'Stop'

$releaseUrl = 'https://archive.mozilla.org/pub/opus/win32/opus-tools-0.2-opus-1.3.zip'
$releaseSha256 = 'a1ae3c806adee9b008348166251f938dd7774ba6987d392187202b11d1152e90'
$userProfilePath = [Environment]::GetFolderPath('UserProfile')
if (-not $Destination) {
    $Destination = Join-Path $userProfilePath '.local\tools\resonith-opus-tools-0.2-opus-1.3'
}

$resolvedDestination = [IO.Path]::GetFullPath($Destination)
$allowedRoot = [IO.Path]::GetFullPath((Join-Path $userProfilePath '.local\tools'))
if (-not $resolvedDestination.StartsWith($allowedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Destination must remain inside $allowedRoot"
}

$encoder = Join-Path $resolvedDestination 'opusenc.exe'
$decoder = Join-Path $resolvedDestination 'opusdec.exe'
if ((Test-Path -LiteralPath $encoder) -and (Test-Path -LiteralPath $decoder)) {
    Write-Output $resolvedDestination
    exit 0
}
if ((Test-Path -LiteralPath $resolvedDestination) -and
    (Get-ChildItem -LiteralPath $resolvedDestination -Force | Select-Object -First 1)) {
    throw "Destination exists and is not an installed opus-tools directory: $resolvedDestination"
}

$stateDirectory = Join-Path $userProfilePath '.local\state\resonith'
New-Item -ItemType Directory -Force -Path $stateDirectory | Out-Null
$archivePath = Join-Path $stateDirectory 'opus-tools-0.2-opus-1.3.zip'
Invoke-WebRequest -Uri $releaseUrl -OutFile $archivePath
$actualSha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualSha256 -ne $releaseSha256) {
    throw "opus-tools archive hash mismatch: $actualSha256"
}

New-Item -ItemType Directory -Force -Path $resolvedDestination | Out-Null
Expand-Archive -LiteralPath $archivePath -DestinationPath $resolvedDestination -Force
if (-not (Test-Path -LiteralPath $encoder) -or -not (Test-Path -LiteralPath $decoder)) {
    throw 'opus-tools archive did not contain opusenc.exe and opusdec.exe'
}
Write-Output $resolvedDestination
