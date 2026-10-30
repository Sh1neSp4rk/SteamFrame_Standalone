# Launches Monster Hunter Rise in VR (REFramework + OpenVR).
# REFramework only starts VR when openvr_api.dll sits next to the exe, so this
# drops it in, launches the game through Steam, and removes it after the game
# exits so a normal Steam launch stays flat.
$ErrorActionPreference = 'Stop'
$vrDir   = $PSScriptRoot
$gameDir = Split-Path $vrDir -Parent
$dll     = Join-Path $gameDir 'openvr_api.dll'
$log     = Join-Path $vrDir 'launcher.log'
function Log($m) { "$(Get-Date -Format s) $m" | Add-Content $log }

Copy-Item (Join-Path $vrDir 'openvr_api.dll') $dll -Force
Log 'openvr_api.dll installed, launching'
Start-Process 'C:\Program Files (x86)\Steam\steam.exe' -ArgumentList '-applaunch', '1446780'

# Wait up to 2 minutes for the game to appear, then until it exits.
$deadline = (Get-Date).AddMinutes(2)
while (-not ($p = Get-Process MonsterHunterRise -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
}
if ($p) { Log "game running (pid $($p[0].Id))"; $p | Wait-Process } else { Log 'game never started' }

# The DLL stays locked a moment after exit; retry the delete.
for ($i = 0; $i -lt 15 -and (Test-Path $dll); $i++) {
    try { Remove-Item $dll -Force } catch { Start-Sleep -Seconds 2 }
}
Log "cleanup done (dll present: $(Test-Path $dll))"
