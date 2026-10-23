# Far Cry VR (CryVR)

**Status:** Working. A 32-bit OpenVR mod under Proton; a proxy `openvr_api.dll` and a native ARM64 overlay helper get the HUD and menus into the headset. Confirmed on 2026-10-23.

| | |
|---|---|
| Upstream | [fholger/farcry_vrmod](https://github.com/fholger/farcry_vrmod) 1.1.0 (CryVR): `Mods/CryVR`, a `d3d9.dll` DXVK 2.2 fork that drives OpenVR, DSOAL `dsound.dll`, SteamVR Input |
| Game data | Far Cry (Steam 13520), 32-bit `Bin32\FarCry.exe`. The mod's files go into the real Steam game folder |
| Route | Proton + FEX, in Far Cry's own prefix; Proton's i386 vrclient bridge |
| Steam entry | Non-Steam shortcut "Far Cry VR" 2151742621 = `steam -applaunch 13520 -frame-vr`, red "FAR CRY VR" art. Far Cry's own entry still launches flat through `flatvr-launch.sh` |
| Set up | 2026-10-23 |

## What it is

fholger's CryVR turns the 2004 Far Cry into a full VR game: a DXVK fork renders Direct3D 9 through Vulkan and submits to OpenVR, with motion-controller input through SteamVR Input and the HUD and menus drawn on OpenVR overlays.

## What broke on the Frame

- **The installer.** The NSIS installer found the prefix's empty stub Steam folder (`C:\Program Files (x86)\Steam\...\FarCry`) instead of the real game, so its files had to be moved into `steamapps/common/FarCry` (the list is in `mod-files.txt`).
- **The Steam exe under a shortcut.** Far Cry's Steam build quits unless started as its own app id, so the VR shortcut launches app 13520 with `-frame-vr` and the `farcry` case of `flatvr-launch.sh` does the rest.
- **ARM64 runtime DLLs.** Microsoft's x86 `msvcp140`, `vcruntime140` and `concrt140` have to sit next to `Bin32\FarCry.exe`; the prefix's copies are ARM64. They are Microsoft's and not in this repository.
- **The DXVK fork's logging crashes device creation.** Its Wine debug-output logging (`__wine_dbg_output`) clobbers ESI in this MSVC build, so `vkGetInstanceProcAddr` becomes a module handle. Not a Frame bug as such, but it only shows under Wine.
- **Proton's 32-bit vrclient asserts on Vulkan overlay textures.** CryVR draws its HUD and menus on overlays with Vulkan textures; Proton's i386 OpenVR bridge asserts in `IVROverlay::SetOverlayTexture` (`vroverlay_manual.c:465 !status`) and the game dies on the first HUD frame.
- **SteamVR's fallback overlay paths.** `SetOverlayRaw` stops for good after about 460 updates (error 23). `SetOverlayFromFile` shows only the first image per path, and every new path leaks about 4.7 MB in `vrcompositor` until SteamVR restarts. And SteamVR refuses to let one process set the texture of another process's overlay (error 12).

## The fix

1. **Launch:** Far Cry's launch options are `~/PCVR/bin/flatvr-launch.sh farcry %command%`. With `-frame-vr` the `farcry` case sets `DXVK_LOG_LEVEL=none` (avoids the logging crash) and `DXVK_STARTOPENVR=1`, forces `d3d9`, `dsound` and the C runtime native, starts hudbridge, and adds `-MOD:CryVR`. The first start shows the mod's auto-detection and configurator dialogs; click OK in theater mode.
2. **ovrshim**, a 32-bit proxy `openvr_api.dll` built on the Frame ([tools/far-cry-ovrshim](../../tools/far-cry-ovrshim/)). Every export forwards to the mod's own library, renamed `openvr_api_real.dll`, except `VR_GetGenericInterface`, which patches slot 60 (`SetOverlayTexture`) of the `IVROverlay_026` vtable. It validates the texture (the `FarCry3D` overlay only carries real data in cinema mode and is skipped) and reads the HUD back asynchronously: blit and downscale to 1024 pixels, double-buffered, never waiting, only changed frames, at most every 33 ms.
3. **hudbridge**, a native ARM64 OpenVR overlay app. ovrshim writes each frame into `/tmp/farcryvr_bridge_<n>.shm` (a seqlock header plus RGBA); hudbridge uploads changed frames to its own Vulkan images and calls `SetOverlayTexture`, the path native apps use. Since SteamVR refuses another process's overlay, it draws a mirror overlay that copies the game overlay's transform, width, visibility, sort order (plus one), bounds, alpha and curvature about 80 times a second. The game overlay keeps one transparent pixel through a single raw call, so the laser pointer still clicks the menus. hudbridge follows the launch pid and exits with the game. Memory stays flat.
4. **Controls:** `fc_frame_controls.py` writes `Mods/CryVR/steamvr/bindings_frame_controller.json`, adds a `frame_controller` default to the mod's `actions.json` (original kept as `.orig`) and selects it for `steam.app.13520` in `steamvr.vrsettings` (backup `.orig-farcry`).

`FRAMEVR_HUD` selects the HUD path: `bridge` (default), `raw`, `file`, `skip` or `pass` (reproduces the crash). Other ovrshim switches: `FRAMEVR_HUD_EVERY`, `_MAX`, `_MS`, `_OPAQUE`, `_STRESS`, and `FRAMEVR_INPUT_LOG=1` for IVRInput logging.

## Exact commands

The scripts live in this repo under `scripts/far-cry-vr/` and the two helpers under `tools/far-cry-ovrshim/`; on the headset they sit in `~/PCVR/FarCryVR/` and `~/PCVR/FarCryVR/ovrshim/`, with `flatvr-launch.sh` in `~/PCVR/bin/`.

```bash
# build the 32-bit proxy openvr_api.dll and install it in Bin32 (the mod's own becomes openvr_api_real.dll)
ssh frame "bash ~/PCVR/FarCryVR/ovrshim/build.sh"

# build the native aarch64 hudbridge next to it (headers from SteamVR's hellovr_vulkan sample)
ssh frame "bash ~/PCVR/FarCryVR/ovrshim/build_bridge.sh"

# Frame binding, actions.json default, steamvr.vrsettings selection
ssh frame "python3 ~/PCVR/FarCryVR/fc_frame_controls.py"

# launch with a free-memory watchdog (kills the game below 700 MB available); shim and bridge summary
ssh frame "bash ~/PCVR/FarCryVR/fc_bridgetest.sh 60 keep"
```

Logs: `ovrshim.log` in the game folder, `~/PCVR/FarCryVR/hudbridge.log`, and a Proton log when `~/PCVR/FarCryVR/debug` exists; `env.test` is sourced if present.

## Controls

On the [standard layout](../../FRAME-LAYOUT.md) with left bumper jump and left trigger crouch. The mod ships only Touch and Index bindings, and SteamVR's Touch-to-Frame remap passes the right-stick zones but none of the buttons, hence the custom binding.

| Input | On foot | In vehicles |
|---|---|---|
| Right trigger | Fire | Vehicle weapon |
| Right bumper | Use (doors, vehicles, mounted guns) | |
| Left trigger | Crouch | Leave vehicle |
| Left bumper | Jump | |
| A | Grenades (hold to throw) | Reload |
| B | Reload | Change seat |
| X | Binoculars | Lights |
| Menu | Pause menu | |
| Left stick | Move; click = sprint | Steer and throttle; click = change view |
| Right stick | Left/right turn (snap or smooth, mod option); up = next weapon and binocular zoom in; down = zoom out | |
| Grips (80%) | The mod's grip action (two-handed weapon hold) | |

If only the right hand responds, the left controller is not connected; SteamVR then logs input for the right hand only.

## Status and known issues

- HUD, menus and intro videos show in the headset without flicker; memory stays flat with hudbridge.
- Microsoft's x86 C++ runtime DLLs and the mod installer are not in this repository.
- The first launch needs two OK clicks in theater mode.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 2151742621"
# then clear Far Cry's launch options, delete the files listed in mod-files.txt from the game folder
# (restore Bin32\d3d9.dll.orig if present), restore actions.json.orig and the .orig-farcry vrsettings backup
```

## Files in this repo

- [tools/far-cry-ovrshim/ovrshim.c](../../tools/far-cry-ovrshim/ovrshim.c) and [build.sh](../../tools/far-cry-ovrshim/build.sh): the proxy `openvr_api.dll`.
- [tools/far-cry-ovrshim/hudbridge.cpp](../../tools/far-cry-ovrshim/hudbridge.cpp) and [build_bridge.sh](../../tools/far-cry-ovrshim/build_bridge.sh): the native overlay helper.
- [fc_frame_controls.py](../../scripts/far-cry-vr/fc_frame_controls.py): the Frame binding, actions.json default and vrsettings selection (layout table in its docstring).
- [fc_bridgetest.sh](../../scripts/far-cry-vr/fc_bridgetest.sh): launch with the memory watchdog and a bridge report.
- [mod-files.txt](../../scripts/far-cry-vr/mod-files.txt): the files the installer adds to the game folder, for the undo step.
- [scripts/common/flatvr-launch.sh](../../scripts/common/flatvr-launch.sh): the `farcry` case.

## Credits

- fholger for farcry_vrmod (CryVR), on his DXVK fork and DSOAL; Crytek and Ubisoft for Far Cry (game data not included).
- Valve for OpenVR, SteamVR and Proton.
- This repo holds only scripts and the helper sources. No game data, no installer, no DLLs or binaries.
