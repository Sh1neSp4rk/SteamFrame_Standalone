# Quake III VR

**Status:** Working. Native ARM64 build of q3vr; the lightest of the Quake ports and the one that needed the least.

| | |
|---|---|
| Upstream | q3vr by RippeR37, https://github.com/RippeR37/q3vr, commit b55e8d7 (v1.0). PC fork of Quake3Quest, ioquake3, OpenXR, OpenGL |
| Game data | Retail `pak0`–`pak8` hard-linked from Steam's Quake III Arena, plus the port's `pakQ3VR` and `pak8a` |
| Route | Native ARM64 build (OpenXR, OpenGL via zink) |
| Steam entry | "Quake III VR" 3668573126, native shortcut, no compat tool, VR flag |
| Set up | 2026-10-21; controls judged fine as shipped |

## What it is

RippeR37's PC fork of Quake3Quest, compiled on the headset. It needed a double-buffered window and a shim around its vcpkg dependency, and nothing else.

## What broke on the Frame

- **Proton/FEX and wineopenxr.** Like the other Quake ports, OpenGL plus OpenXR cannot be bridged by wineopenxr (`wine_xrCreateSession Unhandled graphics binding type: 1000023000`).
- **Build system.** The project wants OpenXR from vcpkg. The system `libopenxr_loader.a` is LTO-only and unusable, and the bundled SDL binary is x86.
- **OpenGL/zink: single-buffered window.** zink/GLX under gamescope offers no single-buffered fbconfig, so the window request failed with `GLXBadFBConfig`.
- **OpenGL/zink: context version.** q3vr creates a GL 4.6 core context. Steam's game session sets `MESA_GL_VERSION_OVERRIDE=4.3`, which makes core-context creation fail with `GLXBadFBConfig`.
- **Toolchain (GCC 15).** Needs `-std=gnu17`.

## The fix

- `q3_build.sh` skips vcpkg with an empty toolchain file and a hand-written `cmake-shim/OpenXR/OpenXRConfig.cmake` that points `OpenXR::openxr_loader` at `/opt/steamvr/bin/linuxarm64/libopenxr_loader.so` and `OpenXR::headers` at `/usr/include`. System SDL2 (`-DUSE_INTERNAL_SDL=OFF`), `-std=gnu17 -Wno-error`.
- `q3_fixgl.sh` changes `code/sdl/sdl_glimp.c` to request a double-buffered window (`SDL_GL_DOUBLEBUFFER 1`). VR frames go to OpenXR swapchains; the window is only a mirror. It also adds `+set r_ext_multisample 0` to the run script.
- `q3vr-run.sh` sets `SDL_VIDEODRIVER=x11` and unsets `MESA_GL_VERSION_OVERRIDE` and `MESA_GLSL_VERSION_OVERRIDE` so zink's 4.6 context is available.

## Exact commands

The scripts live in this repo under `scripts/quake3-vr/` and are copied to `~/PCVR/Q3VR/` on the headset (the run script to `~/PCVR/Q3VR-game/`).

```bash
ssh frame "mkdir -p ~/PCVR/Q3VR && git clone --depth 1 https://github.com/RippeR37/q3vr.git ~/PCVR/Q3VR/src"
ssh frame "bash ~/PCVR/Q3VR/q3_build.sh"      # cmake/ninja, vcpkg shimmed, system SDL2, gnu17
ssh frame "bash ~/PCVR/Q3VR/q3_fixgl.sh"      # double-buffered window, rebuild, copy q3vr into the game folder
```

`~/PCVR/Q3VR-game` holds `q3vr`, the game `.so` files, the port's `pakQ3VR` and `pak8a`, and the retail `pak0`–`pak8` hard-linked from Steam's Quake 3 Arena (the bundled demo `pak0` was set aside).

```bash
ssh frame 'python3 ~/PCVR/bin/steam_shortcuts.py add "Quake III VR" /home/steamos/PCVR/Q3VR-game/q3vr-run.sh /home/steamos/PCVR/Q3VR-game'
```

The wrapper runs `./q3vr +set fs_basepath "$PWD" +set fs_homepath "$PWD/home" +set r_ext_multisample 0`, log `~/PCVR/Q3VR-game/q3vr-last.log`. A working launch reaches an OpenXR session at 1728x1728 per eye.

## Controls

The port's defaults, judged fine as they are. No Frame binding has been written. See the [standard layout](../../FRAME-LAYOUT.md) for what the other ports use.

## Status and known issues

- Working in VR at 1728x1728 per eye.
- Controls not converted to the standard layout (not needed so far).

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3668573126; rm -rf ~/PCVR/Q3VR ~/PCVR/Q3VR-game"
```

## Files in this repo

- [q3_build.sh](../../scripts/quake3-vr/q3_build.sh): cmake/ninja build with the vcpkg shim pointing at SteamVR's loader.
- [q3_fixgl.sh](../../scripts/quake3-vr/q3_fixgl.sh): the double-buffered window change, rebuild and install into the game folder.
- [q3vr-run.sh](../../scripts/quake3-vr/q3vr-run.sh): the Steam launch wrapper.
- [steam_shortcuts.py](../../scripts/common/steam_shortcuts.py): shared shortcut helper.

## Credits

- q3vr by RippeR37; Quake3Quest by Team Beef; ioquake3.
- Valve for OpenVR, SteamVR and the OpenXR runtime on the Frame.
- This repo holds only patches and scripts. No game data or binaries.
