# Windows counterpart of vrsettings_bind.py: selects a SteamVR controller binding for one app on the Steam Frame by
# writing steamvr.vrsettings (frame_controller_CurrentURL_<kind> and the _250820_ variant under <app>).
#
#   powershell -ExecutionPolicy Bypass -File vrsettings_bind.ps1 -App steam.app.976730 -Kind openxr -Binding <file.json> [-StopSteamVR]
#
#   -Kind  openxr (OpenXR games), steamvrinput (OpenVR games with an action manifest) or legacy
#
# SteamVR rewrites steamvr.vrsettings while it runs, so it has to be closed (-StopSteamVR closes it). Start it again
# afterwards. Prefer this over overwriting SteamVR's generated binding file in config\openxr and making it read-only:
# SteamVR on Windows rewrites that file on every launch, and a read-only one makes it load no bindings at all.
param(
    [Parameter(Mandatory = $true)][string]$App,
    [Parameter(Mandatory = $true)][ValidateSet('openxr', 'steamvrinput', 'legacy')][string]$Kind,
    [Parameter(Mandatory = $true)][string]$Binding,
    [switch]$StopSteamVR
)
$ErrorActionPreference = 'Stop'

$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam').SteamPath -replace '/', '\'
$vrs = Join-Path $steam 'config\steamvr.vrsettings'
$file = (Resolve-Path $Binding).Path

$vr = Get-Process vrserver, vrmonitor, vrcompositor, vrdashboard, vrwebhelper, vrstartup -ErrorAction SilentlyContinue
if ($vr) {
    if (-not $StopSteamVR) { throw 'SteamVR is running and would overwrite the change. Close it or pass -StopSteamVR.' }
    $vr | Stop-Process -Force
    Start-Sleep 3
}

Copy-Item $vrs "$vrs.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
$s = Get-Content $vrs -Raw | ConvertFrom-Json
if (-not $s.$App) { $s | Add-Member -NotePropertyName $App -NotePropertyValue ([pscustomobject]@{}) }
$url = 'file:///' + ((($file -replace '\\', '/') -replace ' ', '%20') -replace '\(', '%28' -replace '\)', '%29')
foreach ($key in "frame_controller_CurrentURL_$Kind", "frame_controller_250820_CurrentURL_$Kind") {
    $s.$App | Add-Member -NotePropertyName $key -NotePropertyValue $url -Force
}
[IO.File]::WriteAllText($vrs, ($s | ConvertTo-Json -Depth 32), (New-Object System.Text.UTF8Encoding($false)))
"Selected $url for $App ($Kind). Start SteamVR again."
