# Circuit Superstars VR

**Status:** Working. A gamepad-only Unity VR mod under Proton, driven by the Frame controllers through a small bridge plugin; confirmed in the headset on 2026-10-23.

| | |
|---|---|
| Upstream | [Astienth/Circuit_Superstars_VR](https://github.com/Astienth/Circuit_Superstars_VR) 1.0.0: BepInEx 5.4.22, the UnityVR_Bepinex post-2020 core and the SteamVR Unity plugin. OpenVR |
| Game data | Circuit Superstars (Steam 1097130, Unity URP, Rewired input, 64-bit Windows build). The mod's files live in the game folder |
| Route | Proton Experimental (ARM64) + FEX, in the game's own prefix |
| Steam entry | Non-Steam shortcut "Circuit Superstars VR" 3624666961 with red "CIRCUIT SUPERSTARS VR" art; the library entry stays the flat game |
| Set up | 2026-10-23 |

## What it is

Astienth's VR mod for the top-down racer, the third UnityVR_Bepinex mod on the test headset after [DUSK HD VR](../dusk-hd-vr/) and [Hollow Knight VR](../hollow-knight-vr/). By design it has no motion-controller support: it wants an Xbox pad or a keyboard. The mod's own controls ride on Start (double-tap for the first-person camera, hold to recenter; F1 and F2 on a keyboard).

## What broke on the Frame

- **Proton/FEX, Harmony patches on Unity native methods.** `CircuitSuperstars_VR.dll` is Costura-packed around an older UnityVR_Bepinex core whose four Harmony patches on native methods recurse under FEX until the stack overflows.
- **The game itself, Steamworks under a shortcut.** The first launch died at boot with `[Fatal] Stage 2 Boot Failure: Steamworks is not initialized`.
- **No VR-to-pad bridge.** Steam Input hands the game an XInput pad at boot, but it goes quiet once SteamVR takes the Frame controllers, and this older core has no `vrControllersSupport` (that arrived in later cores). Controllers were dead.
- **Proton, the ViGEmBus driver.** The ViGEm client API the bridge uses needs a kernel driver Proton cannot load.
- **Wine's xinput1_4 and Rewired.** With the framepad shim only replacing `xinput1_3` (Unity's native input layer), the game seated the player at pad 2: Rewired loads Wine's own `xinput1_4`, where Steam Input's virtual pad enumerates first.

## The fix

- **Core:** extracted from the Costura-packed plugin, `StripNativePatches.exe` (the Mono.Cecil tool made for DUSK) removes the four native-method patches, and the clean copy goes into `circuit-superstars_Data/Managed/UnityVR_Bepinex_post2020.dll` under its assembly name, so Mono resolves it before Costura's embedded copy.
- **Flat stays flat:** the shortcut wrapper sets `WINEDLLOVERRIDES` for `winhttp` (BepInEx) and the XInput names, so the mod loads only for the VR entry.
- **Steamworks:** a `steam_appid.txt` holding `1097130` in the game folder. The app then connects to SteamVR as `steam.app.1097130`.
- **FrameVR_CS plugin** (about 100 lines, compiled with the .NET Framework C# compiler against the game's Managed assemblies, BepInEx and the Nefarius ViGEm client): waits for `SteamVR_Input.initialized`, creates an Xbox 360 pad through the ViGEm client API, and every frame copies the mod's default action set onto it: A, B, X, Y, the `LeftGrip` and `RightGrip` actions to LB and RB, both triggers, both sticks and their clicks, the d-pad, Start and Back.
- **framepad** stands in for ViGEm: DUSK's `ViGEmClient.dll` writes the pad state to shared memory, `uinput_pad` mirrors it as a Linux Xbox 360 controller, and the `xinput1_3.dll` shim serves it to the game.
- **One pad, player 1:** the shim is copied to every XInput name (`xinput1_1`, `xinput1_2`, `xinput1_3`, `xinput1_4`, `xinput9_1_0`) with matching overrides, so the game sees exactly one controller in slot 0.

## Exact commands

The scripts live in this repo under `scripts/circuit-superstars-vr/` and are copied to `~/PCVR/CircuitSuperstarsVR/` on the headset. They expect DUSK HD VR's framepad build at `~/PCVR/DuskHDVR/framepad/out/` (its source is not in this repo yet) and the shared helpers in `~/PCVR/bin/`.

```bash
# (re)install the pad chain: ViGEm client, framepad stand-in, xinput shim, FrameVR_CS.dll, the binding; relaunch
ssh frame "bash ~/PCVR/CircuitSuperstarsVR/cs_pad.sh"

# serve the shim under every XInput name and add the overrides to the wrapper (one pad, player 1)
ssh frame "bash ~/PCVR/CircuitSuperstarsVR/cs_xinput14.sh"

# write bindings_frame_controller.json and select it for steam.app.1097130 and the shortcut id
ssh frame "python3 ~/PCVR/CircuitSuperstarsVR/cs_frame_controls.py"

# launch through Steam and print a BepInEx / Player.log / vrserver summary
ssh frame "bash ~/PCVR/CircuitSuperstarsVR/cs_launch.sh 60"
```

Build the plugin on a Windows PC with the .NET Framework compiler:

```
csc /target:library /out:FrameVR_CS.dll /r:<game Managed assemblies, BepInEx, Nefarius.ViGEm.Client, SteamVR> FrameVR_CS.cs
```

Debugging: `touch ~/PCVR/CircuitSuperstarsVR/debug` turns on a Proton log under `~/PCVR/CircuitSuperstarsVR/logs/`; `env.test` is sourced by the wrapper.

## Controls

Not the [standard layout](../../FRAME-LAYOUT.md): the mod has no motion controls, so the binding is the game's own Xbox layout, one to one, through the FrameVR_CS virtual pad.

| Frame input | Pad |
|---|---|
| A, B, X, Y | A, B, X, Y |
| Right trigger | RT (accelerate) |
| Left trigger | LT (brake, reverse) |
| Right bumper, left bumper | RB, LB (through the `RightGrip` and `LeftGrip` actions) |
| Left stick | Left stick (steer); click = L3 |
| Right stick | Right stick; click = R3 |
| Left d-pad | D-pad (taps; the Frame d-pad pulses, see KNOWN-ISSUES) |
| Menu | Start (pause; the mod's double-tap = first-person view, hold = recenter) |
| View | Back |
| Grips | unused |

## Status and known issues

- Working in the headset with the layout above.
- The mod's `UpdateSpeedHaptics` throws a NullReferenceException every frame without a bHaptics vest. Log noise only.
- Steam Input still creates its pads for the shortcut; they are simply invisible to the game through the shim.
- The framepad DLL pair, `uinput_pad` and `StripNativePatches` are described but their source is not in this repository yet.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3624666961"
# to remove the mod: delete BepInEx/, winhttp.dll, doorstop_config.ini, steam_appid.txt, xinput*.dll and the
# Managed/StreamingAssets files it added (the zip's file list), or verify files in Steam
```

## Files in this repo

- [csvr-shortcut.sh](../../scripts/circuit-superstars-vr/csvr-shortcut.sh): the shortcut wrapper (prefix, BepInEx and XInput overrides, uinput pad, debug marker).
- [cs_pad.sh](../../scripts/circuit-superstars-vr/cs_pad.sh): installs the pad chain, the plugin and the binding, then relaunches.
- [cs_xinput14.sh](../../scripts/circuit-superstars-vr/cs_xinput14.sh): serves the shim under every XInput name and checks which pad the game assigned.
- [cs_frame_controls.py](../../scripts/circuit-superstars-vr/cs_frame_controls.py): writes and selects the SteamVR binding (layout and chain in its docstring).
- [FrameVR_CS.cs](../../scripts/circuit-superstars-vr/FrameVR_CS.cs): the bridge plugin source.
- [cs_launch.sh](../../scripts/circuit-superstars-vr/cs_launch.sh): launch through Steam with a log summary.

## Credits

- Astienth for Circuit_Superstars_VR and the UnityVR_Bepinex core, on BepInEx and HarmonyLib; Nefarius for the ViGEm client API; the SteamVR Unity plugin by Valve.
- Circuit Superstars by Original Fire Games, published by Square Enix (game data from Steam, not included).
- This repo holds only scripts and the plugin source. No game data, no mod archive, no built DLLs.
