# Deus Ex: Human Revolution Director's Cut VR

**Status:** Removed. The mod worked under Proton, but at 18 to 36 fps reprojected and with only eleven inputs it was judged not worth keeping; removed on 2026-10-24 and the game plays flat from its normal Steam entry. Documented for the lessons and for a retry.

| | |
|---|---|
| Upstream | [farmerarmor/DeusExHRVR](https://github.com/farmerarmor/DeusExHRVR) 0.3.0: a `d3d11.dll` proxy in the 32-bit game plus a 64-bit OpenXR helper, `DeusExHRVRHost.exe` |
| Game data | Deus Ex: Human Revolution Director's Cut (Steam 238010). The mod's files went into the game folder |
| Route | Proton 11.0 (ARM64) + FEX, in the game's own prefix |
| Steam entry | While installed: the library entry, VR-only and red-labelled; later a flat/VR split with a "Deus Ex HR DC VR" shortcut. Now the plain library entry |
| Set up / removed | 2026-10-21 / 2026-10-24 |

## What it is

The 32-bit game renders both eyes into one shared 1728x3456 Direct3D 11 texture, and a separate 64-bit OpenXR helper process submits it to SteamVR. Cross-process texture sharing works under Proton 11.0 (ARM64) on the Frame.

## What broke on the Frame

- **ARM64 runtime DLL.** The prefix's `vcruntime140_1.dll` is ARM64; the x86-64 helper could not load it.
- **The game rewrites its graphics registry.** Whenever options are saved, DXHR writes `StereoMode 0`, `VSync 1` and `AA 5` back into `[Software\Eidos\Deus Ex: HRDC\Graphics]`. With stereo off the game never produces the shared eye pair and the helper quits after about 20 seconds. VR stopped working silently two days after the install.
- **Scale.** At the mod's default `WorldUnitsPerMetre` 100 the world felt flat and the wrong size.
- **Controls.** The mod ships Touch bindings for eleven inputs. The game suggests two interaction profiles, so a custom Frame binding was ignored until the simple profile was locked empty.
- **Performance.** SteamVR paced it at 18 to 36 Hz with reprojection throughout.

## What was done

- Installed by hand following the mod's `install.ps1`: `dist/*` into the game folder (the d3d11 proxy, `atidxx32.dll`, `atiadlxy.dll`, the `DeusExHRVR/` host and shaders), `DeusExHRVR.ini` from the example, and the registry values `EnableDirectX11=1 StereoMode=1 EnableVSync=0 AntiAliasingMode=0` in the prefix's `user.reg` (originals backed up). An x86-64 `vcruntime140_1.dll` beside the host.
- A flat/VR split: the `deusex` case of `flatvr-launch.sh` set the four registry values per mode on every start and renamed the three mod DLLs aside for flat play, with a "Deus Ex HR DC VR" shortcut.
- `WorldUnitsPerMetre` 300 (the author's tested value) fixed the depth and scale; F8 eye captures confirmed real stereo either way.
- A Frame binding (the mod's OpenXR actions are not hand-scoped, so one works) with the simple profile locked to `{}`, plus `[Buttons]` and `[ScreenButtons]` maps in `DeusExHRVR.ini`, gave the standard layout against the game's Xbox prompts.

## Lessons

- A game that rewrites its own graphics settings needs a launch wrapper that re-applies the mod's values every start; that wrapper is also the clean place for a flat/VR split.
- Scale controls the depth you notice; check the author's recommended value before judging stereo broken.
- Hand-agnostic OpenXR actions can be rebound to the Frame directly, once the app's input context holds one profile (see [KNOWN-ISSUES.md](../../KNOWN-ISSUES.md)).

## State left on the headset

The mod's DLLs, folder, ini, logs and captures were deleted from the game folder; the four graphics values went back to their originals (not the whole registry backup); the launch options, the VR shortcut and its art, the `flatvr-launch.sh` case and the SteamVR binding files were removed. The scripts and the mod's README are kept on the headset for a retry.

## Retry

```bash
# the original install (writes backups of everything it changes), then the registry per mode and the binding
ssh frame "bash ~/PCVR/DeusExHRVR/install.sh"
ssh frame "python3 ~/PCVR/DeusExHRVR/dx_mode.py vr"       # the four graphics values for VR (flat = originals)
ssh frame "python3 ~/PCVR/DeusExHRVR/dx_controls.py"      # Frame binding, simple profile locked, ini button maps
ssh frame "bash ~/PCVR/DeusExHRVR/dx_scale.sh 300"        # WorldUnitsPerMetre
ssh frame "bash ~/PCVR/DeusExHRVR/launch.sh 60"
```

Keys: F9 recenter, F6 tracking mode, F8 eye capture. On the test headset a small XTest key sender (`xkey :1 F8 [window]`) presses them over SSH; its source is not in this repository yet.

## Files in this repo

- [install.sh](../../scripts/deus-ex-hr-vr/install.sh), [launch.sh](../../scripts/deus-ex-hr-vr/launch.sh): the original install with backups, and the launcher with optional Proton and DXVK logging.
- [dx_mode.py](../../scripts/deus-ex-hr-vr/dx_mode.py): the four graphics registry values per mode.
- [dx_flatvr.py](../../scripts/deus-ex-hr-vr/dx_flatvr.py): the flat/VR split (the `flatvr-launch.sh` case and the shortcut).
- [dx_controls.py](../../scripts/deus-ex-hr-vr/dx_controls.py): the Frame binding, the simple-profile lock and the ini button maps.
- [dx_scale.sh](../../scripts/deus-ex-hr-vr/dx_scale.sh): sets `WorldUnitsPerMetre`.

## Credits

- farmerarmor for DeusExHRVR; Eidos Montreal and Square Enix for the game (data not included).
- This repo holds only scripts. No game data, no mod files, no DLLs.
