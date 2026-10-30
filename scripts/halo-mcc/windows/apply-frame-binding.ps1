# Selects the Steam Frame controller layout (mcc_frame_binding.json, 1:1 with the flat Xbox layout) for Halo MCC VR
# on a Windows PC streaming to the Frame, through steamvr.vrsettings (steam.app.976730 ->
# frame_controller_CurrentURL_openxr and the _250820_ variant).
#
#   powershell -ExecutionPolicy Bypass -File apply-frame-binding.ps1 [-StopSteamVR]
#
# Do not overwrite SteamVR's generated steam.app.976730_oculus_touch_N_binding.json and make it read-only (the
# trick used on the Frame itself): SteamVR on Windows rewrites that file on every launch, a read-only one fails with
# "Unable to write OpenXR binding" and "Loading 0 bindings", and every button goes dead. This script also unlocks
# any such file an older version of it locked.
# SteamVR rewrites steamvr.vrsettings while it runs, so it has to be closed (-StopSteamVR closes it). Start it again
# afterwards; the next launch of the mod uses the Frame layout.
param([switch]$StopSteamVR)
$ErrorActionPreference = 'Stop'

$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam').SteamPath -replace '/', '\'
$src = Join-Path $PSScriptRoot 'mcc_frame_binding.json'
if (-not (Test-Path $src)) { throw "missing $src" }

Get-ChildItem (Join-Path $steam 'config\openxr') -Filter 'steam.app.976730_*_binding.json' -ErrorAction SilentlyContinue |
    Where-Object IsReadOnly | ForEach-Object { $_.IsReadOnly = $false; "unlocked $($_.Name)" }

$vr = Get-Process vrserver, vrmonitor, vrcompositor, vrdashboard, vrwebhelper, vrstartup -ErrorAction SilentlyContinue
if ($vr) {
    if (-not $StopSteamVR) { throw 'SteamVR is running and would overwrite the change. Close it or pass -StopSteamVR.' }
    $vr | Stop-Process -Force
    Start-Sleep 3
}

$vrs = Join-Path $steam 'config\steamvr.vrsettings'
Copy-Item $vrs "$vrs.bak-halo-frame" -Force
$s = Get-Content $vrs -Raw | ConvertFrom-Json
$app = 'steam.app.976730'
if (-not $s.$app) { $s | Add-Member -NotePropertyName $app -NotePropertyValue ([pscustomobject]@{}) }
$file = (Resolve-Path $src).Path
$url = 'file:///' + ((($file -replace '\\', '/') -replace ' ', '%20') -replace '\(', '%28' -replace '\)', '%29')
foreach ($key in 'frame_controller_CurrentURL_openxr', 'frame_controller_250820_CurrentURL_openxr') {
    $s.$app | Add-Member -NotePropertyName $key -NotePropertyValue $url -Force
}
[IO.File]::WriteAllText($vrs, ($s | ConvertTo-Json -Depth 32), (New-Object System.Text.UTF8Encoding($false)))
"Selected $url for $app (backup: $vrs.bak-halo-frame). Start SteamVR again."
