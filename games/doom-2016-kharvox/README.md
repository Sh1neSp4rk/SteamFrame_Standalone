# DOOM (2016) VR: KHARVOX with 1:1 Frame controls

**Status:** Working, streamed from a Windows PC. KHARVOX's motion controls plus flat DOOM's Xbox layout on the Frame's buttons, confirmed in the headset. Not tried standalone on the Frame (KHARVOX is a Windows Vulkan layer plus an OpenXR session, with a Windows launcher).

| | |
|---|---|
| Steam app | 379720 (DOOM, 2016) |
| Engine / VR API | idTech 6, Vulkan (`DOOMx64vk.exe`); KHARVOX talks to SteamVR through OpenXR |
| Mod | KHARVOX 1.11 by CactusVR Studios (https://github.com/CactusVRStudios/KHARVOX, source commit ff348bb) |
| Route | Windows PC (RTX 4080 Laptop) streaming to the Frame through SteamVR |
| Frame fixes | the frame_doompad OpenXR API layer, a Frame binding that drives it, and a Steam library entry |
| Date | 2026-10-17 (install) to 2026-10-27 (Frame controls) |

## What it is

KHARVOX is a total VR conversion for DOOM (2016): room-scale 6DoF, tracked hands and stereo rendering through a Vulkan layer (`KharvoxLayer.dll`). You start it from `KharvoxLauncher.exe`, which patches DOOM's campaign gamepad binds, starts DOOM with the layer and hands input to the game as a virtual Xbox pad: an `XInputGetState` import hook in `DOOMx64vk.exe`, fed from KHARVOX's OpenXR actions.

## What you see without the fix

KHARVOX has 12 OpenXR actions, designed around Quest controllers. LT, LB, RB, X, Y, L3, View, Menu and the D-pad have no action of their own; KHARVOX reaches those Xbox buttons through gestures and stick directions (stick up/down for chainsaw and weapon select, the left stick click for the menu). The Frame has every Xbox button, but SteamVR can only bind a Frame button to an action the game declared, so most of them do nothing.

## The fix

### The frame_doompad layer

[doompad.c](../../scripts/doom-2016-kharvox/doompad.c) is an implicit OpenXR API layer that sits between KHARVOX and SteamVR:

- It adds an action set `framepad` with A, B, LB, RB, X, Y, L3, View, Menu, the four D-pad directions and LT. Each frame (`xrSyncActions`) it reads them and ORs the matching XInput bits into what DOOM's `XInputGetState` import returns. DOOM's own campaign gamepad binds then apply exactly as in flat play.
- It wraps DOOM's import slot around whatever is in it when the session attaches. KHARVOX patches that slot once, before it even creates its OpenXR instance, so the wrapper sits outside KHARVOX's hook and sees its finished virtual pad.
- While RB is held DOOM's weapon wheel is open: the physical right stick then goes to DOOM's right stick for the wheel, and KHARVOX's turn reads centered so the view does not turn at the same time.
- The vertical axis of KHARVOX's turn stick reads 0: KHARVOX maps stick up/down to chainsaw and weapon select, which X and RB now do, and a flat player's "look up" would otherwise rev the chainsaw. `FRAMEXR_DOOM_STICK_Y=1` keeps it.
- D-pad right: the KHARVOX launcher rebinds that channel to Use on every launch (and D-pad left to `_quick2`). The layer sends D-pad right plus the keyboard Z key, which the campaign binds to the same equipment cycle.
- A and B match flat with KHARVOX's default (unswapped) jump/crouch. Frame A is a plain Xbox A (jump, confirm). Frame B drives KHARVOX's own crouch action (so its camera follows the crouch) plus a plain Xbox B (crouch, back), and the layer drops the menu A that KHARVOX derives from its crouch action, so B goes back in menus.
- Only the Oculus Touch interaction profile is forwarded, so SteamVR honours the Frame-typed binding.
- It is active only in `DOOMx64vk.exe` / `DOOMx64.exe`. `DISABLE_FRAME_DOOMPAD=1` turns it off. It logs to `frame_doompad.log` in DOOM's folder.

It is built freestanding with clang for `x86_64-pc-windows-msvc` and imports a handful of msvcrt, kernel32 and user32 functions, so no Windows SDK or Visual Studio is needed: [build.sh](../../scripts/doom-2016-kharvox/build.sh) runs on the Frame (clang, lld and the OpenXR headers are there) or any Linux box and writes `out/frame_doompad.dll` and `out/frame_doompad.json`.

### The binding

[kharvox_binding.py](../../scripts/doom-2016-kharvox/kharvox_binding.py) writes [kharvox_frame_binding.json](../../scripts/doom-2016-kharvox/kharvox_frame_binding.json): KHARVOX keeps what needs motion awareness (move, turn, fire, B's crouch, R3 melee/use, the grips for two-hand support and the shoulder weapon), and every other Frame button goes to `framepad`. KHARVOX's own equipment, pause, mission-info and weapon-mod actions are left unbound because `framepad` sends LB, Start, Back and D-pad up 1:1 instead. Grips need an 80% squeeze and let go below 70%.

### Steps (Windows PC)

1. **Install KHARVOX**: extract the release into its own folder (here `C:\KHARVOX`, not inside DOOM) and run `KharvoxLauncher.exe` once so it finds DOOM. Leave the launcher's "Swap Jump/Crouch" off (the default).
2. **Build the layer** with `build.sh` on the Frame or a Linux box, and copy `frame_doompad.dll`, `frame_doompad.json` and `kharvox_frame_binding.json` into `C:\KHARVOX\frame-doompad\`.
3. **Register the layer** for your user: double-click [register-frame-doompad.reg](../../scripts/doom-2016-kharvox/register-frame-doompad.reg). It adds `C:\KHARVOX\frame-doompad\frame_doompad.json` under `HKCU\SOFTWARE\Khronos\OpenXR\1\ApiLayers\Implicit`; edit the path first if KHARVOX lives elsewhere. Per-user is enough: the KHARVOX launcher does not run elevated.
4. **Select the binding** with SteamVR closed:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\common\vrsettings_bind.ps1 -App steam.app.379720 -Kind openxr -Binding C:\KHARVOX\frame-doompad\kharvox_frame_binding.json -StopSteamVR
   ```
   Start SteamVR again.
5. **Library entry (optional):** put [Start-Kharvox.ps1](../../scripts/doom-2016-kharvox/windows/Start-Kharvox.ps1) and [Add-KharvoxSteamShortcut.ps1](../../scripts/doom-2016-kharvox/windows/Add-KharvoxSteamShortcut.ps1) in the KHARVOX folder and run the second one. It closes Steam, adds "DOOM (KHARVOX VR)" with the VR flag to `shortcuts.vdf` (no drive letter: PowerShell looks for `\KHARVOX\Start-Kharvox.ps1` on every drive), copies any art in `.\artwork` to Steam's grid folder and starts Steam again. `Start-Kharvox.ps1` points the launcher's saved DOOM path at the DOOM install (beside KHARVOX on the same drive, or found through Steam's `libraryfolders.vdf`) and starts `KharvoxLauncher.exe`.

## Controls: 1:1 with flat

| Frame | Game sees | Through |
|---|---|---|
| Right trigger | Fire | KHARVOX |
| Left trigger | LT: weapon mod | framepad |
| Left bumper | LB: equipment | framepad |
| Right bumper | RB: change weapon; hold = weapon wheel with the right stick | framepad |
| A | A: jump, confirm | framepad |
| B | B: crouch, back | KHARVOX crouch + framepad |
| X / Y | X: chainsaw / Y: BFG | framepad |
| Right stick / click | turn / R3: melee, use | KHARVOX |
| Left stick / click | move / L3 | KHARVOX / framepad |
| View / Menu | dossier / pause | framepad |
| D-pad | up weapon mod, down objectives, left/right equipment | framepad |
| Grips (80%) | two-hand support, tap equipment, hold BFG (left); weapon mod in front, shoulder weapon behind (right) | KHARVOX |

## Check it worked

- `frame_doompad.log` in DOOM's folder: `frame_doompad active in DOOMx64vk.exe`, then a `buttons 0x....` line per press and `RB held: right stick -> DOOM weapon wheel` / `RB released` around the wheel.
- SteamVR's `vrserver.txt` loads `kharvox_frame_binding.json` for `steam.app.379720`.

## Status and known issues

- **Moving KHARVOX or DOOM** to another drive needs the layer path in the registry, `KharvoxLayer.json` (KHARVOX's own Vulkan layer manifest), `%LOCALAPPDATA%\KHARVOX\settings.json` (`GamePath`) and the binding selection updated. `Start-Kharvox.ps1` fixes `GamePath` itself.
- A KHARVOX update that changes its action list or its XInput hook may need the binding or the layer redone.
- Not tried standalone on the Frame.

## Undo

Double-click [unregister-frame-doompad.reg](../../scripts/doom-2016-kharvox/unregister-frame-doompad.reg), delete `C:\KHARVOX\frame-doompad`, and remove the two `frame_controller_*` keys under `steam.app.379720` in `steamvr.vrsettings` with SteamVR closed (or restore the `.bak-` copy the helper made).

## Files in this repo

- [doompad.c](../../scripts/doom-2016-kharvox/doompad.c), [build.sh](../../scripts/doom-2016-kharvox/build.sh), [frame_doompad.json](../../scripts/doom-2016-kharvox/frame_doompad.json): the layer, its build and its manifest.
- [kharvox_binding.py](../../scripts/doom-2016-kharvox/kharvox_binding.py) / [kharvox_frame_binding.json](../../scripts/doom-2016-kharvox/kharvox_frame_binding.json): the Frame binding.
- [register-frame-doompad.reg](../../scripts/doom-2016-kharvox/register-frame-doompad.reg) / [unregister-frame-doompad.reg](../../scripts/doom-2016-kharvox/unregister-frame-doompad.reg): per-user layer registration for `C:\KHARVOX`.
- [windows/Start-Kharvox.ps1](../../scripts/doom-2016-kharvox/windows/Start-Kharvox.ps1), [windows/Add-KharvoxSteamShortcut.ps1](../../scripts/doom-2016-kharvox/windows/Add-KharvoxSteamShortcut.ps1): drive-independent launch and the Steam library entry.
- [../common/vrsettings_bind.ps1](../../scripts/common/vrsettings_bind.ps1): selects the binding.

## Credits

- KHARVOX by CactusVR Studios (GitHub, Flat2VR Discord). Not included here; get it from its releases page.
