# Quake (Team Beef port)

**Status:** Working. Native ARM64 build of Quake-PCVR, on the standard Frame layout, holding 72 Hz.

| | |
|---|---|
| Upstream | Quake-PCVR by GameOrDie007, https://github.com/GameOrDie007/Quake-PCVR, commit e7abf81. Team Beef's QuakeQuest game code on the DarkPlaces engine, OpenXR, OpenGL. GPL v2 |
| Game data | Steam's Quake (2310): classic Id1 paks plus the rerelease's hipnotic, rogue, dopa, mg1, mg3, ctf |
| Route | Native ARM64 build (OpenXR, OpenGL via zink) |
| Steam entry | "Quake VR (Team Beef)" 2316100907, native shortcut, no compat tool, VR flag |
| Set up | 2026-10-22; controls on the standard Frame layout, confirmed in the headset the same day |

## What it is

The vanilla Quake experience with motion controls: Team Beef's QuakeQuest game code on DarkPlaces, ported to PC VR over OpenXR by GameOrDie007, compiled for the Frame. Original sounds, original look, a weapon wheel, both mission packs and the 2021 episodes. Of the Quake ports on the Frame this is the one to pick for Quake as it was.

## What broke on the Frame

- **Proton/FEX and wineopenxr.** The Windows release is OpenGL plus OpenXR. Proton's wineopenxr bridges Direct3D 11, Direct3D 12 and Vulkan sessions only; an OpenGL game dies at `wine_xrCreateSession Unhandled graphics binding type: 1000023000`. The earlier sideloaded shortcut was parked for this reason.
- **The port itself (Windows-only seam).** The VR layer creates the OpenXR session with `XrGraphicsBindingOpenGLWin32KHR` using `wglGetCurrentDC` / `wglGetCurrentContext` in `vr_xr.c`, with the platform define in `vr_tbxr.h`. The game-change relaunch (`Host_RelaunchGame_f`) is Windows-only.
- **Toolchain (GCC 15).** C23 is the default and `true`/`false` are keywords; `qtypes.h` defines them. The makefile adds `-msse`/`-msse2` to the software rasteriser.
- **Linker.** `/usr/lib/libopenxr_loader.a` is a 14 KB stub, and `sdl2-config --libs` puts `-L/usr/lib` first, so `-lopenxr_loader` picked the stub and every `xr*` symbol came back undefined.
- **SteamVR input.** The port's OpenXR action names are its own (`joystick`, `touchpad`, `gripvalue`, `akey`/`bkey`/`xkey`/`ykey`, `backkey`), not Quake II's, which cost one false start. SteamVR needed one VR session restart before it honoured the selected binding.
- **The port itself (input bugs).** Haptic timing kept float milliseconds since the epoch, which never advance, so a quick save's buzz never stopped. The left hand's A action was not read, so the left bumper could not jump.
- **Missing tool.** The port's `tools/setup.py` generates menu artwork for the game-select page with Python Pillow, which the Frame does not have.

## The fix

- `q1pc_port.py` patches `vr_tbxr.h` (`XR_USE_PLATFORM_XLIB`, X11/GLX headers) and `vr_xr.c` (`XrGraphicsBindingOpenGLXlibKHR` from `glXGetCurrentDisplay` / `glXGetCurrentDrawable` / `glXGetCurrentContext`). Everything else already goes through SDL. The patch is idempotent so it survives a `git pull`.
- The same script fixes `vr_input.c`: haptic timing in double, and the left hand's A action read as the right A so the left bumper jumps and selects.
- `q1pc_build.sh` drives DarkPlaces' own makefile with `CFLAGS_SSE=` and `CFLAGS_SSE2=` emptied (the SSE code itself is guarded), `-std=gnu99 -fcommon -Wno-error`, and SteamVR's loader linked by full path with an rpath.
- Expansions launch with `-game` instead of from the menu.
- Menu artwork is skipped; the menus work without it.
- `id1/autoexec.cfg` sets `vr_supersampling 1` and `vr_msaa 1`. Note from the log: `vr_supersampling` in autoexec does not apply because the eye size is read before the configs; the port runs at its default 1.3x (2246x2246 per eye) and still holds 72 Hz.

## Exact commands

The scripts live in this repo under `scripts/quake-team-beef/` and are copied to `~/PCVR/QuakePCVR/` on the headset. Shared helpers (`steam_shortcuts.py`, `vrsettings_bind.py`) are in `scripts/common/` and live in `~/PCVR/bin/`.

```bash
ssh frame "mkdir -p ~/PCVR/QuakePCVR && git clone --depth 1 https://github.com/GameOrDie007/Quake-PCVR.git ~/PCVR/QuakePCVR/src"
# q1pc_port.py patches vr_tbxr.h and vr_xr.c; q1pc_build.sh runs it first
ssh frame "bash ~/PCVR/QuakePCVR/q1pc_build.sh"
```

What the build script passes to DarkPlaces' makefile:

```bash
make sdl-release -j6 DP_MAKE_TARGET=linux DP_SOUND_API=SDL SDL_CONFIG=sdl2-config \
  CFLAGS_EXTRA="-std=gnu99 -fcommon -Wno-error" CFLAGS_SSE= CFLAGS_SSE2= \
  LDFLAGS_LINUXSDL='$(LDFLAGS_UNIXCOMMON) -lrt -ldl $(LDFLAGS_UNIXSDL) /opt/steamvr/bin/linuxarm64/libopenxr_loader.so -Wl,-rpath,/opt/steamvr/bin/linuxarm64 -lGL -lX11'
```

Result: `darkplaces-sdl`, a 3.9 MB ARM64 binary linked to SDL2, libGL and SteamVR's loader.

Game folder. `q1pc_setup.sh` hard-links the classic `Id1/PAK0.PAK` and `PAK1.PAK` as lowercase `id1/pak0.pak` and `pak1.pak` plus the rerelease expansion paks first, so the port's `tools/setup.py` finds them in place and copies only what it must (Dawn of the Machine, 0.5 GB). It also writes the run wrapper.

```bash
ssh frame "bash ~/PCVR/QuakePCVR/q1pc_setup.sh"
# ~/PCVR/QuakePCVR-game: darkplaces-sdl, id1/, hipnotic/, rogue/, dopa/, mg1/, mg3/, ctf/, q1pc-run.sh
```

`q1pc-run.sh` is the standard wrapper (`SDL_VIDEODRIVER=x11`, Mesa override unset) running `./darkplaces-sdl -basedir . -nohome "$@"`, log in `q1pc-last.log`.

Steam entry and launch (the on-headset helper `q1pc_launch.sh` adds the shortcut once, launches through Steam and prints the log; it is not in this repo):

```bash
ssh frame 'python3 ~/PCVR/bin/steam_shortcuts.py add "Quake VR (Team Beef)" /home/steamos/PCVR/QuakePCVR-game/q1pc-run.sh /home/steamos/PCVR/QuakePCVR-game'
```

Expansions: add `-game hipnotic`, `-game rogue`, `-game dopa`, `-game mg1`, `-game mg3` or `-game ctf` to the shortcut's launch options (or make a second shortcut per episode). `-novr` runs it flat.

Check it worked, in `~/PCVR/QuakePCVR-game/q1pc-last.log`:

```
VR: runtime SteamVR/OpenXR 2.18.2
VR: runtime recommends 1728x1728 per eye
VR: eye framebuffer 1728x1728, 1 samples, 3 swapchain images
VR: session begun (active)
VR: session active at 72Hz
```

## Controls

The port uses Team Beef's OpenXR action set and the Oculus Touch interaction profile, so a SteamVR OpenXR binding file maps the Frame controllers onto it. `q1pc_binding.py` writes `q1pc_frame_binding.json` into the game folder; `vrsettings_bind.py` selects it for `steam.app.2316100907` in `steamvr.vrsettings`, then the VR session has to be restarted once (`systemctl --user restart gamescope-session.target`, which drops whoever is in the headset). Grips are trigger-mode `click` sources at 0.8/0.7; button mode ignored the thresholds.

```bash
ssh frame "python3 ~/PCVR/QuakePCVR/q1pc_binding.py && python3 ~/PCVR/bin/vrsettings_bind.py steam.app.2316100907 openxr ~/PCVR/QuakePCVR-game/q1pc_frame_binding.json"
```

| Left hand | Right hand |
|---|---|
| Stick: move (controller-oriented, the port's own) | Trigger: fire |
| Trigger: run (Quake has no crouch) | Grip (80%): weapon wheel, hold, point, release |
| Grip (80%): two-hand weapon hold | A: jump (select in menus); Y: jump |
| Bumper: jump | B: menu back; X and bumper: unbound (no use key) |
| D-pad up / down: quick save / quick load | Stick: snap turn 45°; up/down = weapons if the wheel is off (`vr_weaponwheel 0`) |
| View: menu | Stick click: laser-sight cycle (the port has no recenter); Menu: pause |

Deviations from the [standard layout](../../FRAME-LAYOUT.md): left trigger is run (the crouch slot; Quake has no crouch), so there is no sprint on the left stick click; right stick click is laser-sight cycle because the port has no recenter; right bumper and X are unbound because there is no use key; movement is controller-oriented, not head-oriented; right grip keeps the port's weapon wheel.

Game side, in `id1/autoexec.cfg`: `vr_yawmode 1`, `cl_comfort 45`, `vr_quicksave 1`, `vr_weaponwheel 1`, `bind / "impulse 12"`, `bind # "impulse 10"` (weapon previous and next).

Checking a binding took:

```bash
ssh frame "grep -A3 'steam.app.2316100907' ~/.local/share/Steam/config/steamvr.vrsettings"
ssh frame "grep -E 'interaction_profiles|controller keys' ~/PCVR/QuakePCVR-game/q1pc-last.log | head"
```

## Status and known issues

- Working and confirmed in the headset on 2026-10-22 at 72 Hz.
- No menu artwork on the game-select page (no Pillow on the Frame).
- Game switching from the menu is Windows-only in this port; use `-game`.
- `vr_supersampling` in autoexec.cfg is ignored (eye size read before configs). The port runs at 1.3x.
- `vrcmd --set-settings-string` does not persist or apply a binding on the Frame; use `vrsettings_bind.py` and restart the VR session.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 2316100907; rm -rf ~/PCVR/QuakePCVR ~/PCVR/QuakePCVR-game"
```

## Files in this repo

- [q1pc_port.py](../../scripts/quake-team-beef/q1pc_port.py): idempotent patch for the Xlib/GLX OpenXR binding, haptic timing and the left-hand A action.
- [q1pc_build.sh](../../scripts/quake-team-beef/q1pc_build.sh): runs the port script and builds `darkplaces-sdl` with DarkPlaces' makefile.
- [q1pc_setup.sh](../../scripts/quake-team-beef/q1pc_setup.sh): builds the game folder (hard-linked paks, the port's setup.py, the run wrapper).
- [q1pc-run.sh](../../scripts/quake-team-beef/q1pc-run.sh): the Steam launch wrapper.
- [q1pc_binding.py](../../scripts/quake-team-beef/q1pc_binding.py): writes the SteamVR OpenXR binding for the Frame layout.
- [q1pc_frame_binding.json](../../scripts/quake-team-beef/q1pc_frame_binding.json): the resulting binding file.
- [vrsettings_bind.py](../../scripts/common/vrsettings_bind.py), [steam_shortcuts.py](../../scripts/common/steam_shortcuts.py): shared helpers.

## Credits

- Quake-PCVR by GameOrDie007; QuakeQuest by Team Beef; DarkPlaces engine. The port is GPL v2.
- Valve for OpenVR, SteamVR and the OpenXR runtime on the Frame.
- This repo holds only patches and scripts. No game data or binaries.
