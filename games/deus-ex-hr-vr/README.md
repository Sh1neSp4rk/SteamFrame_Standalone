# Deus Ex: Human Revolution Director's Cut VR

**Status:** Working — cross-process Direct3D 11 texture sharing works under Proton 11 on the Frame; one runtime DLL needed swapping.

| | |
|---|---|
| Upstream | DeusExHRVR 0.3.0 by farmerarmor, a `d3d11.dll` proxy plus `DeusExHRVRHost.exe`, OpenXR |
| Game data | Deus Ex: Human Revolution Director's Cut (Steam 238010) |
| Route | Proton + FEX (Proton 11.0, ARM64), no launch options |
| Steam entry | The library entry itself, VR-only, with red-labelled art |
| Set up | 2026-10-21 |

## What it is

The 32-bit game renders both eyes into one shared 1728x3456 Direct3D 11 texture through the mod's `d3d11.dll` proxy. A separate 64-bit OpenXR helper, `DeusExHRVR/DeusExHRVRHost.exe`, opens that shared texture and submits it to SteamVR. Cross-process texture sharing between a 32-bit and a 64-bit process works under Proton 11.0 (ARM64) on the Frame. Confirmed in the headset; SteamVR paced it at 24 to 36 Hz, reprojected, on the first run.

## What broke on the Frame

- **Proton, runtime DLLs:** the prefix's `vcruntime140_1.dll` is ARM64, and the x86-64 host `DeusExHRVRHost.exe` cannot load it.
- **The mod's installer:** the mod ships `install.ps1`, a PowerShell script; its steps were reproduced by hand.
- **Registry:** the game only renders in the stereo path with four graphics values set in the prefix registry.

## The fix

- `install.sh` copies `dist/*` into the game folder (the `d3d11.dll` proxy, `atidxx32.dll`, `atiadlxy.dll`, the `DeusExHRVR/` host and shaders), backing up any file it overwrites into `<game>/DeusExHRVR-backup/`, and creates `DeusExHRVR.ini` from the example.
- The Frame fix: x86-64 `msvcp140.dll`, `vcruntime140.dll` and `vcruntime140_1.dll` (14.51, taken from another game's prefix) are placed beside the 64-bit host in `<game>/DeusExHRVR/`.
- The prefix registry, `[Software\Eidos\Deus Ex: HRDC\Graphics]` in `user.reg`, gets `EnableDirectX11=1 StereoMode=1 EnableVSync=0 AntiAliasingMode=0`, the same four values `install.ps1` sets. The originals are saved to `<game>/DeusExHRVR-backup/graphics-registry-before.txt` and the whole file to `user.reg.bak-deusexhrvr`. The Graphics key must already exist, so the game has to be launched once before installing.

## Exact commands

The scripts live in this repo under `scripts/deus-ex-hr-vr/` and are copied to `~/PCVR/DeusExHRVR/` on the headset. The mod archive is extracted to `~/PCVR/DeusExHRVR/extracted/DeusExHRVR`.

```bash
# game closed; installs the mod, the x86-64 runtimes and the registry values, writes uninstall.sh
ssh frame "bash ~/PCVR/DeusExHRVR/install.sh"

# launch through Steam and report processes, Steam launch state and the mod's logs after N seconds (default 75)
ssh frame "bash ~/PCVR/DeusExHRVR/launch.sh 75"

# the same with Proton and DXVK logging turned on for that launch
ssh frame "bash ~/PCVR/DeusExHRVR/launch.sh 75 debug"
```

No launch options are needed. In debug mode `launch.sh` temporarily sets:

```
PROTON_LOG=1 WINEDEBUG=+loaddll,warn+module,err DXVK_LOG_LEVEL=info DXVK_LOG_PATH=/home/steamos/PCVR/DeusExHRVR/dxvk-logs %command%
```

and clears it again on a plain launch. Settings: `<game>/DeusExHRVR.ini`. Logs: `<game>/DeusExHRVR*.log`.

## Controls

The mod's defaults; not yet reviewed against the [standard Frame layout](../../FRAME-LAYOUT.md). Keyboard keys from the mod: F9 recenters, F6 switches tracking mode.

## Status and known issues

- Working in the headset.
- SteamVR paced the first run at 24 to 36 Hz with reprojection.
- Controls have not been converted to the standard layout.
- Unrelated but found the same day: a stale BioShock `winedevice.exe` had spun a CPU core for six hours after its prefix was deleted. If something feels slow, check `pgrep -a winedevice`.

## Undo

```bash
ssh frame "bash ~/PCVR/DeusExHRVR/uninstall.sh"
```

`uninstall.sh` removes `d3d11.dll`, `atidxx32.dll`, `atiadlxy.dll`, the ini files, the `DeusExHRVR/` folder and captures, restores the backed-up files, puts `user.reg.bak-deusexhrvr` back, and clears the launch options.

## Files in this repo

- [install.sh](../../scripts/deus-ex-hr-vr/install.sh): the hand-made equivalent of the mod's `install.ps1`, plus the x86-64 runtimes and backups.
- [launch.sh](../../scripts/deus-ex-hr-vr/launch.sh): launches through Steam, optionally with Proton/DXVK logs, and reports mod state.

## Credits

- DeusExHRVR by farmerarmor, the mod this runs.
- Deus Ex: Human Revolution Director's Cut (game data from Steam, not included).
- Valve for SteamVR, the OpenXR runtime, Proton and the Steam Frame.

This repo holds only scripts. It contains no game data, no mod binaries and no game binaries. The Microsoft runtime DLLs copied by the installer are not included either.
