# Quake II VR

**Status:** Working. Native ARM64 build of Quake-II-PCVR with a GLX OpenXR binding, both expansions, 72 Hz, standard Frame layout.

| | |
|---|---|
| Upstream | Quake-II-PCVR by GameOrDie007, https://github.com/GameOrDie007/Quake-II-PCVR, commit bd161d3. Team Beef's Quake2Quest on Yamagi Quake II, OpenXR, OpenGL |
| Game data | Retail paks, both expansions (xatrix, rogue), soundtrack and Team Beef's HD texture packs from the prepared Windows release folder, hard-linked |
| Route | Native ARM64 build (OpenXR, OpenGL via zink) |
| Steam entry | "Quake II VR" 3173477041, native shortcut, no compat tool, VR flag |
| Set up | 2026-10-22 |

## What it is

Team Beef's Quake2Quest brought to PC VR by GameOrDie007, compiled on the Frame. Both expansions, the soundtrack and the HD texture packs, running at 72 Hz. The earlier sideloaded Windows shortcut ("Quake II VR" pointing at `~/PCVR/Quake2VR/x/quake2-vr-pc`) could not reach VR and was removed; the native build replaced it.

## What broke on the Frame

- **Proton/FEX and wineopenxr.** The Windows build renders with OpenGL and talks OpenXR. wineopenxr only supports D3D11, D3D12 and Vulkan bindings: `wine_xrCreateSession Unhandled graphics binding type: 1000023000` (OpenGL Win32).
- **The port itself (Windows-only seam).** `src/vr/vr_surface.c` creates the session with the Win32 binding and loads GL entry points through `wglGetProcAddress`.
- **The port itself (Unix main loop).** Team Beef's `Qcommon_Init` no longer runs the main loop; only `backends/windows/main.c` had the VR bring-up and frame loop. The engine returned from `main` right after init.
- **ELF symbol interposition.** The `quake2` executable exports `R_SetMode` and friends, and `ref_gl1.so` bound to those instead of its own copies, spinning forever in `R_SetMode`. Windows DLLs never see the executable's symbols; ELF does.
- **OpenGL/zink: black screen on launch.** The shipped `baseq2/config.cfg` asks for `vr_supersampling 2` with `vr_msaa 8`, a 3456x3456 8x multisampled framebuffer the Adreno cannot allocate: `VR: incomplete multisample framebuffer`.
- **OpenGL/zink: right eye unsteady.** SteamVR read the right eye image before zink had finished drawing it. Only the left eye was implicitly flushed by the desktop mirror's swap.
- **Toolchain.** `teambeef/mathlib.c` uses `sincosf` (needs `_GNU_SOURCE`); old duplicate globals need `-fcommon`.
- **Missing tool.** The release's setup generates weapon-wheel icons with Python Pillow, which the Frame does not have.

## The fix

- `q2_port.py` gives `vr_surface.c` an `XR_USE_PLATFORM_XLIB` path: `XrGraphicsBindingOpenGLXlibKHR` from SDL's X11 display and the current GLX context and drawable, GL entry points through `glXGetProcAddressARB`, and the CMake Linux target linked to OpenXR, GL and dl. The Unix `main.c` gets the same VR bring-up and frame loop tail as the Windows one. Idempotent.
- `q2_build.sh` builds with cmake/ninja, `-fcommon -D_GNU_SOURCE`, SteamVR's ARM64 `libopenxr_loader.so` by full path, and `-Wl,-Bsymbolic` on the shared and module linker flags so the `.so` modules bind to their own symbols.
- The on-headset helper `q2_cfgfix.sh` (not in this repo) sets `vr_supersampling 1.0` and `vr_msaa 2` in `baseq2/config.cfg`.
- A `glFinish()` before `xrReleaseSwapchainImage` for the right eye. `glFlush()` is not enough.
- Weapon-wheel icons stay blank.

## Exact commands

The scripts live in this repo under `scripts/quake2-vr/` and are copied to `~/PCVR/Quake2VR/` on the headset (the run script to `~/PCVR/Quake2VR-game/`). Shared helpers are in `scripts/common/` and live in `~/PCVR/bin/`.

```bash
ssh frame "mkdir -p ~/PCVR/Quake2VR && git clone --depth 1 https://github.com/GameOrDie007/Quake-II-PCVR.git ~/PCVR/Quake2VR/src"
ssh frame "bash ~/PCVR/Quake2VR/q2_build.sh"
# cmake/ninja, -fcommon -D_GNU_SOURCE (sincosf), SteamVR's ARM64 libopenxr_loader.so, -Wl,-Bsymbolic on the .so modules
```

`~/PCVR/Quake2VR-game` is a hard-link copy of the prepared Windows release folder's data plus the native `quake2`, `ref_gl1.so`, `ref_soft.so` and `{baseq2,rogue,xatrix}/game.so`. The shortcut runs `q2vr-run.sh` (SDL x11, Mesa override unset, `-portable`), log `q2vr-last.log` (line-buffered through `stdbuf`).

```bash
ssh frame 'python3 ~/PCVR/bin/steam_shortcuts.py add "Quake II VR" /home/steamos/PCVR/Quake2VR-game/q2vr-run.sh /home/steamos/PCVR/Quake2VR-game'
```

Expansions: launch options `+set game xatrix` or `+set game rogue`. A successful VR session logs ` VR: ready`.

## Controls

`q2_binding.py` writes `q2vr_frame_binding.json`, a SteamVR OpenXR binding that maps Frame inputs onto the port's Oculus Touch profile (`/actions/gameplay/in/trigger`, `squeeze`, `a_click`, `b_click`, `x_click`, `y_click`, `menu_click`, `thumbstick`). `vrsettings_bind.py` selects it for `steam.app.3173477041`, and the SteamVR session has to be restarted for a new binding to apply (`systemctl --user restart gamescope-session.target`, never `pkill -9 vrserver`). `vrcmd --set-settings-string` looks like it selects a binding but neither persists nor applies it on the Frame.

```bash
ssh frame "python3 ~/PCVR/Quake2VR/q2_binding.py && python3 ~/PCVR/bin/vrsettings_bind.py steam.app.3173477041 openxr ~/PCVR/Quake2VR-game/q2vr_frame_binding.json"
```

- Left hand: stick move, grip (80%) run, trigger crouch, bumper jump, d-pad left/right help computer / inventory, view menu.
- Right hand: trigger fire, A crouch, B jump, stick turn and weapons, grip weapon wheel, menu.

In the port's code the off-hand squeeze is crouch and the off-hand B is jump, which is why the left trigger drives `squeeze` and the left bumper drives `b_click`.

Deviations from the [standard layout](../../FRAME-LAYOUT.md): left trigger = crouch (Quake II has one; the mod puts it on the off-hand squeeze), left grip = run, d-pad left/right = help computer / inventory, view = menu. The weapon wheel stays on the right grip.

Checking a binding took:

```bash
ssh frame "grep -A3 'steam.app.3173477041' ~/.local/share/Steam/config/steamvr.vrsettings"
ssh frame "grep -E 'interaction_profiles|controller keys' ~/PCVR/Quake2VR-game/q2vr-last.log | head"
```

## Status and known issues

- Working at 72 Hz with the standard layout.
- Weapon-wheel icons are blank (no Pillow on the Frame).
- A black screen on launch means VR setup failed; check `q2vr-last.log` for `VR: incomplete multisample framebuffer` and the supersampling/MSAA values in `baseq2/config.cfg`.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3173477041; rm -rf ~/PCVR/Quake2VR ~/PCVR/Quake2VR-game"
```

## Files in this repo

- [q2_port.py](../../scripts/quake2-vr/q2_port.py): idempotent patch for the Xlib/GLX OpenXR surface, GL entry points and the Unix main loop.
- [q2_build.sh](../../scripts/quake2-vr/q2_build.sh): cmake/ninja build with SteamVR's loader and `-Wl,-Bsymbolic`.
- [q2vr-run.sh](../../scripts/quake2-vr/q2vr-run.sh): the Steam launch wrapper.
- [q2_binding.py](../../scripts/quake2-vr/q2_binding.py): writes the SteamVR OpenXR binding for the Frame layout.
- [q2vr_frame_binding.json](../../scripts/quake2-vr/q2vr_frame_binding.json): the resulting binding file.
- [vrsettings_bind.py](../../scripts/common/vrsettings_bind.py), [steam_shortcuts.py](../../scripts/common/steam_shortcuts.py): shared helpers.

## Credits

- Quake-II-PCVR by GameOrDie007; Quake2Quest by Team Beef; Yamagi Quake II.
- Valve for OpenVR, SteamVR and the OpenXR runtime on the Frame.
- This repo holds only patches and scripts. No game data or binaries.
