# Halo: The Master Chief Collection (flat and with the VR mod)

**Status:** Working, with caveats. Two separate problems: Steam's install script wrecked the Proton prefix, and the VR mod's hooks cannot patch ARM64 code. Both were fixed without touching SteamOS; online matchmaking (EAC) stays off.

| | |
|---|---|
| Steam app | 976730, 97 GB |
| Engine / VR API | Direct3D 11 game; the mod talks to SteamVR/OpenXR |
| Mod | MCCVR 0.5.1, https://github.com/moistman42069/MCCVR-Halo-Build |
| Route | Proton Experimental (ARM64) + FEX, Steam's default for this app |
| Fix | prefix repair + wrapper + x86-64 DXVK beside the exe |
| Date | fixed 2026-10-09 |

## What it is

Halo MCC is a Windows x86-64 title with Easy Anti-Cheat. Steam's launch menu offers two entries, "Halo: The Master Chief Collection" and "Halo: MCC Anti-Cheat Disabled". With the wrapper below those two entries become flat and VR respectively. MCCVR is an injected VR mod that hooks Direct3D 11 in memory.

## What you see

- Press Play on either entry. After about three seconds the button is back to Play. No window, no VR session.
- Changing the Proton version does nothing.

## What broke on the Frame

### 1. Steam install script: the prefix is poisoned by Easy Anti-Cheat's installer

MCC's Steam install script runs `easyanticheat\easyanticheat_eos_setup.exe install` inside the prefix. That installer bundles a Visual C++ 2017 redistributable and writes Microsoft's Windows x86-64 C runtime DLLs into `windows/system32` (and i386 ones into `syswow64`): `ucrtbase.dll`, `msvcp140.dll`, `vcruntime140.dll`, `concrt140.dll`, `vccorlib140.dll`, `vcomp140.dll`, `mfc140*.dll` and about forty `api-ms-win-*.dll` stubs. On a PC that is harmless. On the Frame, Proton's own system DLLs are ARM64 builds, and Wine's own boot process now tries to load Microsoft's x86-64 `ucrtbase.dll` from inside ARM64 code:

```
err:module:import_dll Loading library ucrtbase.dll (which is needed by L"C:\windows\system32\sechost.dll") failed (error c000007b)
err:module:... Importing dlls for L"C:\windows\system32\wineboot.exe" failed, status c0000135
Unhandled exception code c000001d   (in libarm64ecfex.dll)
```

Wine cannot even boot the prefix, so every launch dies in three seconds.

### 2. The game/mod itself and DXVK: the VR mod crashes inside Direct3D

Once the prefix was repaired the mod injected, reported "headset found on runtime SteamVR/OpenXR 2.18.2", printed "D3D11 hooks installed" and then died with exception `C000001D` (illegal instruction) at an address inside `d3d11.dll`. Proton ARM64's DXVK is a native ARM64 library; the mod's MinHook writes x86-64 trampolines into it. The fix is to give the game an x86-64 DXVK, which Proton also ships.

### 3. Anti-cheat

EAC has no Linux path unless the publisher enabled it, and it does not run under FEX either way. EAC is never started on the Frame: its bootstrapper can reinstall the VC++ runtime that broke the prefix.

## The fix

### Step 1: repair the prefix

[repair-mcc-prefix.sh](../../scripts/halo-mcc/repair-mcc-prefix.sh) moves every foreign runtime DLL into a backup folder inside the prefix (`compatdata/976730/polluted-backup-<date>/`) and copies Proton's own versions back. Nothing is deleted. On the test headset the result was `restored=12 backed-up-only=104`.

### Step 2: install the VR mod

1. Download `Halo-MCC-VR.zip` from the MCCVR-Halo-Build release page (0.5.1 at the time) and extract it so the launcher sits at `.../common/Halo The Master Chief Collection/Halo_MCC_VR/HaloMCCVRLauncher.exe`.
2. In `Halo_MCC_VR/halomccvr.cfg` set `resolution_scale = 0.5`. The Adreno 750 is not a desktop GPU.

### Step 3: give the game x86-64 DXVK

Copy Proton's x86-64 `dxgi.dll`, `d3d11.dll` and `d3d10core.dll` next to the game executable. Wine resolves DLLs from the executable's folder first, so these three copies win over the ARM64 ones in `system32`, and the mod's hooks find x86-64 code to patch.

### Step 4: the wrapper and launch option

The wrapper [mcc](../../scripts/halo-mcc/mcc) is saved as `/home/steamos/mcc` (the mod folder also keeps a copy as `mcc-launch.sh`):

```bash
#!/bin/bash
# Steam hands this script its full launch command as arguments.
# Normal entry (mcclauncher.exe, EAC) -> run the game directly with -no-eac: FLAT, no anti-cheat.
# "Anti-Cheat Disabled" entry        -> start the VR mod launcher instead: VR.
# EAC is never started on the Frame: its bootstrapper can reinstall the VC++ runtime that
# broke the Proton prefix, and EAC does not work under FEX anyway.
a=("$@")
for i in "${!a[@]}"; do
  case "${a[$i],,}" in
    *mcc-win64-shipping.exe)
      root="${a[$i]%/*/*/*/*}"
      a[$i]="$root/Halo_MCC_VR/HaloMCCVRLauncher.exe"
      ;;
    */mcclauncher.exe)
      a[$i]="${a[$i]%/*}/MCC/Binaries/Win64/MCC-Win64-Shipping.exe"
      a+=("-no-eac")
      ;;
    -no-eac)
      unset "a[$i]"
      ;;
  esac
done
exec "${a[@]}"
```

With the wrapper in place the two entries in Steam's launch menu mean:

| Steam entry | What Steam would run | What actually runs |
|---|---|---|
| Halo: The Master Chief Collection | `mcclauncher.exe` (starts EAC, then the game) | `MCC-Win64-Shipping.exe -no-eac`: flat, no anti-cheat |
| Halo: MCC Anti-Cheat Disabled | `MCC-Win64-Shipping.exe -no-eac` | `Halo_MCC_VR/HaloMCCVRLauncher.exe`: VR |

## Exact commands

The scripts live in this repo under `scripts/halo-mcc/`.

```bash
# Step 1: repair the prefix (run from the PC; the game must be closed)
ssh frame 'bash -s' < scripts/halo-mcc/repair-mcc-prefix.sh

# Step 3: x86-64 DXVK beside the exe
ssh frame 'cd ~/.local/share/Steam/steamapps/common && cp "Proton Experimental (ARM64)/files/lib/wine/dxvk/x86_64-windows/"{dxgi.dll,d3d11.dll,d3d10core.dll} "Halo The Master Chief Collection/MCC/Binaries/Win64/"'

# Step 4: the wrapper
scp scripts/halo-mcc/mcc steamos@frame.local:~/ && ssh steamos@frame.local chmod 755 mcc
```

Launch Options on the headset (the `PROTON_LOG=1` part is optional and only keeps a Wine log in the home folder):

```
PROTON_LOG=1 bash ~/mcc %command%
```

## Check it worked

The repair script prints a verification table; it wants `builtin=1` and `Aarch64` in `system32`, `Intel 80386` in `syswow64`.

The mod writes `Halo_MCC_VR/HaloMCCVR.log`. A good VR session logs `status: session=focused shouldRender=1 layers=1` and an fps figure (51 at the menu on the verified run), with no `FAULT` or `C000001D` lines over several minutes. The flat entry simply runs; `~/steam-976730.log` stays free of unhandled exceptions.

## Status and known issues

- **Never let the EAC path run.** Steam's "Verify integrity" or a reinstall may run the install script again, which re-poisons the prefix. If Play starts bouncing back in three seconds again, run the repair script again.
- Online matchmaking needs EAC and is therefore off. Campaign, custom games and co-op by invite are what you get.
- **Xbox sign-in:** the mod's focus hook starves the sign-in box in VR. Sign in once from the flat entry (Steam + X opens the keyboard; a Bluetooth keyboard is easier). The token is then cached in the prefix.
- The x86-64 DXVK copies apply to both entries. Flat mode is a little slower and the first run has heavy shader-compile stutter; it settles.
- Rollback of the prefix repair: the moved files are in `compatdata/976730/polluted-backup-<date>/`; `cp -a` them back if ever needed (there is no reason to).

## Undo

```bash
ssh frame 'rm ~/mcc; cd ~/.local/share/Steam/steamapps/common/"Halo The Master Chief Collection" && rm MCC/Binaries/Win64/{dxgi.dll,d3d11.dll,d3d10core.dll} && rm -r Halo_MCC_VR'
# then clear the Launch Options field
```

## Files in this repo

- [repair-mcc-prefix.sh](../../scripts/halo-mcc/repair-mcc-prefix.sh): moves the foreign x86-64/i386 runtime DLLs out of the prefix and restores Proton's copies.
- [mcc](../../scripts/halo-mcc/mcc): launch-option wrapper that maps the two Steam entries to flat (no EAC) and VR (mod launcher).

## Credits

- MCCVR 0.5.1 by moistman42069 (MCCVR-Halo-Build on GitHub).
- This repo holds only scripts, no game data or binaries. The mod is downloaded from its own release page.
