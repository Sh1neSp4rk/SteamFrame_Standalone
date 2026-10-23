# Hollow Knight VR

**Status:** Working. The mod runs under Proton with the DUSK HD VR recipe plus a small Frame-specific BepInEx plugin; confirmed in the headset on 2026-10-23.

| | |
|---|---|
| Upstream | "Hollow Knight VR Enhanced" (`HollowKnight_VREnhanced.zip`): BepInEx 5.4.22, the UnityVR_Bepinex post-2020 x64 core and the SteamVR Unity plugin. OpenVR through SteamVR's action system |
| Game data | Hollow Knight (Steam 367520, Unity 2020, 64-bit). The mod's files live in the game folder |
| Route | Proton Experimental (ARM64) + FEX, in Hollow Knight's own prefix |
| Steam entry | Non-Steam shortcut "Hollow Knight VR" 2289186113 with red "HOLLOW KNIGHT VR" art; the library entry stays the flat game |
| Set up | 2026-10-23 |

## What it is

A BepInEx 5 mod built on the UnityVR_Bepinex core, the same family as [DUSK HD VR](../dusk-hd-vr/). The game is 2D on a quad in VR; the mod's own options (theater mode, camera modes) are on its in-game menu. With `vrControllersSupport = true` the core maps SteamVR actions onto a virtual Xbox pad that the game reads as an ordinary controller.

## What broke on the Frame

- **Proton/FEX, Harmony patches on Unity native methods.** As with DUSK, the core's Harmony patches on native setters recurse under FEX until the main thread's stack overflows.
- **Proton, the ViGEmBus driver.** The core "plugs in" its virtual Xbox pad through the ViGEm kernel driver, which Proton cannot load.
- **The game itself, Steamworks under a shortcut.** Launched from a non-Steam shortcut the mod's Steamworks init fails with `Steam failed to initialize`.
- **The game itself, the first-run language screen.** The first launch is a black screen with no sound: the language-select screen sits on a camera the mod does not render.
- **The mod's core, the d-pad.** The core's left-joystick handler is an every-frame update listener that ends by clearing all four virtual d-pad buttons, so a held d-pad direction reached the game as a one-frame press.
- **The mod's core, pause and inventory.** The core only reaches the pad's Start and Back through a "hotkey" gesture (left controller within 25 cm of the head), which also buzzes the controller every frame while it is held there.
- **The Frame controller driver, d-pad clicks.** Traced from the mod's action events: the driver reports a held left d-pad click as pulses of about 150 ms every 250 ms that stop after about one second even while the button stays down, and the d-pad's touch input is one shared capacitive sensor (a resting thumb fires up, left and right together). The digital click never reaches an app as a plain press and release.

## The fix

- **Install:** unzip into the game folder (BepInEx, `winhttp.dll`, `doorstop_config.ini`, the mod's Managed, Plugins and StreamingAssets files). The core is extracted from its Costura-packed plugin and `StripNativePatches.exe` (the Mono.Cecil tool made for DUSK) removes the native-method patches; the stripped core is placed as `UnityVR_Bepinex_post2020_x64.dll`. The mod's AspectBorders camera is excluded in `BepInEx/config/UnityVR_Bepinex.cfg` (originals kept as `.orig`).
- **Virtual pad:** DUSK's framepad stands in for ViGEm: a `ViGEmClient.dll` that writes pad state to shared memory, a `uinput_pad` that mirrors it as a Linux Xbox 360 controller, and an `xinput1_3.dll` shim the game polls. The shortcut wrapper starts `uinput_pad` and it exits with the launch.
- **Flat stays flat:** the shortcut wrapper sets `WINEDLLOVERRIDES="winhttp=n,b;xinput1_3=n,b"`, so BepInEx loads only for the VR entry and the library entry launches the unmodified game.
- **Steamworks:** a `steam_appid.txt` containing `367520` in the game folder. The app then also connects to SteamVR as `steam.app.367520`; bindings keyed on the shortcut id still apply.
- **Language screen:** pick the language once in the flat game (or in theater mode). It never comes back.
- **FrameVR_HK plugin** (about 150 lines, compiled with the .NET Framework C# compiler against the game's assemblies, installed into `BepInEx/plugins`):
  1. Postfixes the core's Start and Back action handlers to press Start and Back on the virtual pad, and patches the hotkey gesture out (no more vibration).
  2. Re-asserts the held d-pad directions right after the core's per-frame clear.
  3. Works around the driver's d-pad pulses: the binding sends the d-pad clicks to the direction actions and the d-pad touch to the otherwise unused `ClickLeftJoystick` action; the plugin latches a pulsed direction for as long as the touch lasts, releases the opposite direction on a new pulse, and keeps a 0.4 s latch for taps.

## Exact commands

The scripts live in this repo under `scripts/hollow-knight-vr/` and are copied to `~/PCVR/HollowKnightVR/` on the headset. They expect DUSK HD VR's framepad build at `~/PCVR/DuskHDVR/framepad/out/` (its source is not in this repo yet) and the shared helpers in `~/PCVR/bin/`.

```bash
# unzip the mod into the game folder, write the shortcut wrapper, add the shortcut, launch once with logs
ssh frame "bash ~/PCVR/HollowKnightVR/hk_install.sh"

# write bindings_frame_controller.json, the actions.json entry, the cfg change and the steamvr.vrsettings selection
ssh frame "python3 ~/PCVR/HollowKnightVR/hk_frame_controls.py"

# install FrameVR_HK.dll into BepInEx/plugins and relaunch ("debug" adds timed d-pad tracing through env.test)
ssh frame "bash ~/PCVR/HollowKnightVR/hk_plugin_install.sh"

# launch through Steam and print a BepInEx / Player.log / vrserver summary
ssh frame "bash ~/PCVR/HollowKnightVR/hk_launch.sh 60"
```

Build the plugin on a Windows PC with the .NET Framework compiler, referencing the game's `Managed` assemblies, BepInEx, HarmonyLib, the UnityVR core and the SteamVR plugin:

```
csc /target:library /out:FrameVR_HK.dll /r:<refs> FrameVR_HK.cs
```

Debugging: `touch ~/PCVR/HollowKnightVR/debug` turns on a Proton log under `~/PCVR/HollowKnightVR/logs/`; `env.test` is sourced by the wrapper.

## Controls

Not the [standard layout](../../FRAME-LAYOUT.md). The Frame has every Xbox button, so the binding is Hollow Knight's own default pad layout, one to one:

| Frame input | Pad | Hollow Knight action |
|---|---|---|
| Right A | A | Jump |
| Right X | X | Attack |
| Right B | B | Focus / cast |
| Right Y | Y | Dream nail |
| Right trigger | RT | Dash |
| Left trigger | LT | Super dash |
| Right bumper | RB (the core's `rightgrip` action) | Quick cast |
| Left bumper | LB (the core's `leftgrip` action) | Quick map |
| Left stick | Left stick | Move |
| Left d-pad | D-pad | Move, menus |
| Menu | Start | Pause (via FrameVR_HK) |
| View | Back | Inventory (via FrameVR_HK) |
| Right stick click | R3 | |
| Left stick click | unbound | Its action carries the d-pad touch for the plugin; Hollow Knight does not use L3 |
| Grips | unused | |

## Status and known issues

- Working in the headset: no vibration, the Xbox layout as expected, the d-pad walks while the thumb stays on it.
- The d-pad hold depends on the capacitive sensor: keep the thumb on the pad after pressing, lift to stop. That is a Frame driver limitation (the driver is read-only, with no settings), not the game's. See [KNOWN-ISSUES.md](../../KNOWN-ISSUES.md).
- Pressing between two d-pad directions pulses both; a diagonal is harmless here (up and down only look when standing still).
- The framepad DLL pair, `uinput_pad` and `StripNativePatches` are described but their source is not in this repository yet.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 2289186113"
# the flat game is untouched unless BepInEx is forced on; to remove the mod, delete BepInEx/, winhttp.dll,
# doorstop_config.ini, xinput1_3.dll and steam_appid.txt from the game folder and verify files in Steam
```

## Files in this repo

- [hk_install.sh](../../scripts/hollow-knight-vr/hk_install.sh): copies the mod into the game folder without overwriting, writes the shortcut wrapper, adds the shortcut, launches once.
- [hkvr-shortcut.sh](../../scripts/hollow-knight-vr/hkvr-shortcut.sh): the shortcut wrapper (prefix, DLL overrides, uinput pad, debug marker).
- [hk_frame_controls.py](../../scripts/hollow-knight-vr/hk_frame_controls.py): writes the SteamVR binding and selects it (layout and the control chain in its docstring).
- [FrameVR_HK.cs](../../scripts/hollow-knight-vr/FrameVR_HK.cs): the BepInEx plugin source.
- [hk_plugin_install.sh](../../scripts/hollow-knight-vr/hk_plugin_install.sh): installs the built plugin and relaunches.
- [hk_launch.sh](../../scripts/hollow-knight-vr/hk_launch.sh): launch through Steam with a log summary.

## Credits

- Hollow Knight VR Enhanced and the UnityVR_Bepinex core, on BepInEx and HarmonyLib; the SteamVR Unity plugin by Valve.
- Hollow Knight by Team Cherry (game data from Steam, not included).
- This repo holds only scripts and the plugin source. No game data, no mod archive, no built DLLs.
