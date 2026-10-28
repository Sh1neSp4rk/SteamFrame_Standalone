# Gives RE4VR (Resident Evil 4, 2023) the flat Xbox layout 1:1 on Steam Frame controllers, on a
# Windows PC streaming to the Frame.
#
#   powershell -ExecutionPolicy Bypass -File install-pc.ps1 [-StopSteamVR] [-SkipVrSettings]
#
# Run it after RE4VR is installed (OpenVR, Steam) and the game has been started once in VR, so that
# REFramework has written bindings_frame.json into the game folder. RE4 must be closed.
#
# It copies re4_frame_xbox.lua into reframework\autorun, writes _framepad\re4_frame_binding.json
# (every RE4VR Frame binding, plus the bumpers, B, right stick click and View on REFramework's spare
# Block/Heal/MiniMap actions) and selects that binding for steam.app.2050650 in steamvr.vrsettings.
# SteamVR rewrites that file while it runs, so it must be closed (-StopSteamVR closes it).
# -SkipVrSettings writes the files only.
param(
    [switch]$StopSteamVR,
    [switch]$SkipVrSettings
)
$ErrorActionPreference = 'Stop'

$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam').SteamPath -replace '/', '\'
$libs = Select-String -Path "$steam\steamapps\libraryfolders.vdf" -Pattern '"path"\s+"([^"]+)"' |
    ForEach-Object { $_.Matches[0].Groups[1].Value -replace '\\\\', '\' }
$game = $null
foreach ($lib in $libs) {
    if (Test-Path "$lib\steamapps\appmanifest_2050650.acf") {
        $dir = (Select-String -Path "$lib\steamapps\appmanifest_2050650.acf" -Pattern '"installdir"\s+"([^"]+)"').Matches[0].Groups[1].Value
        $game = "$lib\steamapps\common\$dir"
    }
}
if (-not $game) { throw 'Resident Evil 4 (app 2050650) not found in any Steam library.' }
if (Get-Process re4 -ErrorAction SilentlyContinue) { throw 'Close Resident Evil 4 first.' }
if (-not (Test-Path "$game\reframework\data\re4_vr")) { throw "RE4VR is not installed in $game." }
$modBinding = "$game\bindings_frame.json"
if (-not (Test-Path $modBinding)) { throw 'bindings_frame.json is missing: start RE4 once in VR with RE4VR, then run this again.' }
Write-Host "RE4: $game"

$utf8 = New-Object System.Text.UTF8Encoding($false)

# 1. The Lua script that writes the physical buttons into the engine gamepad.
New-Item -ItemType Directory -Force "$game\reframework\autorun", "$game\_framepad" | Out-Null
Copy-Item "$PSScriptRoot\..\re4_frame_xbox.lua" "$game\reframework\autorun\re4_frame_xbox.lua" -Force

# 2. The binding: RE4VR's own Frame layout (its VR menu reads those actions), plus raw buttons.
$b = Get-Content $modBinding -Raw | ConvertFrom-Json
$sources = [System.Collections.ArrayList]@($b.bindings.'/actions/default'.sources)
foreach ($pair in @(
        @('/user/hand/right/input/b', 'heal'),
        @('/user/hand/left/input/bumper', 'block'),
        @('/user/hand/right/input/bumper', 'block'),
        @('/user/hand/right/input/thumbstick', 'minimap'),
        @('/user/hand/left/input/view', 'heal'))) {
    [void]$sources.Add([pscustomobject]@{
            inputs = [pscustomobject]@{ click = [pscustomobject]@{ output = "/actions/default/in/$($pair[1])" } }
            mode   = 'button'
            path   = $pair[0]
        })
}
$b.bindings.'/actions/default'.sources = $sources
$b.name = 'RE4VR Frame - Xbox defaults'
$b.description = 'RE4VR Frame layout plus raw B/LB/RB/R3/View actions read by re4_frame_xbox.lua'
$bindingPath = "$game\_framepad\re4_frame_binding.json"
[IO.File]::WriteAllText($bindingPath, ($b | ConvertTo-Json -Depth 32), $utf8)
Write-Host "Wrote $bindingPath ($($sources.Count) sources)"

if ($SkipVrSettings) { return }

# 3. Select the binding for RE4 (SteamVR Input app, Frame controller).
$vr = Get-Process vrserver, vrmonitor, vrcompositor, vrdashboard, vrwebhelper, vrstartup -ErrorAction SilentlyContinue
if ($vr) {
    if (-not $StopSteamVR) { throw 'SteamVR is running and would overwrite the change. Close it or pass -StopSteamVR.' }
    $vr | Stop-Process -Force
    Start-Sleep 3
}
$vrs = "$steam\config\steamvr.vrsettings"
Copy-Item $vrs "$vrs.bak-re4-frame" -Force
$s = Get-Content $vrs -Raw | ConvertFrom-Json
if (-not $s.'steam.app.2050650') { $s | Add-Member -NotePropertyName 'steam.app.2050650' -NotePropertyValue ([pscustomobject]@{}) }
$url = 'file:///' + (($bindingPath -replace '\\', '/') -replace ' ', '%20')
foreach ($key in 'frame_controller_CurrentURL_steamvrinput', 'frame_controller_250820_CurrentURL_steamvrinput') {
    $s.'steam.app.2050650' | Add-Member -NotePropertyName $key -NotePropertyValue $url -Force
}
[IO.File]::WriteAllText($vrs, ($s | ConvertTo-Json -Depth 32), $utf8)
Write-Host "Selected $url for steam.app.2050650 (backup: $vrs.bak-re4-frame). Start SteamVR again."
