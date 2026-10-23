# Scripts

Everything here ran on the test headset as the `steamos` user. The shared helpers live in `~/PCVR/bin/` there; each port keeps its scripts beside its source in `~/PCVR/<Port>/` and its launch wrapper in the playable folder `~/PCVR/<Port>-game/`. Paths inside the scripts follow that convention. Copy a folder to the headset with `scp -r scripts/<slug> frame:PCVR/<Port>` and read the game's README under [games/](../games/) first.

Every script starts with a comment or docstring saying what it does. Python scripts that only read untrusted files are run with `python3 -I`. Scripts marked **GPL** or **MPL-2.0** patch or embed fragments of a project under that license and are offered under it; the rest are MIT like the repository.

## common/ (`~/PCVR/bin/`)

| Script | What it does |
|---|---|
| [steam_shortcuts.py](common/steam_shortcuts.py) | Adds, lists, removes and stops non-Steam shortcuts through the Steam client's CEF debug port (127.0.0.1:8080 on the headset), with the VR flag and a "PC VR ports" collection; `gameid` converts an appid to the id `steam://rungameid/` wants. Adapted from Frame Control (MIT). |
| [steam_eval.py](common/steam_eval.py) | Runs one JavaScript expression in the Steam client (launch options, compat tools, beta branches, artwork, starting and stopping games). |
| [vrsettings_bind.py](common/vrsettings_bind.py) | Selects a SteamVR controller binding for an app by writing `steamvr.vrsettings` (legacy, OpenXR or SteamVR Input). `vrcmd --set-settings-string` does not persist on the Frame. Restart the VR session afterwards. |
| [apply_art.py](common/apply_art.py) | Applies `<id>p.png`, `<id>.png`, `<id>_hero.png`, `<id>_logo.png` as a game's library art without restarting Steam. |
| [art_inventory.py](common/art_inventory.py) | Lists shortcuts and Steam apps with launch options, and which library art is cached for each. |
| [make_vrart.ps1](common/make_vrart.ps1) | Windows PowerShell: builds red-labelled "GAME VR" library art (capsule, header, hero, logo) from Steam's cached art, for the VR entries. |
| [flatvr-launch.sh](common/flatvr-launch.sh) | Launch-option wrapper that runs a modded Steam game flat unless `-frame-vr` is on the command line, so one install gets a flat library entry and a "Game VR" shortcut. |
| [flatvr_setup.sh](common/flatvr_setup.sh) | Applies that split to DUSK, Left 4 Dead 2, Portal 2 and Bendy. |

## Per game

### gzdoom-vr ([games/gzdoom-vr](../games/gzdoom-vr/))

| Script | What it does |
|---|---|
| [gz_grip.sh](gzdoom-vr/gz_grip.sh) | Writes a copy of SteamVR's stock Frame legacy binding with the grip press raised to 80% (release below 70%) and selects it for the Heretic and Hexen shortcuts. |
| [gzdoomvr_frame_binding.json](gzdoom-vr/gzdoomvr_frame_binding.json) | The resulting legacy binding. |
| [hh_setup.sh](gzdoom-vr/hh_setup.sh) | Copies the DOS WADs from the "Heretic + Hexen" rerelease into the GZDoomVR folder and adds the three shortcuts. |
| [hexw_install.sh](gzdoom-vr/hexw_install.sh) | Adds Ermac's Hexen VR weapons pk3 to both Hexen entries. |
| [make_vrweapons_myhouse.py](gzdoom-vr/make_vrweapons_myhouse.py) | Generates a MODELDEF overlay so MyHouse's renamed weapon classes get the WeaponsForVR 3D models. |

### quake-team-beef ([games/quake-team-beef](../games/quake-team-beef/))

| Script | What it does |
|---|---|
| [q1pc_port.py](quake-team-beef/q1pc_port.py) | **GPL.** Idempotent Linux patches for Quake-PCVR: the Xlib/GLX OpenXR binding in place of Win32, haptic timing in double, the left-hand A action. |
| [q1pc_build.sh](quake-team-beef/q1pc_build.sh) | Builds DarkPlaces in-tree for ARM64 with SDL2 and SteamVR's OpenXR loader linked by path. |
| [q1pc_setup.sh](quake-team-beef/q1pc_setup.sh) | Assembles the game folder: hard-links Steam's Quake paks, then runs the port's own setup.py. |
| [q1pc_binding.py](quake-team-beef/q1pc_binding.py) | Writes the standard Frame layout as a SteamVR OpenXR binding on the port's action names. |
| [q1pc_frame_binding.json](quake-team-beef/q1pc_frame_binding.json) | The resulting binding. |
| [q1pc-run.sh](quake-team-beef/q1pc-run.sh) | Launch wrapper (X11, Mesa override unset, log). |

### quake2-vr ([games/quake2-vr](../games/quake2-vr/))

| Script | What it does |
|---|---|
| [q2_port.py](quake2-vr/q2_port.py) | **GPL.** Idempotent Linux patches for Quake-II-PCVR: Xlib/GLX OpenXR binding, VR bring-up and frame loop in the Unix main, glFinish before swapchain release. |
| [q2_build.sh](quake2-vr/q2_build.sh) | cmake/ninja build with `-Wl,-Bsymbolic` on the modules and SteamVR's loader. |
| [q2_binding.py](quake2-vr/q2_binding.py) | Writes and selects the Frame layout as a SteamVR OpenXR binding. |
| [q2vr_frame_binding.json](quake2-vr/q2vr_frame_binding.json) | The resulting binding. |
| [q2vr-run.sh](quake2-vr/q2vr-run.sh) | Launch wrapper. |

### quake3-vr ([games/quake3-vr](../games/quake3-vr/))

| Script | What it does |
|---|---|
| [q3_build.sh](quake3-vr/q3_build.sh) | Builds q3vr with cmake/ninja, shimming its vcpkg OpenXR dependency to SteamVR's loader. |
| [q3_fixgl.sh](quake3-vr/q3_fixgl.sh) | **GPL.** Switches the mirror window to double buffering (zink under gamescope has no single-buffered fbconfig) and rebuilds. |
| [q3vr-run.sh](quake3-vr/q3vr-run.sh) | Launch wrapper. |

### quakevr-unleashed ([games/quakevr-unleashed](../games/quakevr-unleashed/))

| Script | What it does |
|---|---|
| [q1_port.py](quakevr-unleashed/q1_port.py) | **GPL.** Routes the SSE/AVX intrinsics through SIMDe on ARM and keeps the AVX target attribute x86-only. |
| [q1_build.sh](quakevr-unleashed/q1_build.sh) | clang build with a pkg-config shim to SteamVR's loader and the repo's OpenXR 1.1.63 headers. |
| [quakevr-run.sh](quakevr-unleashed/quakevr-run.sh) | Launch wrapper setting `QVR_GLSAFE_OFF=2` (no bindless textures) and `QVR_XR_SYNC=2` (glFinish per eye). |

### rtcw-vr ([games/rtcw-vr](../games/rtcw-vr/))

| Script | What it does |
|---|---|
| [rtcw_port.py](rtcw-vr/rtcw_port.py) | **GPL.** Adds Team Beef's Windows-only VR layer to the Makefile client, swaps the Win32 binding for Xlib/GLX, fixes the `inline` game-module symbol. |
| [rtcw_build.sh](rtcw-vr/rtcw_build.sh) | make with system SDL2, bundled codecs, no curl. |
| [rtcw_setup.sh](rtcw-vr/rtcw_setup.sh) | Assembles the game folder from RealRTCW (branch `realrtcw5.0`) and RTCW paks, zips the VR assets pk3. |
| [rtcwxr-run.sh](rtcw-vr/rtcwxr-run.sh) | Launch wrapper with `env.test` and `gdb.test` markers. |

### doom3-bfg-vr ([games/doom3-bfg-vr](../games/doom3-bfg-vr/))

| Script | What it does |
|---|---|
| [d3_patch_arm.py](doom3-bfg-vr/d3_patch_arm.py) | **GPL.** Idempotent ARM64 patches for DOOM-3-BFG-VR: SSE x86-only, `SetSkyboxOverride` skipped, signed char, submit bounds, VR buttons into the polled key list. |
| [d3_build.sh](doom3-bfg-vr/d3_build.sh) | cmake/ninja build against native OpenVR. |
| [d3_setup.sh](doom3-bfg-vr/d3_setup.sh) | Assembles the game folder with links to Steam's base files and the mod's assets. |
| [d3_frame_binding.py](doom3-bfg-vr/d3_frame_binding.py) | Writes the SteamVR legacy binding and the mod's `vr_openvr.cfg`, and selects the binding. |
| [d3bfgvr_frame_binding.json](doom3-bfg-vr/d3bfgvr_frame_binding.json) | The resulting binding. |
| [d3bfgvr-run.sh](doom3-bfg-vr/d3bfgvr-run.sh) | Launch wrapper. |

### selaco-vr ([games/selaco-vr](../games/selaco-vr/))

| Script | What it does |
|---|---|
| [selaco_port.py](selaco-vr/selaco_port.py) | **GPL.** Idempotent Linux/ARM64 patches for SelacoVR: GCC 15 fixes, OpenVR joystick on POSIX, `openvr_capi.h` packing, single `VR_Init`, Frame input quirks, `vr_recenter`. |
| [selaco_build.sh](selaco-vr/selaco_build.sh) | Applies the patches and builds with cmake/ninja (OpenVR dynamic, system SDL2 and OpenAL). |
| [zmusic_build.sh](selaco-vr/zmusic_build.sh) | Builds ZMusic for ARM64. |
| [selaco_native_setup.sh](selaco-vr/selaco_native_setup.sh) | Assembles the game folder and writes the run script. |
| [selaco_binding.py](selaco-vr/selaco_binding.py) | Writes the legacy-input binding and the `frame.cfg` the launcher execs (layout table in its docstring). |

### avp-vr ([games/avp-vr](../games/avp-vr/))

| Script | What it does |
|---|---|
| [avp_build.sh](avp-vr/avp_build.sh) | cmake/ninja build with GCC 15 flags and SteamVR's loader. |
| [avp_lowercase.sh](avp-vr/avp_lowercase.sh) | Lowercase symlinks into the untouched Steam install. |
| [AVPVR-frame-keyboard.patch](avp-vr/AVPVR-frame-keyboard.patch) | **GPL.** Falls back to the controller keyboard when SteamVR closes its own at once. |
| [avpvr-run.sh](avp-vr/avpvr-run.sh) | Launch wrapper. |

### dusk-hd-vr ([games/dusk-hd-vr](../games/dusk-hd-vr/))

| Script | What it does |
|---|---|
| [install.sh](dusk-hd-vr/install.sh) | Installs Dusk_HD_VR into `DLC/DUSK HD` with the framepad stand-ins and the launch wrapper. |
| [duskhdvr-launch.sh](dusk-hd-vr/duskhdvr-launch.sh) | Launch wrapper: HD exe, BepInEx and xinput overrides, uinput pad. |
| [dusk_frame_controls.py](dusk-hd-vr/dusk_frame_controls.py) | Writes the SteamVR binding, the mod's mapping file and the camera scale (control chain documented in its docstring). |
| [FrameVR_DuskHD.cs](dusk-hd-vr/FrameVR_DuskHD.cs) | BepInEx plugin source: head-oriented left stick, real menu buttons, scene probe log. Build with the .NET 4 C# compiler. |

The framepad DLL pair, the uinput pad and the Mono.Cecil stripping tool are described in the game README but their source is not in this repository yet.

### hollow-knight-vr ([games/hollow-knight-vr](../games/hollow-knight-vr/))

| Script | What it does |
|---|---|
| [hk_install.sh](hollow-knight-vr/hk_install.sh) | Copies the mod into the game folder without overwriting, writes the shortcut wrapper, adds the shortcut, launches once. |
| [hkvr-shortcut.sh](hollow-knight-vr/hkvr-shortcut.sh) | Shortcut wrapper: Hollow Knight's prefix, BepInEx and xinput overrides, uinput pad, debug marker. |
| [hk_frame_controls.py](hollow-knight-vr/hk_frame_controls.py) | Writes the SteamVR binding (the game's Xbox layout 1:1, d-pad touch on a spare action) and selects it. |
| [FrameVR_HK.cs](hollow-knight-vr/FrameVR_HK.cs) | BepInEx plugin source: Start/Back on the real buttons, d-pad re-assert and pulse latch, hotkey gesture removed. Build with the .NET Framework C# compiler. |
| [hk_plugin_install.sh](hollow-knight-vr/hk_plugin_install.sh) | Installs the built plugin into `BepInEx/plugins` and relaunches. |
| [hk_launch.sh](hollow-knight-vr/hk_launch.sh) | Launch through Steam with a BepInEx, Player.log and vrserver summary. |

### red-faction-vr ([games/red-faction-vr](../games/red-faction-vr/))

| Script | What it does |
|---|---|
| [rf_setup.sh](red-faction-vr/rf_setup.sh) | Runs the mod's Inno installer silently inside Red Faction's prefix through the wrapper's `mode=run` hook. |
| [rfvr-shortcut.sh](red-faction-vr/rfvr-shortcut.sh) | Shortcut wrapper: Red Faction's prefix, debug marker, `mode` hooks for running other commands in the prefix. |
| [rf_patch.py](red-faction-vr/rf_patch.py) | **MPL-2.0.** Idempotent patch: the six hand-scoped actions accept both hands, the menu action pauses under SteamVR, a `recenter` action. |
| [container/Containerfile](red-faction-vr/container/Containerfile), [rf_build2.sh](red-faction-vr/rf_build2.sh) | The MinGW GCC 14 podman image and the full cross-build. |
| [rf_rebuild.sh](red-faction-vr/rf_rebuild.sh), [rf_install_dll.sh](red-faction-vr/rf_install_dll.sh) | Incremental rebuild, DLL install (original kept as `.orig`), rebind, relaunch. |
| [rf_binding.py](red-faction-vr/rf_binding.py), [rf_frame_binding.json](red-faction-vr/rf_frame_binding.json) | The Frame layout as a SteamVR OpenXR binding typed `frame_controller`. |
| [rf_launch.sh](red-faction-vr/rf_launch.sh) | Launch through Steam, keeping the app's Index default unwritable so the custom binding loads. |

### fear-vr, l4d2-vr, portal2-vr, bendy-vr, deus-ex-hr-vr

| Script | What it does |
|---|---|
| [fear-vr/fear_setup.sh](fear-vr/fear_setup.sh) | Points F.E.A.R. at Proton Experimental and the wrapper, runs the mod's Setup once. |
| [fear-vr/fearvr-launch.sh](fear-vr/fearvr-launch.sh) | Launch wrapper; swaps Proton's `waitforexitandrun` for `run` on the launcher's handoff relaunch. |
| [l4d2-vr/l4d2vr_install.py](l4d2-vr/l4d2vr_install.py) | Installs l4d2vr with the Frame binding in its action manifest. |
| [l4d2-vr/l4d2_patch.py](l4d2-vr/l4d2_patch.py) | Binary-patches the mod's `d3d9.dll` to wait for `client.dll` and skip the loading-screen overlay in game. |
| [l4d2-vr/l4d2_setup.sh](l4d2-vr/l4d2_setup.sh) | Checks the Windows build, runs the installer, sets the launch options. |
| [portal2-vr/p2_install.sh](portal2-vr/p2_install.sh) | Installs portal2vr-roomscale with backups of every overwritten file. |
| [portal2-vr/p2_binding.sh](portal2-vr/p2_binding.sh) | Reuses the L4D2 Frame binding (same action set). |
| [bendy-vr/install.sh](bendy-vr/install.sh) | Installs BendyVR by hand once the `release-1.5` branch is in place. |
| [bendy-vr/launch.sh](bendy-vr/launch.sh) | Launches and reports the BepInEx and Unity logs. |
| [deus-ex-hr-vr/install.sh](deus-ex-hr-vr/install.sh) | Installs DeusExHRVR with the x86-64 runtime DLLs and registry settings, with backups. |
| [deus-ex-hr-vr/launch.sh](deus-ex-hr-vr/launch.sh) | Launches with optional Proton/DXVK logging. |

### contractors, halo-mcc, snapshot-vr

| Script | What it does |
|---|---|
| [contractors/contractors](contractors/contractors) | Launch-option wrapper that skips Unreal's prerequisite bootstrapper. |
| [halo-mcc/repair-mcc-prefix.sh](halo-mcc/repair-mcc-prefix.sh) | Restores Proton's ARM64 runtime DLLs after the EAC installer overwrote them. |
| [halo-mcc/mcc](halo-mcc/mcc) | Launch-option wrapper: flat without EAC from the normal entry, the VR mod from the "Anti-Cheat Disabled" entry. |
| [snapshot-vr/install-snapshotvr-fovfix.sh](snapshot-vr/install-snapshotvr-fovfix.sh) | Builds and installs an implicit OpenXR API layer that adds `XR_FB_swapchain_update_state` when a game enables `XR_FB_foveation` without it. |
