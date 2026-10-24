# Jedi Academy VR and Jedi Outcast VR (JKXRL)

**Status:** Working. A native ARM64 build of Patola's Linux fork of Team Beef's JKXR. Academy runs smooth; Outcast is "not perfect but good enough to play". Set up and confirmed on 2026-10-23.

| | |
|---|---|
| Upstream | [Patola/JKXRL](https://github.com/Patola/JKXRL) (main 8bb830e, 2026-10-03), the Linux Vulkan fork of Team Beef's JKXR on OpenJK: Vulkan + OpenXR (`XR_KHR_vulkan_enable2`), GPL-2.0. Its only release is x86-64; it had never been built for ARM. SDL 3.4.18 built into a private prefix |
| Game data | Jedi Academy (Steam 6020) and Jedi Outcast (Steam 6030), `base/*.pk3` hard-linked from the Steam folders |
| Route | Native ARM64 build, Vulkan on Turnip, OpenXR through SteamVR's loader; no Proton, no FEX |
| Steam entries | Non-Steam shortcuts "Jedi Academy VR" 2265637930 and "Jedi Outcast VR" 2719912217, native, red art |
| Set up | 2026-10-23 |

## What it is

Team Beef's JKXR puts both Jedi Knight games in VR with motion-tracked sabers, Force gestures and selection wheels. JKXRL swaps its renderer for Vulkan and talks to OpenXR directly, with the single-player engines, renderers and game modules for both games in one tree.

## What broke on the Frame

- **The OpenXR loader.** CMake found `/usr/lib/libopenxr_loader.a`, the unusable LTO-only static archive, and the renderer loaded with undefined `xr*` symbols. Everything else compiled unchanged on the first try.
- **See-through menus.** The menu quad used `XR_COMPOSITION_LAYER_BLEND_TEXTURE_SOURCE_ALPHA_BIT`, and SteamVR honours the menu art's alpha, so dark parts of the menus showed the world through them ("green screen").
- **Multi-draw indirect.** The renderer batches level geometry into indirect multi-draws. On the Frame's Turnip driver that cost about 80 ms a frame: Academy's `t1_sour` ran at 10 to 12 fps.
- **Tiled rendering in Outcast's heavy scenes.** `kejim_post` draws 300 to 1,800 models a frame, and in the GPU's normal tiled (GMEM) mode each draw cost 40 to 50 µs, so the heaviest moments ran at 13 to 20 fps.
- **Touch assumptions in the controls.** JKXR's gestures are tied to the off-hand trigger and the grips; the Frame has bumpers, a d-pad, a view button and right-hand X and Y that the Touch profile does not carry, and the standard layout puts crouch on the left trigger.

## The fix

`jk_port.py` patches the tree idempotently and `jk_build.sh` applies it before every build:

- **Loader:** `-DOPENXR_LOADER_LIBRARY=/opt/steamvr/bin/linuxarm64/libopenxr_loader.so` with an rpath.
- **Menus:** the panel is opaque (`JKXR_SCREEN_ALPHA=1` restores the blend).
- **Multi-draw indirect off** by default (`JKXR_NO_MDI=1`): the renderer's existing non-indirect path takes about 5 ms at full resolution.
- **Per-game tiling mode:** `TU_DEBUG=sysmem` (render straight to memory) brought Outcast's heavy scene from 48 ms to 11 ms (max 98 to 22) but slows Academy's `t1_sour` from 5 to 12 ms, so each game's `run.sh` sets `JKXR_SYSMEM=1` for Outcast and `0` for Academy.
- **`JKXR_RES_SCALE`** scales the recommended eye size (1728x1728). Resolution was not the cost; it stays at 1.0.
- **Not the problem:** compute skinning off (worse with sysmem), `r_lodbias`, effects, vegetation, fog and anisotropy off, resolution 0.65 to 0.8 all changed little or nothing. Every measurement was taken with the headset worn, from the renderer's own `r_vulkanTiming` output.
- **Controls:** the renderer gains OpenXR actions `frame_bumper`, `frame_dpad_*`, `frame_view`, `frame_x` and `frame_y`, each with a Touch suggestion so SteamVR knows them (the simple profile is no longer suggested, keeping the input context at one profile; `JKXR_SIMPLE_PROFILE=1` brings it back), reported on spare button bits. The client's `CL_FrameLayoutTranslate` (`cl_main.cpp`, `vr_frame_layout 1`, right-handed scheme) rebuilds JKXR's Touch-style state from them, so the Force gestures, saber swings and both wheels keep working. `jk_controls.py` writes the `frame_controller` binding over SteamVR's read-only Touch default for both apps.

## Exact commands

The scripts live in this repo under `scripts/jedi-knight-vr/` and are copied to `~/PCVR/JKXR/` on the headset; the clones go to `~/PCVR/JKXR/src` and `sdl3-src`, the playable folders are `~/PCVR/JKXR/jka` and `jko`. Shared helpers are in `~/PCVR/bin/`.

```bash
# shallow clones of JKXRL and SDL release-3.4.18
ssh frame "bash ~/PCVR/JKXR/jk_clone.sh"

# SDL 3 into a private prefix, then the native build (CMake/Ninja; both engines, renderers and game modules)
ssh frame "bash ~/PCVR/JKXR/jk_sdl3.sh && bash ~/PCVR/JKXR/jk_build.sh"

# install into jka/ and jko/, hard-link the Steam pk3s, write run.sh, add both shortcuts
ssh frame "bash ~/PCVR/JKXR/jk_setup.sh"

# Frame bindings for both apps over the read-only Touch defaults; after engine changes that add actions, jk_rebind.sh
ssh frame "python3 ~/PCVR/JKXR/jk_controls.py"
ssh frame "bash ~/PCVR/JKXR/jk_rebind.sh"

# launch through Steam and summarise the logs (jka or jko)
ssh frame "bash ~/PCVR/JKXR/jk_launch.sh jko 40 keep"

# timed run with the renderer's GPU timing, headset worn
ssh frame "GAME=jko MAP=kejim_post bash ~/PCVR/JKXR/jk_trial.sh test '' '' 1.0 150"
```

`run.sh` (written by the setup, not in this repo) sets `SDL_VIDEODRIVER=x11`, puts the private SDL 3 and SteamVR's loader on `LD_LIBRARY_PATH`, applies the per-game `JKXR_SYSMEM` default and sources `env.test` for `JKXR_RES_SCALE` and `JK_ARGS`. Logs: `jka/last.log` and `jko/last.log`; saves and config under `~/.local/share/openjk` and `openjo`. Performance tools: `jk_sweep.sh` (resolution sweep), `jk_bisect.sh` (cumulative feature bisect), `jk_heavy*.sh` (Outcast heavy-scene comparisons); all need the headset worn.

## Controls

On the [standard layout](../../FRAME-LAYOUT.md), with JKXR's motion features kept. Force moved from the left trigger to the left grip because the standard puts crouch on that trigger.

| Hand | Input | Action |
|---|---|---|
| Right | Trigger | Fire, saber |
| Right | Bumper | Alt-fire (saber on/off) |
| Right | Grip (80%) | Weapon wheel |
| Right | A | Use |
| Right | B | Force wheel (the left stick picks) |
| Right | X | Saber style (`saberAttackCycle`) |
| Right | Y | Console (hold) or back |
| Right | Stick | Snap turn |
| Right | Stick click | Next item |
| Right | Menu | Menu |
| Left | Trigger | Crouch |
| Left | Bumper | Jump |
| Left | Grip (80%) | Use Force, with the hand gestures |
| Left | Stick | Move |
| Left | Stick click | Use item |
| Left | View | Datapad |
| Left | D-pad up / down | Quick save / quick load |
| Left | D-pad left / right | Previous / next Force power |

Tap the d-pad: each d-pad action fires at most once a second, because a held Frame d-pad repeats (see [KNOWN-ISSUES.md](../../KNOWN-ISSUES.md)).

## Status and known issues

- Academy smooth; Outcast's heaviest scenes still peak around 22 ms with sysmem rendering.
- The two driver behaviours (multi-draw indirect, tiled rendering cost per draw) are Turnip findings worth a report; see KNOWN-ISSUES.
- After adding OpenXR actions, SteamVR's defaults must be regenerated before the Frame bindings are locked over them; `jk_rebind.sh` does both games.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 2265637930; python3 ~/PCVR/bin/steam_shortcuts.py remove 2719912217; rm -rf ~/PCVR/JKXR"
# then remove steam.app.2265637930_* and steam.app.2719912217_* from ~/.config/openvr/config/openxr (chmod 644 first)
```

## Files in this repo

- [jk_port.py](../../scripts/jedi-knight-vr/jk_port.py): the engine, renderer and client patches (GPL-2.0 like JKXRL).
- [jk_clone.sh](../../scripts/jedi-knight-vr/jk_clone.sh), [jk_sdl3.sh](../../scripts/jedi-knight-vr/jk_sdl3.sh), [jk_build.sh](../../scripts/jedi-knight-vr/jk_build.sh): clone, SDL 3, build.
- [jk_setup.sh](../../scripts/jedi-knight-vr/jk_setup.sh): the two game folders and shortcuts.
- [jk_controls.py](../../scripts/jedi-knight-vr/jk_controls.py), [jk_rebind.sh](../../scripts/jedi-knight-vr/jk_rebind.sh): the Frame bindings and the regenerate-and-lock cycle.
- [jk_launch.sh](../../scripts/jedi-knight-vr/jk_launch.sh), [jk_trial.sh](../../scripts/jedi-knight-vr/jk_trial.sh), [jk_sweep.sh](../../scripts/jedi-knight-vr/jk_sweep.sh), [jk_bisect.sh](../../scripts/jedi-knight-vr/jk_bisect.sh), [jk_heavy.sh](../../scripts/jedi-knight-vr/jk_heavy.sh), [jk_heavy2.sh](../../scripts/jedi-knight-vr/jk_heavy2.sh), [jk_heavy3.sh](../../scripts/jedi-knight-vr/jk_heavy3.sh): launch and performance tools.
- [scripts/common/make_portrait.ps1](../../scripts/common/make_portrait.ps1): builds a portrait capsule from Steam's cached hero and header for games that have none.

## Credits

- Patola for JKXRL; Team Beef for JKXR; the OpenJK project (all GPL-2.0). The patches in `jk_port.py` modify that code and keep its license.
- Raven Software and LucasArts for Jedi Academy and Jedi Outcast (game data from Steam, not included).
- Valve for SteamVR and the Steam Frame; the Mesa Turnip driver project.
- This repo holds only patches and scripts. No game data, no source clones, no built binaries.
