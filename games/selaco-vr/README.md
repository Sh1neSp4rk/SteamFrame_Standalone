# Selaco VR

**Status:** Working — native ARM64 OpenVR build, confirmed in the headset with the standard controller layout on 2026-10-22.

| | |
|---|---|
| Upstream | SelacoVR by emawind84, https://github.com/emawind84/SelacoVR (commit 6e8f7e0, "selacovr2.0"), GZDoom/QuestZDoom-based, OpenVR + OpenGL, GPL-3. Plus ZMusic 1.1.12 and the OpenVR SDK |
| Game data | Selaco (Steam 1592280) on its `v0.89-bf` beta branch. `Selaco.ipk3` is hard-linked into the game folder. The mod is built for that version; the public branch is newer |
| Route | Native ARM64 build (OpenVR, OpenGL via zink). No container, FEX or Proton |
| Steam entry | Non-Steam shortcut "Selaco VR" 3063768737, native (no compat tool), VR flag, red "SELACO VR" art. Runs `~/PCVR/SelacoVR/game/selacovr-run.sh` |
| Set up | 2026-10-22 |

## What it is

SelacoVR is emawind84's VR port of Selaco, built on the QuestZDoom lineage of GZDoom. It talks to SteamVR through OpenVR and renders with OpenGL. Upstream ships it as a Windows 64-bit zip. On the Frame it is compiled from source on the headset itself and runs as a native OpenVR scene application against SteamVR's ARM64 `libopenvr_api.so`.

It is the one Doom-engine VR game on the test headset that runs as a native OpenVR app rather than through Proton. Getting there took five port fixes and a legacy-input binding before the Frame controllers worked.

## What broke on the Frame

- **Proton/FEX: the Windows build dies before it draws a frame.** Under Proton Experimental (ARM64) the engine starts, finds the ipk3 and the mods, opens OpenAL, and about four seconds in throws a C++ exception that ends in `STATUS_NONCONTINUABLE_EXCEPTION`. It happens with `+vr_mode 0` just as much as in VR, so it is the engine under FEX, not the headset. There is no crash dialog and `-stdout` prints nothing through Wine; `WINEDEBUG=+seh,+process` in a Proton log was the only way to see it. The Windows build is parked in `game/windows-build/`.
- **Toolchain (GCC 15, C23 default):** ZWidget uses `uint32_t` without `<cstdint>`; `thirdparty/math/sqrt.c` calls `sqrt()` without `<math.h>`; the lemon and re2c build tools are K&R-era C that C23 rejects.
- **The game/mod itself, input device on POSIX:** the OpenVR joystick lives in `win32/i_openVR.cpp` and plugs into the Win32 `JoyDevices[]` table, so the SDL build had no VR controller input at all.
- **OpenVR C API struct packing:** the port uses OpenVR's C API, and `openvr_capi.h` leaves `VRControllerState_t` at default packing while the Linux runtime fills it 4-byte packed. Every button and axis decoded as zero until the header packed it like the C++ header does.
- **Two VR_Init calls per process:** `SetupOverlay()` called `VR_Init` a second time as an Overlay app. The Linux runtime logged "called VR_Init 2 times", shut the client down, and the next call segfaulted inside `vrclient.so`.
- **SteamVR input, Frame driver quirks:** the Frame driver reports no `Prop_AxisNType`, so the port never found a joystick axis. Poses and controllers were not polled on the title map (Selaco's main menu is a TITLEMAP), so menus were dead until a game started. The menu overlay alternated between eyes, and the 3D scene behind the PDA made it judder.
- **SteamVR input, legacy ids:** SteamVR's simulated Oculus Touch profile (which the stock legacy binding uses) silently drops the axis3/axis4 press ids. The stock legacy layout also folds B, X, Y into one id and both bumpers into the trigger id, which is why the mod's default controls felt half-connected.
- **The mod's VR defaults never applied:** the mod's VR defaults live in a `CVARINFO.vrdefaults` lump this engine build never reads, so Selaco's screen-space effects (dash, dirt, steam, armor overlays, vignette, film grain, momentum HUD) stayed on and painted a translucent box on the HUD plane.

## The fix

`selaco_port.py` is an idempotent patch set, re-applied by `selaco_build.sh` (it restores the files it rewrites from git first):

- **GCC 15 / C23:** `<cstdint>` in ZWidget, `<math.h>` in `thirdparty/math/sqrt.c`, and `-std=gnu89` for the lemon and re2c build tools.
- **CMake:** `win32/i_openVR.cpp` is built on the SDL side and removed from the Win32 list (otherwise `OTHER_SYSTEM_SOURCES` marks it `HEADER_FILE_ONLY`). The SDK's `linuxarm64` directory is picked for aarch64.
- **Input device on POSIX:** `i_openVR.cpp` gets a small `FJoystickCollection` shim, and `posix/sdl/i_joystick.cpp` polls it through `I_OpenVRGetDevices` / `I_OpenVRAddAxes`.
- **Struct packing:** `openvr_capi.h` packs `VRControllerState_t` at 4 bytes on Linux and macOS.
- **One VR_Init per process:** the second `VR_Init(Overlay)` in `SetupOverlay()` is removed. The overlay interface is reachable from the Scene init.
- **Frame quirks in `gl_openvr.cpp`:** the stick (axis 0) is assumed when no joystick axis type is reported; poses and controllers are polled on the title map too; the menu overlay takes the left eye's image only; spare legacy ids (axis2/3/4 press) become `Joy11` to `Joy16` in `joy_mode 1`; a `vr_recenter` console command replaces a TODO; a `vr_debug_buttons` cvar prints the raw button masks when they change.

The build links system SDL2 and OpenAL, a locally built ZMusic 1.1.12 (`zmusic_build.sh`), and OpenVR dynamically (`-DENABLE_OPENVR=ON -DDYN_OPENVR=ON`), with `HAVE_VULKAN` left on.

`frame.cfg` (written by `selaco_binding.py`, exec'd by the launcher on every start) does more work than usual:

- applies the mod's `CVARINFO.vrdefaults` values by hand (the overlays, vignette, film grain, momentum HUD, bloom and lens effects off);
- `use_mode 2` (use by hand aim or view; the mod's hands-only default makes doors miss when the hand is off the panel);
- `vr_overlayscreen 2` (menus and title on a head-locked SteamVR overlay; the default 1 parks it in raw tracking space out of view on the Frame, 0 draws menus in-world);
- pins Selaco's Steam Deck "Quality" preset (`GFXPresetDeckHigh`). `r_thingLOD 1400` keeps the voxel characters; the first-run "Performance" prompt would set 700 and turn them into sprites;
- `vr_joy_mode 1`, `vr_secondary_button_mappings false`, `vr_snapTurn 45`, `vr_two_handed_weapons true`, and all the key binds.

## Exact commands

The scripts live in this repo under `scripts/selaco-vr/` and are copied to `~/PCVR/SelacoVR/` on the headset. The source clone is `~/PCVR/SelacoVR/src`, ZMusic in `~/PCVR/SelacoVR/zmusic`, the OpenVR SDK in `~/PCVR/SelacoVR/openvr`, and the game folder is `~/PCVR/SelacoVR/game`.

```bash
# ZMusic 1.1.12 for ARM64 (system libsndfile/mpg123, dynamic fluidsynth)
ssh frame "bash ~/PCVR/SelacoVR/zmusic_build.sh"

# patch (selaco_port.py) + CMake/Ninja build
ssh frame "bash ~/PCVR/SelacoVR/selaco_build.sh"

# assemble game/: parks the Windows build, copies Selaco, the pk3s, soundfonts, libzmusic.so,
# SteamVR's /opt/steamvr/bin/linuxarm64/libopenvr_api.so, and writes selacovr-run.sh
ssh frame "bash ~/PCVR/SelacoVR/selaco_native_setup.sh"

# write the legacy binding and frame.cfg, then select the binding for the shortcut's app key
ssh frame "python3 ~/PCVR/SelacoVR/selaco_binding.py"
ssh frame "python3 ~/PCVR/bin/vrsettings_bind.py steam.app.3063768737 legacy ~/PCVR/SelacoVR/game/selaco_frame_binding.json"
# then restart the VR session once (drops whoever is in the headset); later edits to the file reload each launch
ssh frame "systemctl --user restart gamescope-session.target"

# patch, build, copy the binary into game/, relaunch through Steam
ssh frame "bash ~/PCVR/SelacoVR/selaco_cycle.sh"
```

`selacovr-run.sh`, the launcher the shortcut runs, sets `LD_LIBRARY_PATH` to the game folder, `SDL_VIDEODRIVER=x11`, unsets `MESA_GL_VERSION_OVERRIDE` / `MESA_GLSL_VERSION_OVERRIDE`, sources `../env.test` if present, and runs:

```bash
./Selaco +logfile selaco.log +vid_preferbackend 0 +vid_vsync false +vr_mode 10 +vid_fullscreen 0 +vid_defwidth 1400 +vid_defheight 1400 "$@"
```

The OpenGL backend, `vr_mode 10` (OpenVR), a 1400x1400 mirror window, and `+exec frame.cfg`. The game folder holds the `Selaco` binary, `qzdoom.pk3`, `lights.pk3`, `brightmaps.pk3`, soundfonts, `fm_banks`, `libzmusic.so`, `libopenvr_api.so` (the port dlopens `$PROGDIR/libopenvr_api.so`), `Selaco.ipk3` (hard link of the `v0.89-bf` ipk3), and `mods/` with `selaco-vr.pk3` and the laser sight, which autoload. Config is `~/.config/selaco-ea/selaco-ea.ini`.

Check it worked:

```bash
ssh frame "grep -a 'Successfully loaded binding' ~/.local/share/Steam/logs/vrserver.txt | tail -1"
ssh frame "grep -a -i 'selaco' ~/.local/share/Steam/logs/vrserver.txt | tail -3"   # VRMsg_Connect from .../game/Selaco (VRApplication_Scene)
ssh frame "touch ~/PCVR/SelacoVR/dev.test"   # next launch logs VRBTN L=... R=... masks to game/selaco.log on every press (stick click = screenshot)
ssh frame "touch ~/PCVR/SelacoVR/gdb.test"   # next launch runs under gdb, batch output in selaco-gdb.log
```

## Controls

Selaco VR uses legacy OpenVR input. The chain is: a legacy binding JSON (`game/selaco_frame_binding.json`) maps each Frame input to one of the eight legacy button ids per hand, the port's `joy_mode 1` code turns ids into gamepad keys (patched so axis2/3/4 press are distinct keys), and `frame.cfg` binds the keys. The binding uses **no** `simulated_controller_type`, because SteamVR's Oculus Touch simulation drops the axis3/axis4 press ids, which is where the menu button, both bumpers and d-pad down had to go. Grips use `click_activate_threshold 0.8` / `click_deactivate_threshold 0.7`.

The layout follows the [standard Frame layout](../../FRAME-LAYOUT.md), confirmed in the headset on 2026-10-22:

| Frame input | Legacy id | Key | Action |
|---|---|---|---|
| Right trigger | right_axis1 | RTrigger | `+attack` (primary fire) |
| Right bumper | right_axis4 | Joy13 | `+altattack` (secondary fire) |
| Right A | right_a | Pad_A | `+use` |
| Right B | right_appmenu | Pad_B | `+reload` |
| Right X | right_axis2 | Joy11 | `Toggle_Flashlight` |
| Right menu | right_axis3 | Joy12 | `menu_main` (pause) |
| Right stick click | right_axis0 | Enter | `vr_recenter` |
| Right stick up/down | (code, 70%) | MWheel | `weapprev` / `weapnext` |
| Right stick left/right | (code) | | snap turn 45° |
| Right grip (80%) | right_grip | LTrigger | `+usereload` (use-or-reload) |
| Right Y | | | unbound (no spare legacy id) |
| Left trigger | left_axis1 | Shift | `+crouch` |
| Left bumper | left_axis4 | Joy16 | `+jump` |
| Left stick click | left_axis0 | Space | `+speed` (sprint) |
| Left grip (80%) | left_grip | | two-handed weapon hold |
| Left d-pad up | left_axis2 | Joy14 | `useGadget` |
| Left d-pad down | left_axis3 | Joy15 | `switchGadget` |
| Left d-pad left | left_a | Pad_X | `useMeds` |
| Left view | left_appmenu | Pad_Y | `codex` (PDA) |
| Left d-pad right | | | unbound |

Deviations from the standard:

- Right bumper is secondary fire and A is use (the user's preference: both fires on the firing hand, primary on the trigger and secondary on the bumper above it).
- Left trigger is crouch, as in the Quake games.
- Right grip (80%) is use-or-reload (`+usereload`), also the user's preference.
- Quick save and quick load were dropped from the controls (they got in the way; the menu has them). Left d-pad up/down are use gadget and switch gadget instead.
- Right Y and left d-pad right are unbound: legacy input has eight ids per hand and the Frame has nine inputs.
- Menus work from the right stick plus A and B in VR. Selaco's UI is mouse-styled, so theater mode also works with the pointer.

## Status and known issues

- Working in the headset with the layout above.
- The ipk3 is pinned to `v0.89-bf`. Steam's public Selaco was switched back to its default branch afterwards, so the hard link is what keeps the old data.
- Right Y and left d-pad right cannot be bound through legacy input.
- Graphics are pinned to the Deck "Quality" preset by `frame.cfg`; the first-run "Performance" prompt would otherwise turn voxel characters into sprites.
- Markers in `~/PCVR/SelacoVR/`: `dev.test` (button-mask log, stick click = screenshot), `gdb.test` (next launch under gdb), `env.test` (sourced by the launcher).

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3063768737; rm -rf ~/PCVR/SelacoVR ~/.config/selaco-ea"
# and remove the steam.app.3063768737 section from ~/.config/openvr/config/steamvr.vrsettings
```

## Files in this repo

- [selaco_port.py](../../scripts/selaco-vr/selaco_port.py): idempotent Linux/ARM64 patches for the SelacoVR source and the OpenVR C API header.
- [selaco_build.sh](../../scripts/selaco-vr/selaco_build.sh): runs the port script, then CMake/Ninja with OpenVR dynamic, system SDL2/OpenAL and the local ZMusic.
- [zmusic_build.sh](../../scripts/selaco-vr/zmusic_build.sh): builds ZMusic 1.1.12 for ARM64 into `~/PCVR/SelacoVR/zmusic/install`.
- [selaco_native_setup.sh](../../scripts/selaco-vr/selaco_native_setup.sh): assembles the game folder from the build and writes `selacovr-run.sh`.
- [selaco_binding.py](../../scripts/selaco-vr/selaco_binding.py): writes the legacy-input binding `selaco_frame_binding.json` and `frame.cfg`.

## Credits

- SelacoVR by emawind84 (QuestZDoom and GZDoom lineage), GPL-3. The patches in `selaco_port.py` modify that code and keep its upstream license.
- Selaco itself (game data from Steam app 1592280, not included).
- ZMusic (the GZDoom music library) and the OpenVR SDK.
- Valve for OpenVR, SteamVR and the Steam Frame.

This repo holds only patches, scripts and configuration. It contains no game data, no mod binaries and no game binaries. Patched upstream code keeps its upstream license (GPL-3 for SelacoVR).
