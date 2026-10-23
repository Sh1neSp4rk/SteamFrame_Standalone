# Unreal Revived VR

**Status:** Working. Direct3D 12 plus OpenXR under Proton at 72 fps, after four fixes; one of them is a reusable OpenXR API layer. Confirmed in the headset on 2026-10-23.

| | |
|---|---|
| Upstream | [kwstasg/Unreal-Revived](https://github.com/kwstasg/Unreal-Revived) 0.9.0: OldUnreal 227k_15, the D3D12Drv renderer, XInputWinDrv, native OpenXR with motion-controller aiming |
| Game data | Unreal Gold (Steam 13250) as the installer's source. The installer copies the original maps, textures, sounds and music into its own tree, so the result no longer needs the Steam copy |
| Route | Proton Experimental (ARM64) + FEX, in the shortcut's own prefix; wineopenxr and vkd3d-proton |
| Steam entry | Non-Steam shortcut "Unreal Revived VR" 3358004613 with red "UNREAL REVIVED VR" art. The game lives inside the prefix at `C:\Games\Unreal Revived` |
| Set up | 2026-10-23 |

## What it is

Unreal Gold rebuilt on OldUnreal's 227k engine with a DirectX 12 renderer and native OpenXR. The game maps per-hand OpenXR actions (trigger, squeeze, primary, secondary, stick click, menu, view) onto a virtual Xbox pad, and Unreal binds that pad as Joy1 to Joy12 in `User.ini`.

## What broke on the Frame

- **The installer and ARM64 Wine.** The Inno Setup installer is `ArchitecturesAllowed=x64compatible`. On ARM64 Windows that means Windows 11 with x64 emulation, which Inno checks by asking which machine types the system can run. Proton's ARM64 Wine answers "x86 and Arm64", even with the prefix set to Windows 11, so setup quits with "does not support the version of Windows". Its real work is two PowerShell scripts, which Wine cannot run either.
- **ARM64 runtime DLLs.** The prefix's `vcruntime140`, `vcruntime140_1` and `msvcp140` are ARM64; the x86-64 game cannot load them.
- **Wine's shader compiler.** The renderer compiles HLSL at runtime through `d3dcompiler_47`. Wine's built-in replacement (vkd3d-shader) rejects `SV_ClipDistance` in the runtime-compiled `Scene.vert`, and D3D12Drv dereferences the failed shader and crashes right after "stereo session begun".
- **The crash flag.** A crash leaves `System64\Running.ini`, and the next start opens a "not shut down properly" recovery dialog that is invisible in VR.
- **SteamVR rejects the menu panel.** The menu, HUD and intro text are one panel submitted as two `XrCompositionLayerQuad` layers, eye LEFT from array slice 0 and eye RIGHT from slice 1 of an `arraySize=2` swapchain. SteamVR on the Frame rejected every `xrEndFrame` carrying that pair with `compositor failed EndFrame()` and `XR_ERROR_POSE_INVALID` (-39), although the quaternion was unit length. Menus showed on the monitor and in theater mode, never in the headset.
- **SteamVR's Touch-to-Frame remap.** The game suggests Touch and Index bindings. SteamVR's automatic translation drives each bumper from its trigger, and with two profiles in the input context a custom Frame binding is ignored (the same finding as [Red Faction VR](../red-faction-vr/)).

## The fix

1. **Install on a Windows PC, then copy.** The installer was run silently on a PC with the same paths the prefix uses, so no config needed rewriting; the finished folder was tarred into the shortcut's prefix at `C:\Games\Unreal Revived` and the PC install removed. No absolute paths live in its configs.

   ```
   UnrealRevived-Setup-0.9.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER /DIR="C:\Games\Unreal Revived" /TASKS="" /OriginalGameRoot="C:\Unreal"
   ```

2. **VC++ runtime:** x86-64 copies of the three DLLs next to the exe (`ur_launch.sh` finds them in other prefixes).
3. **Shader compiler:** Microsoft's x64 `d3dcompiler_47.dll` from a Windows PC's `System32` next to the exe, with `WINEDLLOVERRIDES=d3dcompiler_47=n,b` set by the wrapper. That DLL is Microsoft's and is not in this repository.
4. **Crash flag:** the wrapper deletes `System64\Running.ini` before each start.
5. **frame_quadfix**, an OpenXR API layer ([tools/frame-quadfix](../../tools/frame-quadfix/)), built on the Frame with clang and lld-link and registered as an implicit layer in the prefix's `HKLM` (`system.reg`, `Software\Khronos\OpenXR\1\ApiLayers\Implicit`). It rewrites each frame before the runtime sees it: the LEFT quad is shown to both eyes and the RIGHT quad dropped. Zero rejected frames afterwards. `FRAMEXR_QUAD=both|drop|pass` selects the mode; it logs to `frame_quadfix.log` next to the game.
6. **Controls without a VR restart:** the same layer forwards only the game's Touch profile suggestion (`FRAMEXR_PROFILES=all` disables that), so the input context holds one profile. `ur_controls.py` writes a `frame_controller`-typed binding over the auto-generated `steam.app.3358004613_oculus_touch_0_binding.json` and makes it read-only. SteamVR logs "Unable to write" and loads the Frame binding, with no VR session restart. The script also writes the `User.ini` binds and `VRAimMode=1` in `UnrealVR.ini` (aim with the right controller).

## Exact commands

The scripts live in this repo under `scripts/unreal-revived-vr/` and the layer under `tools/frame-quadfix/`; on the headset they sit in `~/PCVR/UnrealRevivedVR/` and `~/PCVR/UnrealRevivedVR/quadfix/`, with the shared helpers in `~/PCVR/bin/`.

```bash
# download and verify the installer, add the shortcut with its own prefix, mirror Steam's Unreal Gold at C:\Unreal
ssh frame "bash ~/PCVR/UnrealRevivedVR/ur_setup.sh"
# (install on a Windows PC as above, then copy C:\Games\Unreal Revived into the prefix's drive_c/Games/)

# first run points the shortcut at System64\UnrealRevivedVR.exe and copies the x86-64 VC++ runtime; every run reports
ssh frame "bash ~/PCVR/UnrealRevivedVR/ur_launch.sh 60"

# build frame_quadfix.dll, register it as an implicit layer in the prefix, install it next to the game
ssh frame "bash ~/PCVR/UnrealRevivedVR/quadfix/build.sh"

# Frame binding over the auto-generated Touch default, User.ini binds, VRAimMode
ssh frame "python3 ~/PCVR/UnrealRevivedVR/ur_controls.py"
```

Logs: the game's own log, SteamVR's `xrclient_UnrealRevivedVR.txt`, `frame_quadfix.log` beside the exe, and a Proton log under `~/PCVR/UnrealRevivedVR/logs/` when `debug` exists. The wrapper's `mode` file (`play`, `run`, `cmd`) runs other commands inside the prefix.

## Controls

On the [standard layout](../../FRAME-LAYOUT.md) with left bumper jump and left trigger crouch. Chain: Frame input, the game's per-hand `revived_motion` action, an Xbox pad bit, `Joy1` to `Joy12`, the `User.ini` bind.

| Hand | Input | Action |
|---|---|---|
| Right | Trigger | Fire |
| Right | Bumper | Alt-fire |
| Right | A | Use item |
| Right | B | Next item |
| Right | X | Translator |
| Right | Menu | Pause |
| Right | Stick | Turn |
| Right | Stick click | Recenter |
| Left | Trigger | Crouch |
| Left | Bumper | Jump |
| Left | Stick | Move |
| Left | Stick click, d-pad left | Previous item |
| Left | D-pad up / down | Weapons |
| Left | View | Translator |

Right Y, d-pad right and both grips are unbound: the game has only twelve pad buttons. Aim follows the right controller.

## Status and known issues

- Working in the headset at 72 fps with the layout above; every frame accepted with the layer in place.
- Microsoft's `d3dcompiler_47.dll` has to come from your own Windows installation.
- The Inno installer cannot run in the prefix; the PC-install-and-copy step is manual.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3358004613; rm -rf ~/.local/share/Steam/steamapps/compatdata/3358004613"
# then remove ~/PCVR/UnrealRevivedVR and the steam.app.3358004613 files in ~/.config/openvr/config/openxr (chmod 644 first)
```

## Files in this repo

- [ur_setup.sh](../../scripts/unreal-revived-vr/ur_setup.sh): downloads and verifies the installer, adds the shortcut with its own prefix, mirrors Steam's Unreal Gold for the installer.
- [urvr-shortcut.sh](../../scripts/unreal-revived-vr/urvr-shortcut.sh): the shortcut wrapper (prefix, `d3dcompiler_47` override, `Running.ini` cleanup, `mode` hooks, debug marker).
- [ur_launch.sh](../../scripts/unreal-revived-vr/ur_launch.sh): first-run exe setup, x86-64 runtime copies, launch with a log summary.
- [ur_controls.py](../../scripts/unreal-revived-vr/ur_controls.py) and [ur_frame_binding.json](../../scripts/unreal-revived-vr/ur_frame_binding.json): the Frame binding (layout and chain in the docstring), `User.ini` binds and `VRAimMode`.
- [tools/frame-quadfix/quadfix.c](../../tools/frame-quadfix/quadfix.c) and [build.sh](../../tools/frame-quadfix/build.sh): the OpenXR API layer and its clang build and registration.

## Credits

- kwstasg for Unreal Revived; OldUnreal for the 227 engine; Epic for Unreal Gold (game data not included).
- Valve for SteamVR, Proton and wineopenxr; the vkd3d-proton and Khronos OpenXR loader projects.
- This repo holds only scripts, the binding and the layer source. No game data, no installer, no DLLs.
