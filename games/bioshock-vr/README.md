# BioShock Remastered VR

**Status:** Parked. A 32-bit game with a 32-bit OpenXR-to-OpenVR shim; the shim connects to SteamVR, the game never draws a frame. Removed on 2026-10-21; the findings are kept so the next attempt starts further along.

| | |
|---|---|
| Steam app | 409710 |
| Engine / VR API | 32-bit `BioshockHD.exe`; the mod's SteamVR path is its own 32-bit OpenXR-to-OpenVR shim (`bvr_steamvr32.dll` plus a 32-bit `openvr_api.dll`) |
| Mod | bioshock-vr v0.8.3 by mohamad-balouza, https://github.com/mohamad-balouza/bioshock-vr |
| Route | Proton 11.0 (ARM64) + FEX; x86 Proton Experimental never starts the game at all |
| Fix | none yet |
| Date | diagnosed 2026-10-21 |

## What it is

BioShock Remastered is a 32-bit Windows game. The bioshock-vr mod injects through `xinput1_3.dll` and reaches SteamVR through a 32-bit shim that translates its OpenXR calls to OpenVR. On the Frame that means Proton's i386 vrclient bridge under FEX.

## What you see

The game starts, the mod loads and SteamVR reports a connected client, but no frame is ever presented. The headset shows nothing from the game.

## What broke on the Frame

- **wineopenxr / OpenXR loader.** Wine looks "elevated", so the OpenXR loader ignores `XR_RUNTIME_JSON`. Fixed by registering the shim as the 32-bit active runtime in the prefix registry: `[Software\Wow6432Node\Khronos\OpenXR\1]` in `compatdata/409710/pfx/system.reg` (backup `system.reg.bak-bioshockvr`), done by a small `regfix.py`.
- **Proton's i386 vrclient bridge: works.** With that, 32-bit OpenVR does connect under Proton 11.0 (ARM64). The mod's log reads:

```
OpenVR connected. IVRSystem_026 / IVRCompositor_029 / IVRInput_011
```

- **The game/mod itself under FEX: hangs before the first frame.** The game never presents its first frame: main thread idle in ntsync, only six threads, no render or audio threads. Ruled out:
  - address space (1.7 of 4 GB used)
  - window focus (a nested gamescope wrapper, `bioshockvr-launch.sh`, did not help)
  - DXVK's OpenVR hook (`dxvk.enableOpenVR=False` did not help)
- **Debugging limits.** `PROTON_LOG=1` makes it hang inside `OutputDebugString` handling instead. `winedbg --auto` cannot walk 32-bit stacks under FEX. x86 "Proton - Experimental" never starts the game at all.

Mod logs: `compatdata/409710/pfx/drive_c/users/steamuser/AppData/Local/BioshockVR/{bioshockvr,ovrshim}.log`.

## What was tried

1. Installed the mod into the game folder; the mod DLLs only load with `WINEDLLOVERRIDES=xinput1_3=n,b`.
2. Registered the shim as the 32-bit OpenXR active runtime in `system.reg` (the `XR_RUNTIME_JSON` route is ignored because Wine appears elevated).
3. Confirmed the OpenVR connection in the shim log.
4. Tried a nested gamescope, disabled DXVK's OpenVR hook, checked address space, tried Proton logging and winedbg. None moved the game past its idle main thread.
5. Left the game as plain flat BioShock: default compat tool, no launch options. Then removed the game, the prefix and the mod folder on 2026-10-21.

## Exact commands

Nothing from this attempt is in the repo as a script. The launch option that made the mod load was:

```
WINEDLLOVERRIDES=xinput1_3=n,b %command%
```

## Check it worked

It did not. A working run would show a render thread and a presented frame after the `OpenVR connected` line in `ovrshim.log`.

## Status and known issues

Parked. What would move it:

- A way to see where the 32-bit main thread is waiting under FEX (winedbg cannot walk the stack; Proton logging changes the hang).
- A 64-bit build of the mod or shim, which would take the i386 bridge out of the picture.

Retry recipe: install the mod v0.8.3, apply the `Wow6432Node\Khronos\OpenXR\1` registry entry for the 32-bit shim, launch with `WINEDLLOVERRIDES=xinput1_3=n,b %command%` on Proton 11.0 (ARM64), and read `ovrshim.log`.

Also found during this work: a stale `winedevice.exe` had spun a CPU core for six hours after the prefix was deleted. If the headset feels slow, `pgrep -a winedevice`.

## Undo

The mod's own `uninstall.sh` removed its files from the game folder; the game, the prefix (`compatdata/409710`) and the mod folder were then removed entirely. The registry backup was `system.reg.bak-bioshockvr`.

## Credits

- bioshock-vr v0.8.3 by mohamad-balouza.
- This repo holds only scripts, no game data or binaries.
