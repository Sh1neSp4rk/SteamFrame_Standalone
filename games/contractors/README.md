# Contractors VR

**Status:** Working. The file Steam launches is Unreal's prerequisite checker, not the game; a wrapper script starts the real executable instead.

| | |
|---|---|
| Steam app | 963930, 24 GB |
| Engine / VR API | Unreal 4.22, OpenVR (SteamVR plugin) |
| Route | Proton 11.0 (ARM64) + FEX, Steam's default compat tool |
| Fix | wrapper script + launch option |
| Date | fixed 2026-10-09 |

## What it is

Contractors is a Windows-only Steam title. Steam offers four depots and all of them are Windows x86-64; there is no Frame-native build. On the Frame it runs through Proton and FEX like any other Windows game.

## What you see

- Press Play. Steam shows the game as running and the headset stays in SteamVR Home. Nothing ever appears.
- After a minute or so you press Stop. Every attempt looked like this.
- Reinstalling does nothing. Switching Proton versions does nothing.

## What broke on the Frame

- **Launcher.** The launch entry starts `Contractors.exe` in the game's root folder, a 147 KB file. That is Unreal Engine's *BootstrapPackagedGame*: it checks that the Visual C++ runtime and DirectX are installed, then starts the real executable, `Contractors_UE4_22/Binaries/Win64/Contractors_UE4_22_Steam-Win64-Shipping.exe`.
- **Steam install script.** The install script for this game installs the 2015 Visual C++ runtime (it is what the app's shared depots list), which writes version 14.0.24215 into the prefix registry.
- **The bootstrapper's version check.** The bootstrapper was built with a newer toolchain. It reads `Major`, `Minor`, `Bld` and `Rbld` from `HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64`, decides 14.0 is too old, then looks for the installer it would normally offer to run, `Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe`. The Steam build does not ship that file. So it shows a Yes/No message box ("The following component(s) are required to run this program ... Would you like to install them now?") on the Wine desktop and waits. In VR that desktop is invisible. The game never starts.

Proton log for the bootstrapper process with `WINEDEBUG=+reg,+file,+dialog`:

```
trace:reg:NtOpenKeyEx (0x20,L"SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64",...)
trace:reg:RegQueryValueExW (...,L"Major",...)   L"Minor"   L"Bld"   L"Rbld"
warn:file:NtQueryAttributesFile L"\\??\\S:\\steamapps\\common\\ContractorsVR\\Engine\\Extras\\Redist\\en-us\\UE4PrereqSetup_x64.exe" not found (c000003a)
trace:dialog:DIALOG_GetControl32     L"Button" L"&Yes" ...
trace:dialog:DIALOG_GetControl32     L"Button" L"&No" ...
```

No `Contractors_UE4_22_Steam-Win64-Shipping.exe` was ever loaded, and SteamVR's `vrserver.txt` never saw it connect.

The registry key, the two runtime files the bootstrapper also tests for (`msvcp140_2.dll`, `vcruntime140_1.dll`) and `xinput1_3.dll` all exist in the prefix. Only the version comparison fails.

## The fix

Skip the bootstrapper and start the shipping executable directly. The wrapper takes the launch command Steam built and swaps one argument. The game's own `-hmd=steamvr` argument is kept, so it comes up in VR as before.

The wrapper lives in this repo under `scripts/contractors/`:

```bash
#!/bin/bash
# Steam hands this script its full launch command as arguments.
# Contractors.exe is Unreal's "BootstrapPackagedGame" launcher: it checks the
# VC++ / DirectX redistributables and, when it is not satisfied, pops a Yes/No
# dialog that is invisible in VR, so the real game never starts on the Frame.
# Skip the bootstrapper and run the shipping executable directly.
a=("$@")
for i in "${!a[@]}"; do
  case "${a[$i]}" in
    */ContractorsVR/Contractors.exe)
      a[$i]="${a[$i]%/*}/Contractors_UE4_22/Binaries/Win64/Contractors_UE4_22_Steam-Win64-Shipping.exe"
      ;;
  esac
done
exec "${a[@]}"
```

## Exact commands

1. Copy the wrapper to the headset as `/home/steamos/contractors` and make it executable. From a PC:

```bash
scp scripts/contractors/contractors steamos@frame.local:~/ && ssh steamos@frame.local chmod 755 contractors
```

2. In the headset's library: Contractors VR, Properties, Launch Options:

```
/home/steamos/contractors %command%
```

3. Launch.

## Check it worked

```bash
ssh frame "ls ~/.local/share/Steam/logs | grep Contractors"
# vrclient_Contractors_UE4_22_Steam-Win64-Shipping.txt   <- the real exe talked to SteamVR
ssh frame "grep -c 'Created remote Vulkan image' ~/.local/share/Steam/logs/vrclient_Contractors_UE4_22_Steam-Win64-Shipping.txt"
# 6 -> three 1728x1728 textures per eye were handed to the compositor
```

The game also creates `Saved/Config`, `Saved/Logs` and `Saved/SaveGames` under `compatdata/963930/pfx/drive_c/users/steamuser/AppData/Local/Contractors_UE4_22/`. On the verified run it registered as the SteamVR scene application within 10 seconds of launch and ran until stopped.

## Status and known issues

- **First run downloads your mod.io maps.** Contractors pulls every community map the account is subscribed to into `Contractors_UE4_22/ApeModio/`. On the test headset that was 1.4 GB in the first two minutes, which pushed the internal drive from 2.6 GB free to under 1 GB. Keep space in reserve or unsubscribe from maps you do not use.
- No anti-cheat is involved (the SCUE4 plugin the game bundles is an in-process scanner and loads fine), so online play is not blocked by this fix.
- Nothing about the game's data changes; this only changes which executable Steam starts.
- Untested alternative: installing the Visual C++ 2022 redistributable into the prefix would make the stock bootstrapper pass, but a prefix reset or a future Steam install script run would undo it. The launch option survives both.

## Undo

```bash
ssh frame rm /home/steamos/contractors
# then clear the Launch Options field in the game's Properties
```

## Files in this repo

- [contractors](../../scripts/contractors/contractors): the launch-option wrapper that swaps the bootstrapper for the shipping executable.

## Credits

No mod is involved. This repo holds only scripts, no game data or binaries.
