# Installs Halo MCC VR on a Windows PC for streaming to a Steam Frame, with the Frame's controls.
#
#   powershell -ExecutionPolicy Bypass -File install-pc.ps1 -ModFiles <folder> -Launcher <HaloMCCVRLauncher.exe> -Layer <folder>
#
#   -ModFiles  the mod's runtime files: the "ModFiles" folder from cmake --install ... --component dist
#              (HaloMCCVR.dll, assets\, licenses\, nvngx_dlss.dll, ...) or the same files copied from another PC
#   -Launcher  HaloMCCVRLauncher.exe from the same build
#   -Layer     folder holding frame_quadfix.dll and frame_quadfix.json (tools/frame-quadfix/halo/out)
#   -McCRoot   optional; found from Steam's library folders when omitted
#
# What it does: copies everything into <MCC>\Halo_MCC_VR, writes a minimal halomccvr.cfg if there is none
# (vr_action_mapping = 0 so the buttons stay 1:1 with flat, y_b_start_chord = 0 so Y+B is not
# also a pause chord), copies the Frame controller layout and the
# apply-frame-binding.ps1 helper next to it, and writes register-frame-layer.reg / unregister-frame-layer.reg with
# this machine's path. Registering the layer needs administrator rights, so that one step is yours: double-click
# register-frame-layer.reg. Nothing outside the MCC folder is changed by this script.
param(
    [Parameter(Mandatory = $true)][string]$ModFiles,
    [Parameter(Mandatory = $true)][string]$Launcher,
    [Parameter(Mandatory = $true)][string]$Layer,
    [string]$McCRoot
)
$ErrorActionPreference = 'Stop'

if (-not $McCRoot) {
    $steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
    if (-not $steam) { $steam = 'C:\Program Files (x86)\Steam' }
    $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
    $libs = @($steam) + @(Select-String -Path $vdf -Pattern '"path"\s+"([^"]+)"' | ForEach-Object { $_.Matches[0].Groups[1].Value -replace '\\\\', '\' })
    foreach ($l in $libs) {
        $c = Join-Path $l 'steamapps\common\Halo The Master Chief Collection'
        if (Test-Path (Join-Path $c 'MCC\Binaries\Win64\MCC-Win64-Shipping.exe')) { $McCRoot = $c; break }
    }
    if (-not $McCRoot) { throw 'Halo MCC not found in any Steam library; pass -McCRoot.' }
}
if (Get-Process MCC-Win64-Shipping -ErrorAction SilentlyContinue) { throw 'Close MCC first.' }
$dst = Join-Path $McCRoot 'Halo_MCC_VR'
New-Item -ItemType Directory -Force $dst | Out-Null
"MCC: $McCRoot"

Copy-Item -Recurse -Force (Join-Path $ModFiles '*') $dst
Copy-Item -Force $Launcher $dst
Copy-Item -Force (Join-Path $Layer 'frame_quadfix.dll'), (Join-Path $Layer 'frame_quadfix.json') $dst
Copy-Item -Force (Join-Path $PSScriptRoot 'apply-frame-binding.ps1') $dst
Copy-Item -Force (Join-Path $PSScriptRoot '..\mcc_frame_binding.json') $dst

$cfg = Join-Path $dst 'halomccvr.cfg'
if (-not (Test-Path $cfg)) {
    "config_version = 6`r`n# Steam Frame: plain 1:1 gamepad buttons, matching the flat layout`r`nvr_action_mapping = 0`r`ny_b_start_chord = 0`r`n" |
        Set-Content -Path $cfg -Encoding ascii -NoNewline
    'wrote a minimal halomccvr.cfg (the mod fills in every other setting with its defaults)'
} else {
    $text = Get-Content $cfg -Raw
    if ($text -match '(?m)^vr_action_mapping\s*=') { $text = $text -replace '(?m)^vr_action_mapping\s*=.*$', 'vr_action_mapping = 0' }
    else { $text = $text.TrimEnd() + "`r`nvr_action_mapping = 0`r`n" }
    if ($text -match '(?m)^y_b_start_chord\s*=') { $text = $text -replace '(?m)^y_b_start_chord\s*=.*$', 'y_b_start_chord = 0' }
    else { $text = $text.TrimEnd() + "`r`ny_b_start_chord = 0`r`n" }
    Set-Content -Path $cfg -Value $text -Encoding ascii -NoNewline
    'kept the existing halomccvr.cfg, set vr_action_mapping = 0 and y_b_start_chord = 0'
}

$json = (Join-Path $dst 'frame_quadfix.json').Replace('\', '\\')
$key = '[HKEY_LOCAL_MACHINE\SOFTWARE\Khronos\OpenXR\1\ApiLayers\Implicit]'
@"
Windows Registry Editor Version 5.00

; Registers the frame_quadfix OpenXR layer (Steam Frame helpers for Halo MCC VR). HKLM is required because the
; MCCVR launcher runs as administrator and the OpenXR loader ignores per-user layers in elevated processes.
; The layer does nothing in processes other than MCC-Win64-Shipping.exe.

$key
"$json"=dword:00000000
"@ | Set-Content -Path (Join-Path $dst 'register-frame-layer.reg') -Encoding Unicode
@"
Windows Registry Editor Version 5.00

$key
"$json"=-
"@ | Set-Content -Path (Join-Path $dst 'unregister-frame-layer.reg') -Encoding Unicode

''
'Installed. Next:'
"  1. Double-click $dst\register-frame-layer.reg (admin prompt) once."
"  2. With SteamVR closed: powershell -ExecutionPolicy Bypass -File `"$dst\apply-frame-binding.ps1`" -StopSteamVR"
'     (selects the Frame layout for Halo in steamvr.vrsettings).'
'  3. Start SteamVR streaming to the Frame, run HaloMCCVRLauncher.exe, choose MCC and Launch.'
