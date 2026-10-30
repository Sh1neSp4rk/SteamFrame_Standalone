# Starts the KHARVOX launcher from wherever this drive is mounted.
#
# Expected layout on the drive (any drive letter):
#   <drive>\KHARVOX\                              this folder
#   <drive>\SteamLibrary\steamapps\common\DOOM\   DOOM (2016)
#
# Before opening the launcher, this points the launcher's saved DOOM path at
# the DOOM folder on the same drive, so a changed drive letter just works.
# Steam runs this through the "DOOM (KHARVOX VR)" library entry; see
# Add-KharvoxSteamShortcut.ps1.

$ErrorActionPreference = 'Stop'

$kharvoxDir = $PSScriptRoot
$launcher   = Join-Path $kharvoxDir 'KharvoxLauncher.exe'
$doomDir    = Join-Path (Split-Path $kharvoxDir -Parent) 'SteamLibrary\steamapps\common\DOOM'
$settings   = Join-Path $env:LOCALAPPDATA 'KHARVOX\settings.json'

# DOOM is not beside this folder (e.g. KHARVOX on C: with DOOM in Steam's own
# library): look it up in Steam's library list instead.
if (-not (Test-Path -LiteralPath (Join-Path $doomDir 'DOOMx64vk.exe'))) {
    try {
        $steamPath = (Get-ItemProperty 'HKCU:\Software\Valve\Steam').SteamPath
        $vdf = Join-Path $steamPath 'steamapps\libraryfolders.vdf'
        foreach ($m in [regex]::Matches([IO.File]::ReadAllText($vdf), '"path"\s+"([^"]+)"')) {
            $candidate = Join-Path ($m.Groups[1].Value.Replace('\\', '\')) 'steamapps\common\DOOM'
            if (Test-Path -LiteralPath (Join-Path $candidate 'DOOMx64vk.exe')) { $doomDir = $candidate; break }
        }
    } catch { }
}

function Show-Error([string]$message) {
    Add-Type -AssemblyName System.Windows.Forms
    [void][System.Windows.Forms.MessageBox]::Show($message, 'KHARVOX', 'OK', 'Error')
}

if (-not (Test-Path -LiteralPath $launcher)) {
    Show-Error "KharvoxLauncher.exe was not found in $kharvoxDir."
    exit 1
}

# Update the saved DOOM path. If the launcher has never run on this PC there is
# no settings file yet; the launcher then finds DOOM through Steam's library list.
if ((Test-Path -LiteralPath (Join-Path $doomDir 'DOOMx64vk.exe')) -and (Test-Path -LiteralPath $settings)) {
    try {
        $text = [IO.File]::ReadAllText($settings)
        $jsonPath = $doomDir.Replace('\', '\\')
        $pattern = '"GamePath":"(?:[^"\\]|\\.)*"'
        $evaluator = [Text.RegularExpressions.MatchEvaluator] { param($m) '"GamePath":"' + $jsonPath + '"' }
        $updated = [regex]::Replace($text, $pattern, $evaluator)
        if ($updated -ne $text) {
            [IO.File]::WriteAllText($settings, $updated, (New-Object Text.UTF8Encoding $false))
        }
    } catch {
        # Never block the launch; the launcher's Browse button still works.
    }
}

# Wait for the launcher so Steam shows the game as running until it closes.
Start-Process -FilePath $launcher -WorkingDirectory $kharvoxDir -Wait
