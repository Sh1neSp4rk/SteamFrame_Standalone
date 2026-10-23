# DUSK HD VR

**Status:** Working — three Frame-specific fixes plus a controls plugin; fixed 2026-10-21.

| | |
|---|---|
| Upstream | Dusk_HD_VR 1.0.0 by Astienth (distributed through the FarmerTrueVR Discord), BepInEx plugin, OpenVR |
| Game data | DUSK (Steam 519860), Windows build (compat tool set to proton-stable; Steam had installed the Linux build), with the free DUSK HD DLC. The mod installs into `Dusk/DLC/DUSK HD` |
| Route | Proton + FEX (Proton stable, ARM64) |
| Steam entry | DUSK 519860 stays the flat entry (classic DUSK) through `flatvr-launch.sh`. "DUSK HD VR" 3975090014 is the VR shortcut, which runs `/usr/bin/steam -applaunch 519860 -frame-vr` with the VR flag set |
| Set up | 2026-10-21 |

## What it is

A Unity VR mod that drives DUSK through a virtual Xbox controller. The mod "plugs in" an Xbox 360 pad with the ViGEmBus driver, reads SteamVR input, and feeds it to that pad; the game reads the pad through XInput. Three separate Frame problems stood between it and a playable game: a Windows kernel driver Proton cannot run, a Harmony patch that recurses forever under FEX, and a game that only reads gamepads it can match to a real device.

## What broke on the Frame

- **Proton/FEX, the virtual pad driver:** the mod depends on the ViGEmBus kernel driver to create its virtual Xbox 360 pad. Proton cannot run that driver, so the game never saw any input.
- **Proton/FEX, Harmony patches on Unity native methods:** a stack overflow on the main thread right after "[SteamVR] Initialized". The mod Harmony-patches Unity native methods (`Transform.set_*_Injected`, `GameObject.set_tag`, `Camera.ResetProjectionMatrix`), and calling them recursed forever under Proton/FEX.
- **The game itself, pad detection:** Unity ignores an XInput pad unless it can match it to a real game-controller device, and the prefix had none. DUSK also scans for controllers only once, at startup.
- **The mod itself, hands:** the release has no hands bundle, so `createHands` has to be off.
- **The mod itself, menus:** the base mod has no pause action on a button, only a gesture (hold the left controller by the head, then click the right stick).

## The fix

1. **framepad, stand-ins for ViGEmBus.** `~/PCVR/DuskHDVR/framepad` (built with clang + lld-link, no Windows SDK) provides two DLLs: a `ViGEmClient.dll` for `BepInEx/plugins` that the mod calls, and an `xinput1_3.dll` beside `Dusk.exe` that the game's XInputInterface reads. They share pad state through memory (`Local\FramePadViGEm`, backed by `C:\users\steamuser\framepad.shm` in the prefix). The original DLL is kept as `~/PCVR/DuskHDVR/ViGEmClient.dll.orig`. framepad reports controller 0 from startup because DUSK scans only once. It logs to `C:\users\steamuser\framepad.log` in the prefix.
2. **A stripped plugin core.** `Dusk_Data/Managed/UnityVR_Bepinex_pre2020.dll` shadows the Costura-embedded copy of the mod's core, with the native-method Harmony patches removed. It was made with a small Mono.Cecil tool (StripNativePatches) built with Windows' csc on a PC. DUSK's default settings do not need those patches (only `useTransformSetterPatchForAttachObj` would).
3. **A real controller device on the Linux side.** The launch wrapper starts `framepad/out/uinput_pad`, an idle Linux uinput Xbox 360 pad (045e:028e) that mirrors the shared pad state and exits with the game, so Wine reports a game controller and Unity creates a joystick. That uinput pad is the device Unity actually reads. "Allow gamepads" must be enabled in game.

Also: `createHands = false` in `BepInEx/config/UnityVR_Bepinex.cfg` (original kept as `.bak-frame`).

The framepad DLLs, `uinput_pad` and the StripNativePatches Mono.Cecil tool are described here but their source is **not** in this repo.

## Exact commands

The scripts live in this repo under `scripts/dusk-hd-vr/` and are copied to `~/PCVR/DuskHDVR/` on the headset. The mod zip is extracted to `~/PCVR/DuskHDVR/extracted`.

```bash
# copies the zip contents into Dusk/DLC/DUSK HD, swaps in framepad's ViGEmClient.dll and xinput1_3.dll,
# writes duskhdvr-launch.sh and uninstall.sh, and sets the launch option
ssh frame "bash ~/PCVR/DuskHDVR/install.sh"

# controls (game closed): binding, actions.json entry, steamvr.vrsettings selection, mappings/default.ini,
# VRCamScale, the FrameVR plugin, then relaunch
ssh frame "bash ~/PCVR/DuskHDVR/apply_controls.sh"

# start without Steam's launch-option dialog
ssh frame "steam steam://launch/519860/option0"
```

Launch option on DUSK 519860 (set by `install.sh`):

```
/home/steamos/PCVR/DuskHDVR/duskhdvr-launch.sh %command%
```

`duskhdvr-launch.sh` exports `WINEDLLOVERRIDES="winhttp=n,b;xinput1_3=n,b"` (BepInEx's doorstop and framepad's XInput), swaps `common/Dusk/Dusk.exe` in the command line for `common/Dusk/DLC/DUSK HD/Dusk.exe`, starts `uinput_pad`, and execs the result. It records each launch in `~/PCVR/DuskHDVR/last-launch.txt`.

Debugging: `touch ~/PCVR/DuskHDVR/debug` turns on `PROTON_LOG=1` and `WINEDEBUG=+loaddll` (Proton log in `~/steam-519860.log`). Do not add `+seh`; it overflows Mono's stack by itself. With `~/PCVR/DuskHDVR/rawlist` present the wrapper also runs `rawlist.exe` in the prefix through `PROTON_REMOTE_DEBUG_CMD`.

## Controls

The chain is: Frame button, to a SteamVR action (`bindings_frame_controller.json`), to the virtual Xbox pad (the mod swaps LB to RB, R3 to LB, RB to R3 on the way), to a DUSK action (`mappings/default.ini`, preset 0). `dusk_frame_controls.py` writes the binding (plus the `actions.json` default entry and the `steamvr.vrsettings` selection for `steam.app.519860`), the mapping file, and `VRCamScale = 1.35` in `UnityVR_Bepinex.cfg` so DUSK's oversized world reads closer to real size. Originals are kept as `*.orig`.

`FrameVR_DuskHD.dll` (source `FrameVR_DuskHD.cs`, a BepInEx plugin built on a PC with the .NET 4 csc) in `BepInEx/plugins` adds what the mapping cannot express: a head-oriented left stick (rotated by the headset's yaw relative to the game body before it reaches the pad), the menu button pressed as the pad's Start (pause), the view button as Back, a "probe" log line per scene (player collider height and headset height, for tuning `VRCamScale`), and optional per-second input logging (`framevr.duskhd.cfg`, `logInputState`).

Layout, on the [standard Frame layout](../../FRAME-LAYOUT.md):

| Frame input | Action |
|---|---|
| Right trigger | Fire |
| Left trigger | Alt fire (zoom) |
| Left bumper | Jump |
| Right bumper | Use |
| Right A | Crouch |
| Right B | Quick melee |
| Right X | Flashlight |
| Right Y | Jump |
| Left stick | Move, head-oriented (plugin) |
| Left stick click | Walk |
| Left grip (80%) | Tap: last weapon; hold plus right stick: weapon wheel |
| Right stick | Turn |
| Right stick click | Recenter when both sticks are clicked together (mod gesture) |
| Left d-pad up / down | Quick load / quick save |
| Left d-pad left / right | Previous / next weapon |
| Menu (right) | Pause menu (plugin) |
| View (left) | Stats / back (plugin) |
| Right grip | Unused |

Deviations from the standard: left stick click is walk (not sprint); left grip (80%) is last weapon / weapon wheel; right stick up/down is unused because it drives the wheel (the mod frees it only while the left grip action is held). The left grip needs a firm 80% squeeze (`click_activate_threshold 0.8`, `click_deactivate_threshold 0.7`) so holding the controller does not fire it. Without the plugin, the menu is the mod's gesture: hold the left controller by your head and click the right stick.

## Status and known issues

- Working in VR with the layout above.
- The framepad DLLs, `uinput_pad` and the Mono.Cecil stripping tool are prebuilt pieces whose source is not in this repo.
- "Allow gamepads" must be on in DUSK's settings.
- `+seh` in `WINEDEBUG` overflows Mono's stack on its own; do not use it when debugging.

## Undo

```bash
ssh frame "bash ~/PCVR/DuskHDVR/uninstall.sh"
```

This removes the files that came from the zip plus framepad, `BepInEx`, `xinput1_3.dll`, `winhttp.dll` and `doorstop_config.ini`, and clears the launch option. DUSK stays on Proton; switch it back to native in Properties > Compatibility.

## Files in this repo

- [install.sh](../../scripts/dusk-hd-vr/install.sh): installs the mod into `DLC/DUSK HD`, swaps in framepad's DLLs, writes the launch wrapper and `uninstall.sh`, sets the launch option.
- [duskhdvr-launch.sh](../../scripts/dusk-hd-vr/duskhdvr-launch.sh): the launch-option wrapper (HD exe, DLL overrides, `uinput_pad`, debug toggles).
- [dusk_frame_controls.py](../../scripts/dusk-hd-vr/dusk_frame_controls.py): writes the SteamVR binding, the mod's mapping file and `VRCamScale`; the control chain is documented at the top.
- [FrameVR_DuskHD.cs](../../scripts/dusk-hd-vr/FrameVR_DuskHD.cs): the BepInEx plugin for head-oriented locomotion and real menu buttons.

## Credits

- Dusk_HD_VR by Astienth (FarmerTrueVR Discord), the mod this runs.
- BepInEx and HarmonyLib, which the plugin builds on.
- DUSK and the DUSK HD DLC (game data from Steam, not included).
- Valve for OpenVR, SteamVR and the Steam Frame.

This repo holds only patches, scripts and the plugin source. It contains no game data, no mod binaries and no game binaries. The framepad stand-ins and the stripped plugin core are not included.
