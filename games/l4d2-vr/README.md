# Left 4 Dead 2 VR

**Status:** Working — a binary-patched copy of the mod's `d3d9.dll` waits out FEX's slow DLL loading; fixed 2026-10-21.

| | |
|---|---|
| Upstream | l4d2vr v0.6.2 by sd805, OpenVR, a Direct3D 9 proxy DLL |
| Game data | Left 4 Dead 2 (Steam 550), Windows build. The compat tool must be set before installing so Steam fetches the Windows depots |
| Route | Proton + FEX (Proton Experimental, ARM64) |
| Steam entry | Left 4 Dead 2 550 stays the flat entry (the Vulkan renderer, no mod) through `flatvr-launch.sh`. "Left 4 Dead 2 VR" 3229493339 is the VR shortcut, which runs `/usr/bin/steam -applaunch 550 -frame-vr` with the VR flag set |
| Set up | 2026-10-21 |

## What it is

The l4d2vr mod is a `d3d9.dll` proxy dropped beside the game: it hooks the game's Direct3D 9 renderer, submits the eyes to SteamVR through OpenVR, and reads a SteamVR action manifest for input. Two of its timing assumptions break under FEX, where the game's `client.dll` takes about three minutes to load.

## What broke on the Frame

- **Proton/FEX, module load time:** the mod's `GetModuleWithRetry` gives up after 100 tries of 50 ms. Under FEX `client.dll` loads about three minutes in, so the mod never started VR and the game ran flat.
- **Proton/FEX, frame rate:** `VR::SubmitVRTextures` shows the main-menu overlay (the last flat backbuffer, which is the loading screen) on every call where the game did not render a new stereo frame. At FEX frame rates that happens constantly in game, so the loading screen flickered in front of the view.
- **The game itself, renderer:** this build of Left 4 Dead 2 defaults to its own Vulkan renderer (`shaderapivk` plus `bin/dxvk_d3d9.dll`), which bypasses the mod's `d3d9.dll` entirely.
- **Steam depots:** with the default compat setting Steam installs the Linux build, which has no `left4dead2.exe` for the mod to hook.

## The fix

`l4d2_patch.py` makes two changes to the mod's binary (`x/d3d9.dll` in, `d3d9-frame.dll` out):

1. The retry loop tail `6a 32 / ff 15 <Sleep> / 83 fe 64 / 7c d4` becomes a 127 ms sleep with the `jl` turned into a `jmp`, so it retries until `GetModuleHandleA` succeeds. It waits for `client.dll` indefinitely.
2. An `IsInGame()` check is added at the top of the no-new-frame path in `SubmitVRTextures`. In game it now returns without touching overlays, and the compositor keeps or reprojects the last eye frames. The new code lives in the `.text` slack after VirtualSize (`0x100f3354`), reached by a `jmp` at `0x100dd896`; the section's VirtualSize is grown over the cave so the loader maps it.

`l4d2vr_install.py <game dir>` copies `d3d9.dll` and `openvr_api.dll` (originals kept as `*.orig-l4d2vr`) and the `VR/` folder (preserving an existing `VR/config.txt`), writes `VR/SteamVRActionManifest/bindings_frame_controller.json`, and inserts it first in `action_manifest.json`'s `default_bindings`.

`-dx9` on the launch options forces the Direct3D 9 renderer so the proxy is loaded, and `WINEDLLOVERRIDES=d3d9=n,b` makes Wine prefer the mod's DLL over its own.

## Exact commands

The scripts live in this repo under `scripts/l4d2-vr/` and are copied to `~/PCVR/L4D2VR/` on the headset. The mod zip is extracted to `~/PCVR/L4D2VR/x`.

```bash
# checks the install is the Windows build (left4dead2.exe, PE machine type), installs the mod + binding,
# and sets the launch options
ssh frame "bash ~/PCVR/L4D2VR/l4d2_setup.sh"

# the FEX-patched DLL
ssh frame "python3 -I ~/PCVR/L4D2VR/l4d2_patch.py ~/PCVR/L4D2VR/x/d3d9.dll ~/PCVR/L4D2VR/d3d9-frame.dll"

# reinstall everything (install + patched DLL) and relaunch
ssh frame "bash ~/PCVR/L4D2VR/l4d2_relaunch.sh"

# SteamVR per-app render resolution (native 1728)
ssh frame "bash ~/PCVR/L4D2VR/l4d2_res.sh"     # steam.app.550/resolutionOverride = 1440
```

Launch options on Left 4 Dead 2 550, as set by `l4d2_setup.sh`:

```
WINEDLLOVERRIDES="d3d9=n,b" %command% -insecure -dx9 -window -w 1280 -h 720 +mat_motion_blur_percent_of_screen_max 0 +crosshair 0 +mat_queue_mode 0 +mat_vsync 0 +mat_antialias 0 +mat_grain_scale_override 0
```

During troubleshooting the line was prefixed with `PROTON_LOG=1 WINEDEBUG=+loaddll`; that was dropped once stable. The flat library entry goes through `~/PCVR/bin/flatvr-launch.sh` and only runs the mod when `-frame-vr` is on the command line. Expect about three minutes from launch to the menu.

## Controls

An action-manifest binding, `VR/SteamVRActionManifest/bindings_frame_controller.json`, written by `l4d2vr_install.py` onto the mod's `/actions/main` set. Poses, skeleton and haptics are taken from the mod's Oculus Touch file. Grips are unused. Stick deadzone is 10% for move and turn; the right stick's up/down act as a d-pad in touch sub-mode with a 75% deadzone.

Layout, on the [standard Frame layout](../../FRAME-LAYOUT.md):

| Frame input | Action |
|---|---|
| Right trigger | PrimaryAttack (shoot) |
| Left trigger | SecondaryAttack (shove) |
| Left bumper | Jump |
| Right bumper | Use |
| Right A | Crouch, ActivateVR, MenuSelect |
| Right B | Reload, MenuBack |
| Right X | Flashlight |
| Right Y | Jump |
| Left stick | Walk; click = ResetPosition (recenter) |
| Right stick | Turn; up/down = PrevItem / NextItem; click = ShowHUD |
| Left d-pad | MenuUp / MenuDown / MenuLeft / MenuRight; left/right also PrevItem / NextItem |
| Menu (right) | Pause |
| View (left) | Scoreboard |

Deviations from the standard: right stick click shows the HUD, left stick click recenters (the mod's default), and X is the flashlight. The left stick has no menu d-pad because it is the walk stick; the left d-pad buttons navigate menus.

## Status and known issues

- Working in VR.
- Launch to menu takes about three minutes under FEX.
- SteamVR's per-app render resolution is lowered to 1440 (native 1728) for performance.
- The patch offsets are specific to l4d2vr v0.6.2's `d3d9.dll`; the script asserts on the byte patterns and refuses to patch anything else.

## Undo

The sources record no dedicated uninstall script. The installer keeps the originals as `d3d9.dll.orig-l4d2vr` and `openvr_api.dll.orig-l4d2vr` in the game folder; restoring them, removing `VR/`, clearing the launch options on 550, and removing shortcut 3229493339 (`python3 ~/PCVR/bin/steam_shortcuts.py remove 3229493339`) reverses the setup. A Steam file verify also removes the mod files.

## Files in this repo

- [l4d2vr_install.py](../../scripts/l4d2-vr/l4d2vr_install.py): copies the mod into the game folder and writes the Frame binding into the action manifest; the layout is in its docstring.
- [l4d2_patch.py](../../scripts/l4d2-vr/l4d2_patch.py): the two binary patches to the mod's `d3d9.dll`, with the byte patterns and addresses documented.
- [l4d2_setup.sh](../../scripts/l4d2-vr/l4d2_setup.sh): checks for the Windows build, runs the installer and sets the launch options.

## Credits

- l4d2vr by sd805, the mod this runs. The binary patch modifies that mod's DLL for FEX; the patched file is not distributed here.
- Left 4 Dead 2 (game data from Steam, not included).
- Valve for Left 4 Dead 2, OpenVR, SteamVR, Proton and the Steam Frame.

This repo holds only patches and scripts. It contains no game data, no mod binaries and no game binaries.
