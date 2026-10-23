# Doom 3 BFG VR ("Fully Possessed")

**Status:** Working. Native ARM64 build against native OpenVR, with the one call the ARM64 bridge cannot convert skipped, at 72 Hz with a Frame layout of its own.

| | |
|---|---|
| Upstream | DOOM-3-BFG-VR by NPi2Loup, https://github.com/NPi2Loup/DOOM-3-BFG-VR, commit 2e7209a. RBDoom3BFG fork, OpenVR (SDK submodule moved to Valve master 0924064, IVRSystem_026), OpenGL |
| Game data | Steam's DOOM 3 BFG Edition `base/` (208200), linked, plus the repo's renderprogs and vr_assets |
| Route | Native ARM64 build (OpenVR, OpenGL via zink). The Proton route was a dead end |
| Steam entry | "Doom 3 BFG VR" 3138655638, native shortcut, no compat tool, VR flag |
| Set up | 2026-10-21 (replaces the 2026-10-06 Proton dead end) |

## What it is

The "Fully Possessed" VR mod for Doom 3 BFG, built on the headset against native ARM64 OpenVR (`/usr/lib/libopenvr_api.so`). It starts, finds the HMD (72 Hz, 1728x1728) and enters its render loop.

## What broke on the Frame

- **Proton/FEX: the OpenVR compositor bridge (dead end, 2026-10-06).** The Windows build (v0.021j, 64-bit) connected to SteamVR and created 2246x2246 buffers, then:

  ```
  fixme:vrclient:set_skybox_override_init Conversion for type 1 is not supported.
  err:msvcrt:_wassert (L"!status",L"../src-vrclient/vrcompositor_manual.c",2264)
  ```

  `neo/vr/Vr.cpp` calls `IVRCompositor::SetSkyboxOverride` with OpenGL textures every time and no cvar disables it. Proton ARM64's compositor bridge has no OpenGL conversion for that call and asserts instead of returning an error. Half-Life: VR Mod hits the identical assertion. GZDoom VR also renders with OpenGL and works because it never calls it.
- **Native OpenVR.** The same `SetSkyboxOverride` call with a GL skybox crashes the native ARM64 vrclient too.
- **Toolchain.** The CMake file adds `-mmmx -msse -msse2` and the code uses SSE intrinsics. GCC 15 defaults to C++17, where this code's `throw()` specs are errors; the hand-rolled precompiled-header commands only see definitions, not `CMAKE_CXX_FLAGS`. `Cinematic.cpp` uses the pre-4.0 FFmpeg API. The OpenVR SDK only puts linux64 on the link path.
- **ARM `char` is unsigned.** The GUI text came out garbled.
- **The mod itself (submit bounds).** The default texture bounds on `Submit` produced "Invalid texture bounds" and no image.
- **The mod itself (input).** VR buttons only reached the menus, not in-game movement and firing, and the face-forward screen did not accept them. A single slot lost presses. Escape (main menu) was only sent on Windows.
- **SteamVR input.** Holding the controller kept triggering the physical grips at Steam's stock 10% threshold. Stick directions re-fired snap turn and weapon switch while held.
- **Debugging.** Plain ptrace attach is blocked.

## The fix

`d3_patch_arm.py` changes, all behind flags or guards and idempotent:

- SSE flags and intrinsics x86-only; an ARM64 `CPUSTRING`; `-std=gnu++14 -fpermissive -w` through `add_definitions`; `-fsigned-char`.
- `SetSkyboxOverride` skipped unless `D3BFGVR_SKYBOX=1`.
- Explicit texture bounds on `Submit`.
- The face-forward screen accepts VR buttons, and VR buttons also feed the polled keyboard list that in-game movement and firing read, through a queue instead of a single slot.
- Stick directions use hysteresis (press 60%, release 30%).

`d3_build.sh` configures with `-DSDL2=ON -DONATIVE=OFF -DFFMPEG=OFF` (cutscenes are skipped), symlinks the ARM64 OpenVR library dir onto the link path, and links with `-Wl,-rpath,$ORIGIN`. gdb works from inside the launch wrapper (`d3_gdb.sh` on the headset, not in this repo).

## Exact commands

The scripts live in this repo under `scripts/doom3-bfg-vr/` and are copied to `~/PCVR/bin/` on the headset (the run script is written into `~/PCVR/D3BFGVR-game/` by `d3_setup.sh`).

```bash
ssh frame "git clone --depth 1 --recurse-submodules https://github.com/NPi2Loup/DOOM-3-BFG-VR.git ~/PCVR/D3BFGVR"
ssh frame "python3 ~/PCVR/bin/d3_patch_arm.py ~/PCVR/D3BFGVR/neo && bash ~/PCVR/bin/d3_build.sh"    # log: ~/PCVR/D3BFGVR/build.log; d3_build.sh clean for a fresh build
ssh frame "bash ~/PCVR/bin/d3_setup.sh"     # builds ~/PCVR/D3BFGVR-game and adds the shortcut if missing
```

`~/PCVR/D3BFGVR-game` holds `Doom3BFGVR`, `base/` (links to the Steam game's base plus the repo's renderprogs, which win over Steam's default.cfg) and "Fully Possessed" (link to the repo's vr_assets). `d3bfgvr-run.sh` sets `SDL_VIDEODRIVER=x11` and runs `./Doom3BFGVR +set fs_basepath "$PWD"`; log `d3bfgvr-last.log`.

## Controls

The game uses legacy OpenVR input, so the layout lives in two places: a SteamVR legacy binding and the mod's own cfg. `d3_frame_binding.py` writes both and selects the binding:

1. `~/PCVR/D3BFGVR-game/d3bfgvr_frame_binding.json`: derived from SteamVR's own Frame legacy binding (`/opt/steamvr/drivers/frame_controller/resources/input/legacy_bindings_frame_controller.json`). Physical grips dropped; bumpers drive the legacy grip button; left d-pad down drives `left_applicationmenu_press`; the duplicate X/Y sources removed.
2. `Fully Possessed/vr_openvr.cfg`: legacy button `JOYn` to game action, executed after `vr_openvr_default.cfg`.
3. Selects the file for `steam.app.3138655638` under `frame_controller_CurrentURL_legacy` in `steamvr.vrsettings` (backup `steamvr.vrsettings.bak-d3bfgvr`).

Run with the game closed, then restart vrserver so it rereads the settings. The on-headset `d3_apply_binding.sh` (not in this repo) quits the game, runs the script and restarts SteamVR.

```bash
ssh frame "python3 ~/PCVR/bin/d3_frame_binding.py"
```

Layout v2:

- Left: stick move, stick click sprint (`_speed`), trigger flashlight (`_impulse16`), bumper jump (`_moveup`), d-pad down main menu (`_impulse40`, Escape, which the mod only sent on Windows). Grip unused.
- Right: trigger fire (`_attack`), stick left/right snap turn (`_impulse35`/`_impulse34`), stick up/down next and previous weapon (`_impulse14`/`_impulse15`) with hysteresis, stick click recenter (`_impulse32`), A crouch hold (`_movedown`), B reload (`_impulse13`), bumper PDA (`_impulse19`). Grip unused.

Deviations from the [standard layout](../../FRAME-LAYOUT.md): left trigger is flashlight rather than the secondary slot; the main menu is on the left d-pad down, not the menu button (predates the menu-button rule); right bumper is PDA; X and Y are unbound; grips unused.

Layout v1, for the record: left grip crouch, left bumper previous weapon, right A jump, right grip PDA. Replaced on 2026-10-21 because the grips kept firing from holding the controller.

## Status and known issues

- Working at 72 Hz, 1728x1728 per eye.
- Cutscenes are skipped (`FFMPEG=OFF`).
- The GL skybox override stays off; `D3BFGVR_SKYBOX=1` re-enables the call and crashes the ARM64 vrclient.
- Main menu is on the left d-pad rather than the menu button.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3138655638; rm -rf ~/PCVR/D3BFGVR ~/PCVR/D3BFGVR-game"
# steamvr.vrsettings backup from the binding step: steamvr.vrsettings.bak-d3bfgvr
```

## Files in this repo

- [d3_patch_arm.py](../../scripts/doom3-bfg-vr/d3_patch_arm.py): idempotent Frame/ARM64 patches to the `neo/` tree.
- [d3_build.sh](../../scripts/doom3-bfg-vr/d3_build.sh): cmake/ninja build with the ARM64 OpenVR library on the link path.
- [d3_setup.sh](../../scripts/doom3-bfg-vr/d3_setup.sh): builds the game folder, writes the run wrapper and adds the shortcut.
- [d3bfgvr-run.sh](../../scripts/doom3-bfg-vr/d3bfgvr-run.sh): the Steam launch wrapper.
- [d3_frame_binding.py](../../scripts/doom3-bfg-vr/d3_frame_binding.py): writes the legacy binding, `vr_openvr.cfg`, and selects the binding in `steamvr.vrsettings`.
- [d3bfgvr_frame_binding.json](../../scripts/doom3-bfg-vr/d3bfgvr_frame_binding.json): the resulting legacy binding file.
- [steam_shortcuts.py](../../scripts/common/steam_shortcuts.py): shared shortcut helper.

## Credits

- DOOM-3-BFG-VR "Fully Possessed" by NPi2Loup, on RBDoom3BFG.
- Valve for OpenVR, SteamVR and the OpenVR SDK.
- This repo holds only patches and scripts. No game data, mod assets or binaries.
