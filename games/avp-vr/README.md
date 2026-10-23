# Aliens versus Predator VR

**Status:** Working — native ARM64 OpenXR build; the first native port on the test headset and the recipe the Quake ports followed.

| | |
|---|---|
| Upstream | Aliens-Versus-Predator-VR by Bassquake, https://github.com/Bassquake/Aliens-Versus-Predator-VR (commit 6ef4868), OpenXR, OpenGL |
| Game data | Steam's Aliens versus Predator Classic, untouched, reached through lowercase symlinks |
| Route | Native ARM64 build (OpenXR, OpenGL via zink). No container, FEX or Proton |
| Steam entry | Non-Steam shortcut "AvP VR" 4045669378, native (no compat tool), VR flag. Runs `~/PCVR/AVPVR-game/avpvr-run.sh` |
| Set up | 2026-10-20 |

## What it is

Bassquake's VR port of AvP Classic. It renders with OpenGL and talks to the headset through OpenXR. Because it is OpenGL plus OpenXR, it cannot reach VR under Proton on the Frame (Proton's wineopenxr only bridges Direct3D 11, Direct3D 12 and Vulkan bindings), so it was built on the headset as a native linux-arm64 binary. First launch reached an OpenXR session with SteamVR/OpenXR 2.18.2 at 72 Hz, 1728x1728 per eye.

## What broke on the Frame

- **Toolchain (GCC 15):** the C23 default breaks K&R `()` prototypes, and GCC 14+ turned old pointer warnings into errors.
- **OpenXR loader:** the repo bundles only an x64 `libopenxr_loader.so`; there is none for linux-arm64.
- **The game/mod itself, file names:** the game expects lowercase file names, while Steam's AvP Classic install uses mixed case.
- **SteamVR keyboard:** the mod opens SteamVR's keyboard for text entry (`ShowKeyboardForOverlay` on a hidden overlay). The Frame's SteamVR closes it right after opening it: the events are `KeyboardOpened_Global` then `KeyboardClosed`, with no Done or Back, so text fields could never be filled.

## The fix

- `avp_build.sh` adds `-std=gnu17 -fpermissive` to the C flags and copies SteamVR's ARM64 loader from `/opt/steamvr/bin/linuxarm64/libopenxr_loader.so` into `source/extern/OpenXR/lib/linux/arm64/` before configuring with `-DAVP_ENABLE_LINUX=ON -DAVP_ENABLE_PCVR=ON`.
- `avp_lowercase.sh` replaces the folder-level links in `~/PCVR/AVPVR-game` with real lowercase folders whose files are lowercase-named symlinks into the Steam install (`FMVs`, `avp_huds`, `avp_rifs`, `fastfile`, `Text`, plus `language.txt` and `default.cfg`). The Steam install stays untouched.
- `avpvr-run.sh` sets `SDL_VIDEODRIVER=x11` (the OpenXR binding is GLX, so SDL must use X11) and `LD_LIBRARY_PATH` to the game folder with its bundled libs.
- `AVPVR-frame-keyboard.patch` logs the keyboard events and makes `SteamVRKeyboard_Poll` return `-2` when SteamVR drops the keyboard within 3 s, at which point the menu code falls back to the mod's own controller grid. `AVP_NO_STEAMVR_KEYBOARD=1` forces the grid without trying SteamVR's keyboard.

## Exact commands

The scripts live in this repo under `scripts/avp-vr/` and are copied to `~/PCVR/bin/` (build and lowercase scripts) and `~/PCVR/AVPVR-game/` (run wrapper) on the headset. The source clone is `~/PCVR/AVPVR`; the keyboard patch sits at `~/PCVR/AVPVR-frame-keyboard.patch`.

```bash
# build; adds -std=gnu17 -fpermissive for GCC 15 and copies SteamVR's ARM64 libopenxr_loader.so
# log: ~/PCVR/AVPVR/build-arm64vr.log
ssh frame "bash ~/PCVR/bin/avp_build.sh"

# lowercase symlinks into the Steam install; rerun if Steam updates AvP Classic
ssh frame "bash ~/PCVR/bin/avp_lowercase.sh"

# keyboard patch: reapply after pulling upstream, then rebuild and relaunch
ssh frame "cd ~/PCVR/AVPVR && git apply ~/PCVR/AVPVR-frame-keyboard.patch"
ssh frame "cd ~/PCVR/AVPVR && cmake --build .build-linux/arm64vr"
ssh frame "bash ~/PCVR/bin/avp_restart.sh"
```

The game folder `~/PCVR/AVPVR-game/` holds `avpvr_arm64`, the bundled libs and `avpvr-run.sh`. Logs are `avpvr-last.log` and `avp_log.txt` in the game folder. Optional music goes in `cd_tracks/track01.ogg` and so on.

## Controls

The mod's defaults. Not yet reviewed against the [standard Frame layout](../../FRAME-LAYOUT.md).

## Status and known issues

- Working: OpenXR session at 72 Hz, 1728x1728 per eye.
- SteamVR's keyboard does not stay open on the Frame; text entry uses the mod's controller grid through the patch.
- `avp_lowercase.sh` has to be rerun whenever Steam updates AvP Classic.
- Controls have not been converted to the standard layout.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 4045669378; rm -rf ~/PCVR/AVPVR ~/PCVR/AVPVR-game"
```

The Steam AvP Classic install is never modified, so nothing there needs restoring.

## Files in this repo

- [avp_build.sh](../../scripts/avp-vr/avp_build.sh): native ARM64 PCVR build with the GCC 15 flags and SteamVR's OpenXR loader.
- [avp_lowercase.sh](../../scripts/avp-vr/avp_lowercase.sh): lowercase symlink tree over the Steam install.
- [avpvr-run.sh](../../scripts/avp-vr/avpvr-run.sh): launch wrapper the shortcut runs (SDL on X11, bundled libs on the library path).
- [AVPVR-frame-keyboard.patch](../../scripts/avp-vr/AVPVR-frame-keyboard.patch): keyboard-event logging and the fallback to the controller grid when SteamVR drops its keyboard.

## Credits

- Aliens-Versus-Predator-VR by Bassquake (the VR port this build is made from). The keyboard patch modifies that code and keeps its upstream license.
- Aliens versus Predator Classic (game data from Steam, not included).
- Valve for OpenVR, SteamVR, the OpenXR runtime and the Steam Frame.

This repo holds only patches and scripts. It contains no game data, no mod binaries and no game binaries. Patched upstream code keeps its upstream license.
