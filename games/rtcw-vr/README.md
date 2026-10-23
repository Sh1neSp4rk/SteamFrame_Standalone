# Return to Castle Wolfenstein VR

**Status:** Working. Native ARM64 build of RealRTCW XR; menu, Play and the campaign run in the headset. Controls are still Team Beef's defaults.

| | |
|---|---|
| Upstream | RealRTCWXR by Team Beef, https://github.com/Team-Beef-Studios/RealRTCWXR, commit 77a6fab (RealRTCW XR 0.8.7). ioRTCW/rtcw-sp, OpenXR, OpenGL (rend2). GPL-3 |
| Game data | RealRTCW (free, Steam 1379630) on its `realrtcw5.0` beta branch, plus the original Return to Castle Wolfenstein (9010) single-player paks. 2.9 GB download, 3.3 GB staged |
| Route | Native ARM64 build (OpenXR, OpenGL via zink) |
| Steam entry | "Return to Castle Wolfenstein VR" 3255137504, native shortcut, no compat tool, VR flag, red RTCW VR art |
| Set up | 2026-10-22; controls are Team Beef's defaults |

## What it is

RealRTCW is WolfETPlayer's free single-player overhaul of RTCW: expanded arsenal, new enemies, reworked AI and difficulty, HD assets. Team Beef's XR port builds on RealRTCW 5.0. The Windows project kept its VR layer outside the Makefile, Steam's RealRTCW had moved two versions past what the port expects, and one C99 subtlety broke the game module; all three are fixed and the campaign plays.

## What broke on the Frame

- **The game data (Steam branch).** Steam's default RealRTCW branch is 5.3 now, and its menus call a UI script the 5.0 engine does not have. With default data the Play menu opens dead while Options works, and the log says `unknown UI script loadCampaignArenas`.
- **Steam client (installing).** The install-wizard API (`OpenInstallWizard`) wants two arguments and the second is not a bool. Steam downloads only in bursts while the headset is asleep and shows zero progress (`BytesDownloaded` stays 0 in the appmanifest) until it commits.
- **The port itself (build system).** The VR layer (`code/RealRTCWXR/RealRTCWXR`: OpenXrInput, VrInput*, windows/TBXR_Common, RTCWXR_SurfaceView) lives only in a Visual Studio project; the Makefile never heard of it. The client's `cl_patrons.o` is also missing from the Makefile. The bundled SDL2 is x86-64. The legacy OpenGL 1 renderer target no longer compiles in this fork (`tr_cmds.c` 'eye').
- **The port itself (Windows-only code).** Win32 graphics binding, `GetTickCount64`, `Unknwn.h`/`wglext.h` includes. The two `#ifndef _WIN32` branches in VrInput*.c assume Android. `sdl_glimp.c` only called `VR_Init`/`VR_Shutdown` under `#if defined(_WIN32)`, so the eye buffers were never created and the first frame died on a null `glBindFramebuffer` in `TBXR_prepareEyeBuffer`.
- **The port itself (`-DRTCWXR_CLIENT`).** Under that define `vr` is a struct, and the renderer wants the pointer form, so the define must reach client objects only.
- **Toolchain (GCC 15, GNU C99).** A stale generated prototype in `g_func_decs.h` (`BG_AkimboFireSequence` int) is a hard error. `g_main.c` declared `G_GameSkillIntToStr` plain `inline`: MSVC emits a definition, GNU C99 does not, so `qagame.sp.aarch64.so` loaded with an undefined symbol and the campaign died on "VM_Create on game failed". The client header wants a system `opus/opusfile.h` unless opus is off.
- **Filesystem case.** The engine's base game dir is lowercase `"main"`. A capitalised `Main` folder gave "pak0.pk3 is missing".
- **Process name.** Linux truncates the process name to `RealRTCW.aarch6`, so killing it by exact name fails, and a launch while an old instance lives silently reuses it.
- **Harmless noise.** `xdg-open: cannot execute binary file` (Steam's x86 runtime xdg-open on PATH) and `couldn't exec realrtcwxr.cfg`.

## The fix

- Switch the Steam app to the `realrtcw5.0` beta before anything else. Set its compat tool to `proton-experimental-arm64` first so Steam fetches the Windows depots; only the data is used.
- `rtcw_port.py`, idempotently: compiles the VR sources into the client (objects added to `Q3OBJ` with pattern rules for `code/RealRTCWXR/RealRTCWXR{,/windows}`), with `-DXR_USE_PLATFORM_XLIB -DXR_USE_GRAPHICS_API_OPENGL` and the repo's OpenXR headers, linked to `/opt/steamvr/bin/linuxarm64/libopenxr_loader.so` by full path. `-DRTCWXR_CLIENT` goes to client objects only through a new `XRCLIENT_CFLAGS` in `DO_CC`. `VrCommon.h` uses the windows/ layer on Linux; `TBXR_Common.h` gets X11/GLX includes; `TBXR_Common.c` gets the `XrGraphicsBindingOpenGLXlibKHR` binding (`glXGetCurrentDisplay`/`Drawable`/`Context`) and a `clock_gettime` timer; the Android branches become Android-only; `sdl_glimp.c` calls `VR_Init`/`VR_Shutdown` on Linux too; `cl_patrons.o` is added; the OpenGL 1 renderer target is dropped; the game modules get `-I` for `VrClientInfo.h`; the stale prototype is fixed; `G_GameSkillIntToStr` is un-`inline`d. Gotcha: `patch()` skips when the replacement text is already a substring of the file, so replacements must be distinct.
- `rtcw_build.sh` runs `make` with `USE_INTERNAL_LIBS=0` but the bundled ogg/vorbis/opus/zlib/jpeg sources, `USE_CURL=0`, `USE_CODEC_OPUS=0 USE_VOIP=0`, `-std=gnu99 -fcommon`, and GCC 15's new hard errors downgraded (`-Wno-error=incompatible-pointer-types`, `int-conversion`, `implicit-function-declaration`, `implicit-int`, `return-mismatch`). Output: `RealRTCW.aarch64`, `renderer_sp_rend2_aarch64.so`, `main/{cgame,qagame,ui}.sp.aarch64.so`. Zink exposes `GL_OVR_multiview2`, which the renderer needs.
- `rtcw_setup.sh` builds the game folder with a lowercase `main/` (and a `Main` symlink), removes old pk3 and cfg links first (a Steam update replaces files, and a branch switch can drop pk3s that must not keep loading), hard-links RealRTCW's pk3s and cfgs and RTCW's `pak0`, `sp_pak1`–`4`, and zips `z_zzzRealRTCWXR.pk3` from the repo's `z_zzzRealRTCWXR/` (the job of their `make_z_vr_assets_pk3.bat`).
- The scripts use `pkill -f 'RealRTCW.aarch64 '`.

## Exact commands

The scripts live in this repo under `scripts/rtcw-vr/` and are copied to `~/PCVR/RealRTCWXR/` on the headset (the run script to `~/PCVR/RealRTCWXR-game/`). Shared helpers are in `scripts/common/` and live in `~/PCVR/bin/`.

Data first:

```bash
ssh frame 'python3 ~/PCVR/bin/steam_eval.py "SteamClient.Apps.JoinAppContentBeta(1379630, \"realrtcw5.0\")"'
# the branch list: appDetailsStore.GetAppDetails(1379630).vecBetas
# then: steam steam://install/1379630  on the headset, followed by SteamClient.Installs.ContinueInstall() from steam_eval
```

Build and game folder:

```bash
ssh frame "mkdir -p ~/PCVR/RealRTCWXR && git clone --depth 1 https://github.com/Team-Beef-Studios/RealRTCWXR.git ~/PCVR/RealRTCWXR/src"
ssh frame "bash ~/PCVR/RealRTCWXR/rtcw_build.sh"     # runs rtcw_port.py, then make
ssh frame "bash ~/PCVR/RealRTCWXR/rtcw_setup.sh"     # ~/PCVR/RealRTCWXR-game, 2.4 GB, paks hard-linked
ssh frame 'python3 ~/PCVR/bin/steam_shortcuts.py add "Return to Castle Wolfenstein VR" /home/steamos/PCVR/RealRTCWXR-game/rtcwxr-run.sh /home/steamos/PCVR/RealRTCWXR-game'
```

The on-headset `rtcw_cycle.sh` (not in this repo) chains port, build, relink, the undefined-symbol check on the modules and a relaunch.

`rtcwxr-run.sh` is the usual wrapper (`SDL_VIDEODRIVER=x11`, Mesa override unset, `+set fs_basepath "$PWD" +set fs_homepath "$PWD/home"`), with two optional markers: `env.test` is sourced for test environment (`RTCWXR_DEBUG_INPUT=1` traces every VR key and UI click into the log), and `gdb.test` runs the next launch under gdb into `rtcwxr-gdb.log` (plain ptrace attach is blocked). Log: `rtcwxr-last.log`.

Check it worked:

```bash
ssh frame "grep -a -i 'realrtcw' ~/.local/share/Steam/logs/vrserver.txt | tail -5"
# VRMsg_Connect from RealRTCW; Transition from VRApplication_OpenXRInstance to VRApplication_OpenXRScene
ssh frame "cd ~/PCVR/RealRTCWXR-game/main; for f in *.so; do echo \$f \$(ldd -r \$f | grep -c 'undefined symbol'); done"   # all 0
```

Its SteamVR client log is `xrclient_.txt` (empty executable name).

## Controls

Team Beef's RTCWQuest defaults (`vr_controls` / `weapons_vr.cfg`): right grip weapon wheel, their stick scheme. Same OpenXR action set family as the Quake ports, so the same kind of binding file converts it; the [standard layout](../../FRAME-LAYOUT.md) conversion is the next step and has not been done.

## Status and known issues

- Working: menu, Play and the campaign in the headset (2026-10-22).
- Controls not yet on the standard layout.
- Steam's 5.3 branch is the default; "Verify integrity" keeps the selected branch, but switching back to default re-breaks the Play menu.
- Killing the game by exact name fails (`RealRTCW.aarch6`); use `pkill -f 'RealRTCW.aarch64 '`.
- Shader caches of other games were freed on the headset to make room for the download's staging.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3255137504; rm -rf ~/PCVR/RealRTCWXR ~/PCVR/RealRTCWXR-game"
# RealRTCW itself: uninstall from the library, or set its beta back to None
```

## Files in this repo

- [rtcw_port.py](../../scripts/rtcw-vr/rtcw_port.py): idempotent patch adding the VR layer to the Makefile, the Xlib/GLX binding, the timer, and the GCC 15 and C99 fixes.
- [rtcw_build.sh](../../scripts/rtcw-vr/rtcw_build.sh): the `make` invocation with system SDL2, bundled codecs, no curl and the error downgrades.
- [rtcw_setup.sh](../../scripts/rtcw-vr/rtcw_setup.sh): builds the game folder with hard-linked data and the VR assets pk3.
- [rtcwxr-run.sh](../../scripts/rtcw-vr/rtcwxr-run.sh): the Steam launch wrapper with the `env.test` and `gdb.test` markers.
- [steam_shortcuts.py](../../scripts/common/steam_shortcuts.py), [steam_eval.py](../../scripts/common/steam_eval.py): shared helpers.

## Credits

- RealRTCWXR by Team Beef Studios (GPL-3); RealRTCW by WolfETPlayer; ioRTCW/rtcw-sp.
- Valve for OpenVR, SteamVR and the OpenXR runtime on the Frame.
- This repo holds only patches and scripts. No game data or binaries.
