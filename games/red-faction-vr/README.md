# Red Faction VR (Alpine Faction VR)

**Status:** Working. Runs under Proton; the standard controller layout needed a patched, rebuilt mod. Confirmed in the headset on 2026-10-23.

| | |
|---|---|
| Upstream | [CactusVRStudios/alpinefactionVR](https://github.com/CactusVRStudios/alpinefactionVR) 1.1 beta (MPL-2.0; a fork of Alpine Faction / Dash Faction). 32-bit, OpenXR on a forced Direct3D 11 renderer |
| Game data | Red Faction (Steam 20530). The mod's installer converts the Steam `RF.exe` into the 1.20 NA executable it requires |
| Route | Proton Experimental (ARM64) + FEX, in Red Faction's own prefix; the i386 wineopenxr bridges the 32-bit OpenXR session to SteamVR |
| Steam entry | Non-Steam shortcut "Red Faction VR" 3865968601 with red "RED FACTION VR" art; the library entry stays the flat game |
| Set up | 2026-10-23 |

## What it is

Cactus VR Studios' VR build of the Alpine Faction community patch for Red Faction (2001). Its README says SteamVR cannot run it because Windows SteamVR has no 32-bit OpenXR runtime. On the Frame, Proton's 32-bit wineopenxr bridges it straight into SteamVR, the same way F.E.A.R. VR works.

## What broke on the Frame

- **The mod's installer and Proton paths.** Alpine Faction refuses the Steam executable's checksum, so its Inno installer must run. It swaps `RedFaction.exe` for a Windows symlink that Linux cannot follow, and the launcher's "Executable Path" must be a `Z:` path: with Proton's `S:` game drive the launcher reports `tables.vpp` missing from a folder that plainly has it.
- **SteamVR, custom OpenXR bindings for Proton apps (three findings):**
  1. SteamVR builds a Proton OpenXR app's input context from auto-generated defaults (`~/.config/openvr/config/openxr/steam.app.<id>_<type>_N_binding.json`, rewritten every launch) and only honours the user-selected Frame-path file when that context holds a single interaction profile. This mod suggests Touch and Index; Quake II VR suggests only Touch, which is why its custom binding worked at once.
  2. A custom file with `controller_type: oculus_touch` is treated as Touch paths and pushed through the Frame remap, which drives each hand's trigger and bumper from the one Touch trigger, so bumper and trigger cannot differ. A file carrying a haptic entry for an action the app does not define (`Unknown action ... when loading binding file`) is dropped whole.
  3. The mod's actions were hand-scoped in code: jump and crouch accepted right-hand sources only, reload, flashlight, alt-fire and menu left-hand only, and under SteamVR the menu action was ignored in favour of a reload-plus-crouch hold chord.
- **The build.** The project documents a MinGW cross-build on Ubuntu 24.04, whose MinGW GCC 13 rejects the mod's C++23 "deducing this". The OpenXR loader needs `-DWINAPI_PARTITION_SYSTEM=0` under the project's `-Werror=undef`. The `shader_compiler.exe` steps fail (a Windows tool).

## The fix

- **Install:** the release zip's `VR Mod` folder goes into the game folder as is. The installer runs silently inside the game's prefix through the shortcut wrapper's `mode=run` hook with `/VERYSILENT /DIR=Z:\...\Red Faction`; it bsdiff-patches `RF.exe` into `RF_120na.exe` and points the launcher at it. Afterwards restore `RedFaction.exe` from its `.bak` (so the library entry stays the flat game) and keep the registry "Executable Path" (`HKCU\Software\Volition\Red Faction\Alpine Faction`) on a `Z:` path. Snap turn is set to 45° in the prefix's `user.reg` ("VR Snap Turn Degrees").
- **Single profile:** `rf_launch.sh` keeps the app's auto-generated Index default unwritable (a read-only `{}`), so SteamVR logs `SetXrInputConfig failed. Unable to write` and `Loading 1 bindings`, and the custom Frame binding applies.
- **Binding file:** `rf_binding.py` writes `rf_frame_binding.json` with `controller_type` `frame_controller`, the Touch interaction profile, poses on `openxr_grip` and `openxr_aim`, and `"haptics": []`.
- **Mod patch and rebuild:** `rf_patch.py` (idempotent) creates the six hand-scoped actions for both hands and reads them with `XR_NULL_PATH`, makes the pause press `input.menu || chord_held`, and adds a `recenter` action that calls the mod's own `recenter_tracking()`. The build runs in a podman container (`container/Containerfile`, image `afvr-mingw14`, Debian trixie with MinGW GCC 14) with `-DWINAPI_PARTITION_SYSTEM=0`. The failed shader steps do not matter: the compiled shaders ship in `alpinefaction.vpp`. The patched `AlpineFaction.dll` replaces the shipped one (kept as `.orig`); `AlpineFactionVR.exe` is left as shipped.

## Exact commands

The scripts live in this repo under `scripts/red-faction-vr/` and are copied to `~/PCVR/RedFactionVR/` on the headset, with the mod source cloned at `~/PCVR/RedFactionVR/src` and the shared helpers in `~/PCVR/bin/`.

```bash
# run the Inno installer silently inside Red Faction's prefix (converts RF.exe to 1.20 NA), restore RedFaction.exe
ssh frame "bash ~/PCVR/RedFactionVR/rf_setup.sh"

# build the MinGW GCC 14 container image and do the first full build of the patched mod
ssh frame "bash ~/PCVR/RedFactionVR/rf_build2.sh"

# later cycles: re-patch, incremental ninja in the container, install AlpineFaction.dll, rebind, relaunch
ssh frame "bash ~/PCVR/RedFactionVR/rf_rebuild.sh"

# write and select the Frame binding (one VR session restart after the first selection)
ssh frame "python3 ~/PCVR/RedFactionVR/rf_binding.py"
ssh frame "python3 ~/PCVR/bin/vrsettings_bind.py steam.app.3865968601 openxr ~/PCVR/RedFactionVR/rf_frame_binding.json"

# launch through Steam, keep the Index default unwritable, report the mod's OpenXR log
ssh frame "bash ~/PCVR/RedFactionVR/rf_launch.sh 60"
# AlpineFaction.log: Runtime: SteamVR/OpenXR 2.18.2 · Enabled extension: XR_KHR_D3D11_enable · Eye swapchains 1728x1728 · OpenXR session begun
```

Logs: `<game>/logs/AlpineFaction.log`, `AppData/Roaming/Alpine Faction VR/AlpineFactionVR.log` in the prefix, and SteamVR's `xrclient_RF_120na.txt`. `touch ~/PCVR/RedFactionVR/debug` adds a Proton log; `env.test` is sourced by the wrapper.

## Controls

On the [standard layout](../../FRAME-LAYOUT.md) after the mod patch.

| Hand | Input | Action |
|---|---|---|
| Right | Trigger | Fire |
| Right | Bumper | Alt-fire |
| Right | A | Laser sight |
| Right | B | Reload |
| Right | X | Flashlight |
| Right | Menu | Pause |
| Right | Stick | Snap turn 45°, weapon cycle |
| Right | Stick click | Recenter (the new `recenter` action) |
| Right | Grip (80%) | The mod's alt-fire modifier |
| Left | Trigger | Crouch |
| Left | Bumper | Jump |
| Left | Grip (80%) | Use, two-hand grab |
| Left | Stick | Move |
| Left | Stick click | Holster |

Deviations: A is the laser sight and the left stick click is holster; Y, view and the d-pad are free because the mod has no further actions.

## Status and known issues

- Working in single player with the layout above.
- Multiplayer aim does not follow the controller; the mod itself calls multiplayer unsupported.
- The HUD and menus are quads fixed at the recenter anchor: recenter (right stick click) once in, especially if the headset was off at launch.
- The first Steam launch of the flat game waits on a dialog in the headset; the VR shortcut does not.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 3865968601; cd ~/.local/share/Steam/steamapps/common/'Red Faction' && mv AlpineFaction.dll.orig AlpineFaction.dll"
# or verify Red Faction's files in Steam to drop the mod entirely; remove ~/PCVR/RedFactionVR and the
# steam.app.3865968601 section of ~/.config/openvr/config/steamvr.vrsettings
```

## Files in this repo

- [rf_setup.sh](../../scripts/red-faction-vr/rf_setup.sh): runs the installer silently inside the prefix through the wrapper's `mode=run` hook.
- [rfvr-shortcut.sh](../../scripts/red-faction-vr/rfvr-shortcut.sh): the shortcut wrapper (prefix, debug marker, `mode` hooks).
- [rf_patch.py](../../scripts/red-faction-vr/rf_patch.py): the idempotent mod patch (both-hand actions, menu pause, recenter). MPL-2.0 like the mod.
- [container/Containerfile](../../scripts/red-faction-vr/container/Containerfile) and [rf_build2.sh](../../scripts/red-faction-vr/rf_build2.sh): the MinGW GCC 14 image and the full build.
- [rf_rebuild.sh](../../scripts/red-faction-vr/rf_rebuild.sh) and [rf_install_dll.sh](../../scripts/red-faction-vr/rf_install_dll.sh): the incremental rebuild and DLL install cycle.
- [rf_binding.py](../../scripts/red-faction-vr/rf_binding.py) and [rf_frame_binding.json](../../scripts/red-faction-vr/rf_frame_binding.json): the Frame binding.
- [rf_launch.sh](../../scripts/red-faction-vr/rf_launch.sh): launch with the single-profile trick and a log report.

## Credits

- Cactus VR Studios for Alpine Faction VR; GooberRF's Alpine Faction and Dash Faction it is built on (MPL-2.0).
- Red Faction by Volition (game data from Steam, not included).
- Valve for OpenVR, SteamVR, Proton and wineopenxr.
- This repo holds only patches, scripts and configuration. No game data, no mod archive, no built binaries.
