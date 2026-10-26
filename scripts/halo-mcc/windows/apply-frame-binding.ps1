# Puts the Steam Frame controller layout (mcc_frame_binding.json, 1:1 with the flat Xbox layout) into the
# OpenXR binding file SteamVR generated for Halo MCC (steam.app.976730_oculus_touch_N_binding.json) and makes it
# read-only, so SteamVR keeps loading it as Halo's default. SteamVR only creates that file the first time the mod
# starts in VR (and again whenever the mod's action list changes), so:
#   1. run this with -Watch, then launch Halo MCC VR once (that launch still uses SteamVR's automatic layout);
#   2. from the next launch on, the Frame layout is used.
# Without -Watch it updates the files that already exist and exits.
param([switch]$Watch, [int]$TimeoutMinutes = 15)

$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
if (-not $steam) { $steam = 'C:\Program Files (x86)\Steam' }
$dir = Join-Path $steam 'config\openxr'
$src = Join-Path $PSScriptRoot 'mcc_frame_binding.json'
if (-not (Test-Path $src)) { throw "missing $src" }
$wanted = [IO.File]::ReadAllText($src)

function Apply-Binding {
    $files = @(Get-ChildItem $dir -Filter 'steam.app.976730_oculus_touch_*_binding.json' -ErrorAction SilentlyContinue)
    foreach ($f in $files) {
        if ([IO.File]::ReadAllText($f.FullName) -eq $wanted -and $f.IsReadOnly) { "already Frame layout: $($f.Name)"; continue }
        $f.IsReadOnly = $false
        [IO.File]::WriteAllText($f.FullName, $wanted)
        $f.IsReadOnly = $true
        "Frame layout written and locked: $($f.Name)"
    }
    return $files.Count
}

if (-not $Watch) { if ((Apply-Binding) -eq 0) { "No Halo binding file yet in $dir - run with -Watch and launch the VR mod once." }; return }

$start = Get-Date
"Waiting for SteamVR to write Halo's binding file in $dir (launch Halo MCC VR now)..."
while ((Get-Date) - $start -lt [TimeSpan]::FromMinutes($TimeoutMinutes)) {
    $fresh = Get-ChildItem $dir -Filter 'steam.app.976730_oculus_touch_*_binding.json' -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -gt $start }
    if ($fresh) { Start-Sleep -Seconds 2; Apply-Binding | Out-Host; "Done. Restart Halo MCC VR to use the Frame layout."; return }
    Start-Sleep -Seconds 1
}
"Timed out: no new binding file appeared."
