# Adds (or updates) a "DOOM (KHARVOX VR)" entry in this PC's Steam library.
#
# Run once on each PC: right-click this file > Run with PowerShell.
# Steam is closed while the shortcut file is edited, then started again.
#
# The entry contains no drive letter. It runs PowerShell, which looks for
# \KHARVOX\Start-Kharvox.ps1 on every connected drive and runs the first one
# it finds, so the external drive can be mounted on any letter.
#
# It also copies the library artwork in .\artwork into Steam's grid folder,
# so the entry shows a labeled tile instead of a blank one.
#
# Options:
#   -NoRestart   leave Steam closed afterwards
#   -ShortcutsFile <path>   edit this shortcuts.vdf instead (for testing;
#                           Steam is not touched)

param(
    [switch]$NoRestart,
    [string]$ShortcutsFile
)

$ErrorActionPreference = 'Stop'
$AppName = 'DOOM (KHARVOX VR)'

Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

public class KvNode {
    public byte Type;      // 0 map, 1 string, 2 int32, 7 uint64
    public string Key;
    public object Value;   // List<KvNode>, string, uint or byte[8]
}

public static class KvBinary {
    public static List<KvNode> Read(byte[] data) {
        int i = 0;
        return ReadMap(data, ref i);
    }

    static string ReadString(byte[] b, ref int i) {
        int start = i;
        while (b[i] != 0) i++;
        string s = Encoding.UTF8.GetString(b, start, i - start);
        i++;
        return s;
    }

    static List<KvNode> ReadMap(byte[] b, ref int i) {
        var list = new List<KvNode>();
        while (i < b.Length) {
            byte t = b[i++];
            if (t == 8) return list;
            var n = new KvNode();
            n.Type = t;
            n.Key = ReadString(b, ref i);
            switch (t) {
                case 0: n.Value = ReadMap(b, ref i); break;
                case 1: n.Value = ReadString(b, ref i); break;
                case 2: n.Value = BitConverter.ToUInt32(b, i); i += 4; break;
                case 7: var x = new byte[8]; Array.Copy(b, i, x, 0, 8); n.Value = x; i += 8; break;
                default: throw new InvalidDataException("Unknown shortcut field type " + t + " at byte " + (i - 1));
            }
            list.Add(n);
        }
        return list;
    }

    public static byte[] Write(List<KvNode> root) {
        var ms = new MemoryStream();
        WriteMap(ms, root);
        return ms.ToArray();
    }

    static void WriteString(MemoryStream ms, string s) {
        byte[] x = Encoding.UTF8.GetBytes(s);
        ms.Write(x, 0, x.Length);
        ms.WriteByte(0);
    }

    static void WriteMap(MemoryStream ms, List<KvNode> map) {
        foreach (var n in map) {
            ms.WriteByte(n.Type);
            WriteString(ms, n.Key);
            switch (n.Type) {
                case 0: WriteMap(ms, (List<KvNode>)n.Value); break;
                case 1: WriteString(ms, (string)n.Value); break;
                case 2: ms.Write(BitConverter.GetBytes((uint)n.Value), 0, 4); break;
                case 7: ms.Write((byte[])n.Value, 0, 8); break;
            }
        }
        ms.WriteByte(8);
    }

    public static uint ShortcutId(string exe, string name) {
        var table = new uint[256];
        for (uint k = 0; k < 256; k++) {
            uint c = k;
            for (int j = 0; j < 8; j++) c = (c & 1) != 0 ? 0xEDB88320u ^ (c >> 1) : c >> 1;
            table[k] = c;
        }
        uint crc = 0xFFFFFFFFu;
        foreach (byte b in Encoding.UTF8.GetBytes(exe + name)) crc = table[(crc ^ b) & 0xFF] ^ (crc >> 8);
        return (crc ^ 0xFFFFFFFFu) | 0x80000000u;
    }

    public static KvNode Str(string key, string value) { var n = new KvNode(); n.Type = 1; n.Key = key; n.Value = value; return n; }
    public static KvNode Int(string key, uint value)   { var n = new KvNode(); n.Type = 2; n.Key = key; n.Value = value; return n; }
    public static KvNode Map(string key, List<KvNode> value) { var n = new KvNode(); n.Type = 0; n.Key = key; n.Value = value; return n; }
}
'@

function Get-SteamDir {
    $key = Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue
    if ($key -and $key.SteamPath) { return ($key.SteamPath -replace '/', '\') }
    foreach ($p in @("${env:ProgramFiles(x86)}\Steam", "$env:ProgramFiles\Steam")) {
        if (Test-Path -LiteralPath (Join-Path $p 'steam.exe')) { return $p }
    }
    throw 'Steam was not found on this PC.'
}

function Get-SteamUserDir([string]$steamDir) {
    $login = Join-Path $steamDir 'config\loginusers.vdf'
    if (Test-Path -LiteralPath $login) {
        $text = Get-Content -LiteralPath $login -Raw
        foreach ($m in [regex]::Matches($text, '"(\d{17})"\s*\{([^}]*)\}')) {
            if ($m.Groups[2].Value -match '"MostRecent"\s*"1"') {
                $accountId = [uint64]$m.Groups[1].Value - 76561197960265728
                $dir = Join-Path $steamDir "userdata\$accountId"
                if (Test-Path -LiteralPath $dir) { return $dir }
            }
        }
    }
    # Fall back to the most recently used userdata folder.
    $latest = Get-ChildItem -LiteralPath (Join-Path $steamDir 'userdata') -Directory |
        Where-Object { $_.Name -match '^\d+$' -and $_.Name -ne '0' } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { throw 'No Steam user folder was found. Sign in to Steam once first.' }
    return $latest.FullName
}

$testMode = [bool]$ShortcutsFile
if ($testMode) {
    $vdfPath = $ShortcutsFile
} else {
    $steamDir = Get-SteamDir
    $steamExe = Join-Path $steamDir 'steam.exe'
    $vdfPath  = Join-Path (Get-SteamUserDir $steamDir) 'config\shortcuts.vdf'
}
Write-Host "Steam shortcuts file: $vdfPath"

# Steam rewrites shortcuts.vdf when it exits, so it must be closed first.
if (-not $testMode -and (Get-Process steam -ErrorAction SilentlyContinue)) {
    Write-Host 'Closing Steam...'
    & $steamExe -shutdown
    $waited = 0
    while ((Get-Process steam -ErrorAction SilentlyContinue) -and $waited -lt 90) { Start-Sleep 2; $waited += 2 }
    if (Get-Process steam -ErrorAction SilentlyContinue) { throw 'Steam did not close. Exit Steam manually and run this again.' }
}

# Load existing shortcuts, or start a new file.
if (Test-Path -LiteralPath $vdfPath) {
    $original = [IO.File]::ReadAllBytes($vdfPath)
    $root = [KvBinary]::Read($original)
    if ([Convert]::ToBase64String([KvBinary]::Write($root)) -ne [Convert]::ToBase64String($original)) {
        throw 'The existing shortcuts file has a layout this script does not understand. Nothing was changed.'
    }
    $backup = "$vdfPath.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss')
    Copy-Item -LiteralPath $vdfPath -Destination $backup
    Write-Host "Backup: $backup"
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path $vdfPath) | Out-Null
    $root = New-Object 'System.Collections.Generic.List[KvNode]'
}

$shortcutsNode = $root | Where-Object { $_.Type -eq 0 -and $_.Key -eq 'shortcuts' } | Select-Object -First 1
if (-not $shortcutsNode) {
    $shortcutsNode = [KvBinary]::Map('shortcuts', (New-Object 'System.Collections.Generic.List[KvNode]'))
    $root.Add($shortcutsNode)
}
$entries = $shortcutsNode.Value

# Remove any earlier KHARVOX entry, keeping everything else in order.
$kept = New-Object 'System.Collections.Generic.List[KvNode]'
foreach ($e in $entries) {
    $name = $e.Value | Where-Object { $_.Key -ieq 'AppName' } | Select-Object -First 1
    if ($name -and $name.Value -eq $AppName) { Write-Host 'Replacing the existing KHARVOX entry.'; continue }
    $kept.Add($e)
}

# The command searches every ready drive for \KHARVOX\Start-Kharvox.ps1.
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$exe = '"' + $powershell + '"'
$command = '$f = $null; foreach ($d in [IO.DriveInfo]::GetDrives()) { if ($d.IsReady) { $p = Join-Path $d.RootDirectory.FullName ''KHARVOX\Start-Kharvox.ps1''; if (Test-Path -LiteralPath $p) { $f = $p; break } } }; if ($f) { & $f } else { Add-Type -AssemblyName System.Windows.Forms; [void][System.Windows.Forms.MessageBox]::Show(''The KHARVOX drive was not found. Connect it and try again.'', ''KHARVOX'') }'
$launchOptions = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "' + $command + '"'

# Icon from the drive as it is mounted right now (cosmetic only).
$icon = Join-Path (Split-Path $PSScriptRoot -Parent) 'SteamLibrary\steamapps\common\DOOM\DOOMx64vk.exe'
if (-not (Test-Path -LiteralPath $icon)) { $icon = Join-Path $PSScriptRoot 'KharvoxLauncher.exe' }

$appId = [KvBinary]::ShortcutId($exe, $AppName)
$fields = New-Object 'System.Collections.Generic.List[KvNode]'
$fields.Add([KvBinary]::Int('appid', $appId))
$fields.Add([KvBinary]::Str('AppName', $AppName))
$fields.Add([KvBinary]::Str('Exe', $exe))
$fields.Add([KvBinary]::Str('StartDir', '"' + $env:SystemRoot + '\System32\"'))
$fields.Add([KvBinary]::Str('icon', $icon))
$fields.Add([KvBinary]::Str('ShortcutPath', ''))
$fields.Add([KvBinary]::Str('LaunchOptions', $launchOptions))
$fields.Add([KvBinary]::Int('IsHidden', 0))
$fields.Add([KvBinary]::Int('AllowDesktopConfig', 1))
$fields.Add([KvBinary]::Int('AllowOverlay', 1))
$fields.Add([KvBinary]::Int('OpenVR', 1))
$fields.Add([KvBinary]::Int('Devkit', 0))
$fields.Add([KvBinary]::Str('DevkitGameID', ''))
$fields.Add([KvBinary]::Int('DevkitOverrideAppID', 0))
$fields.Add([KvBinary]::Int('LastPlayTime', 0))
$fields.Add([KvBinary]::Str('FlatpakAppID', ''))
$fields.Add([KvBinary]::Str('sortas', ''))
$fields.Add([KvBinary]::Map('tags', (New-Object 'System.Collections.Generic.List[KvNode]')))
$kept.Add([KvBinary]::Map('', $fields))

# Steam numbers entries 0, 1, 2, ...
for ($n = 0; $n -lt $kept.Count; $n++) { $kept[$n].Key = [string]$n }
$shortcutsNode.Value = $kept

[IO.File]::WriteAllBytes($vdfPath, [KvBinary]::Write($root))
Write-Host "Added '$AppName' to Steam."

# Library artwork from .\artwork, named after the entry's ID in Steam's grid folder.
$artDir = Join-Path $PSScriptRoot 'artwork'
if (Test-Path -LiteralPath $artDir) {
    $grid = Join-Path (Split-Path $vdfPath) 'grid'
    New-Item -ItemType Directory -Force -Path $grid | Out-Null
    $map = @{ 'kharvoxp.png' = "${appId}p.png"; 'kharvox.png' = "$appId.png"; 'kharvox_hero.png' = "${appId}_hero.png"; 'kharvox_logo.png' = "${appId}_logo.png" }
    foreach ($source in $map.Keys) {
        $from = Join-Path $artDir $source
        if (Test-Path -LiteralPath $from) { Copy-Item -LiteralPath $from -Destination (Join-Path $grid $map[$source]) -Force }
    }
    Write-Host "Installed library artwork to $grid"
}

if (-not $testMode -and -not $NoRestart) {
    Write-Host 'Starting Steam...'
    Start-Process -FilePath $steamExe
}
