# Counter-Strike VR (Team Beef CSVR)

**Status:** Working. Team Beef's Quest and Pico port built natively for the Frame's ARM64 Linux, talking to SteamVR's OpenXR runtime directly. Controls and the menu cursor confirmed in the headset on 2026-10-23.

| | |
|---|---|
| Upstream | [Team-Beef-Studios/CSVR](https://github.com/Team-Beef-Studios/CSVR) (main 2eab9ff), a cs16-client fork with submodules: Team Beef's xash3d-fwgs (the engine, with `engine/vr` for OpenXR on Android GLES), mainui_cpp, ReGameDLL_CS (android branch), YaPB bots, MiniUTL, SDL. GPL-3.0 |
| Game data | Counter-Strike (Steam app 10): `Half-Life/cstrike` and `valve`, hard-linked into the game folder, so it takes no extra space and survives a Steam uninstall |
| Route | Native ARM64 build, OpenXR, desktop OpenGL through zink with a GLX binding; no Proton, no FEX |
| Steam entry | Non-Steam shortcut "Counter-Strike VR" 3307658986, native, red "COUNTER-STRIKE VR" art |
| Set up | 2026-10-23 |

## What it is

Counter-Strike 1.6 on the open-source Xash3D FWGS engine with OpenXR, motion-controlled weapons and offline YaPB bots. Team Beef releases it only for Quest and Pico, but the source is public and its VR layer is the same design that ported cleanly for [Quake](../quake-team-beef/).

## What broke on the Frame

- **Android assumptions in the engine's VR code.** The OpenXR session was set up for OpenGL ES through EGL, the instance was created from an Android start-up hook, and VR forced the mobile `gles3compat` renderer (a failed renderer load opens a blocking warning box).
- **SteamVR has no `XR_KHR_composition_layer_cylinder`.** The menus are drawn on a curved cylinder layer.
- **A latent engine crash.** `CL_FindModelIndex` read `cl.models` one entry past the end of its table. On Android the next value happened to be zero; here it was 2, and the client crashed on load.
- **Toolchain.** GCC 15 needs `-std=gnu17`; the client needed its C++ headers ahead of `cl_util.h`'s `min` and `max` macros; the weapon calibration file lived under `/sdcard`; `gitlab.xiph.org` answered 502 for the libogg, opusfile and vorbis submodules.
- **The Frame has inputs the Touch profile lacks.** The game's OpenXR actions follow the Touch controller, which has no bumpers, view button or d-pad. And SteamVR drops a whole custom binding file that names an action missing from the app's suggested bindings: `Loading 0 bindings`, no input, no menu pointer.
- **No text keyboard inside OpenXR on the Frame.** The multiplayer menu's player-name prompt could not be answered (the Quest build uses Android's keyboard).

## The fix

`cs_port.py` patches the engine idempotently (each patch is skipped when its replacement is present):

- **OpenXR:** `XR_KHR_opengl_enable` with `XrGraphicsBindingOpenGLXlibKHR` (GLX display, drawable and context from SDL's X11 window), `apiVersion` 1.0 (SteamVR's version), `xrGetOpenGLGraphicsRequirementsKHR` before the session, the instance created lazily on first use, GL swapchain images; links GL and X11 plus SteamVR's `/opt/steamvr/bin/linuxarm64/libopenxr_loader.so`.
- **Renderer:** VR loads the desktop `gl` renderer (zink). It swaps the window once per eye, so `SDL_GL_SwapWindow` is skipped (`CSVR_DESKTOP_SWAP=1` brings it back). The Android haptics service is stubbed; controller rumble still works.
- **Menu panel:** one flat quad of the arc's width at the arc's distance, shown to both eyes.
- **The crash:** the `CL_FindModelIndex` loop bound.
- **Frame inputs:** new boolean actions `bumper_left`, `bumper_right`, `view_button` and `dpad_up/down/left/right` on spare `ovrButton` bits, with `vr_button_bumper_left/right`, `vr_button_view` and `vr_button_dpad_*` console variables; grips press at 80%. Every new action also gets a Touch suggestion, because SteamVR only learns actions from the game's suggestions.

`cs_port_client.py` fixes the client's header order and moves the calibration file to `cstrike/models/vr_weapons.cfg`. `cs_xiph.sh`, `cs_subfix.sh` and `cs_sub2.sh` fetch the pinned submodule commits, the Xiph ones from the `github.com/xiph` mirrors.

Controls: `cs_controls.py` writes a `frame_controller` binding over SteamVR's auto-generated Touch default and makes it read-only (SteamVR logs "Unable to write" and loads it at the next start, no VR restart), plus `cstrike/frame_controls.cfg`, which the launcher execs every start. The player name: `cs_name.py` writes `cstrike/frame_name.cfg` at every launch from `cstrike/frame_name.txt` if present, else the Steam persona name, else "Player", so the prompt never appears.

## Exact commands

The scripts live in this repo under `scripts/counter-strike-vr/` and are copied to `~/PCVR/CSVR/` on the headset; the source clone goes to `~/PCVR/CSVR/src` and the playable folder is `~/PCVR/CSVR/game`. The shared helpers are in `~/PCVR/bin/`.

```bash
# shallow clone with submodules (about 380 MB), then the pinned nested submodules and the Xiph mirrors
ssh frame "git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/Team-Beef-Studios/CSVR.git ~/PCVR/CSVR/src"
ssh frame "bash ~/PCVR/CSVR/cs_subfix.sh; bash ~/PCVR/CSVR/cs_sub2.sh; bash ~/PCVR/CSVR/cs_xiph.sh"

# engine (waf, -std=gnu17, no software renderer, no VGUI) and the client, menu, ReGameDLL and YaPB (CMake/Ninja); about 5 minutes
ssh frame "bash ~/PCVR/CSVR/cs_build_engine.sh && bash ~/PCVR/CSVR/cs_build_game.sh"

# hard-link Steam's Counter-Strike into game/, copy CSVR's VR models and bot configs over the links, add the shortcut
ssh frame "bash ~/PCVR/CSVR/cs_setup.sh"

# Frame binding over the read-only Touch default, and frame_controls.cfg
ssh frame "python3 ~/PCVR/CSVR/cs_controls.py"

# launch through Steam and summarise the logs; after engine changes that add actions, use cs_rebind.sh instead
ssh frame "bash ~/PCVR/CSVR/cs_launch.sh 40 keep"
ssh frame "bash ~/PCVR/CSVR/cs_rebind.sh"
```

The shortcut runs `game/csvr-run.sh` (written by the setup, not in this repo): `SDL_VIDEODRIVER=x11`, the Mesa GL caps unset, the loader on `LD_LIBRARY_PATH`, then `./xash3d -game cstrike -ref gl -dll dlls/yapb_arm64.so +exec frame_controls.cfg +exec frame_name.cfg`. YaPB loads as the game DLL and loads `cs_arm64.so`. Log: `game/csvr-last.log`. The launch helper kills the game with `-9` because the engine's warning box ignores SIGTERM; that is the game, never vrserver.

## Controls

On the [standard layout](../../FRAME-LAYOUT.md), using every Frame input.

| Hand | Input | Action |
|---|---|---|
| Right | Trigger | Fire (and menu click) |
| Right | Bumper | Secondary fire |
| Right | A | Use |
| Right | B | Reload |
| Right | X | Buy menu |
| Right | Y | Drop |
| Right | Grip (80%) | Last weapon |
| Right | Stick | Left/right snap turn; up/down weapons |
| Right | Stick click | Flashlight |
| Right | Menu | Menu |
| Left | Trigger | Crouch |
| Left | Bumper | Jump |
| Left | Grip (80%) | Walk (hold) |
| Left | Stick | Move |
| Left | Stick click | Night vision |
| Left | View | Scoreboard |
| Left | D-pad up / down | Primary / secondary ammo |
| Left | D-pad left / right | Spray / team menu |

Tap the d-pad: the Frame repeats a held d-pad (see [KNOWN-ISSUES.md](../../KNOWN-ISSUES.md)).

## Status and known issues

- Working with bots offline; controls and the menu cursor confirmed.
- After adding OpenXR actions to the engine, SteamVR's default binding must be regenerated before the Frame binding is locked over it; `cs_rebind.sh` does the two passes.
- The player name comes from a file or the Steam persona name; there is no in-headset keyboard.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3307658986; rm -rf ~/PCVR/CSVR"
# then remove steam.app.3307658986_* from ~/.config/openvr/config/openxr (chmod 644 first)
```

## Files in this repo

- [cs_port.py](../../scripts/counter-strike-vr/cs_port.py): the engine patches (GPL-3.0 like the engine).
- [cs_port_client.py](../../scripts/counter-strike-vr/cs_port_client.py): the client fixes (GPL-3.0).
- [cs_build_engine.sh](../../scripts/counter-strike-vr/cs_build_engine.sh), [cs_build_game.sh](../../scripts/counter-strike-vr/cs_build_game.sh): the two builds.
- [cs_subfix.sh](../../scripts/counter-strike-vr/cs_subfix.sh), [cs_sub2.sh](../../scripts/counter-strike-vr/cs_sub2.sh), [cs_xiph.sh](../../scripts/counter-strike-vr/cs_xiph.sh): submodule fetching at the pinned commits.
- [cs_setup.sh](../../scripts/counter-strike-vr/cs_setup.sh): the game folder and the shortcut.
- [cs_controls.py](../../scripts/counter-strike-vr/cs_controls.py), [cs_name.py](../../scripts/counter-strike-vr/cs_name.py): the binding, `frame_controls.cfg` and the player name.
- [cs_rebind.sh](../../scripts/counter-strike-vr/cs_rebind.sh), [cs_launch.sh](../../scripts/counter-strike-vr/cs_launch.sh), [cs_state.sh](../../scripts/counter-strike-vr/cs_state.sh): rebind, launch and status helpers.

## Credits

- Team Beef for CSVR; the Xash3D FWGS project, mainui_cpp, ReGameDLL_CS and YaPB it builds on (all GPL-3.0). The patches in the two port scripts modify that code and keep its license.
- Valve for Counter-Strike (game data from Steam, not included), OpenXR through SteamVR, and the Steam Frame.
- This repo holds only patches and scripts. No game data, no source clone, no built binaries.
