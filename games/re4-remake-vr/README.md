# Resident Evil 4 (2023) VR: RE4VR with 1:1 Frame controls

**Status:** Working, streamed from a Windows PC. RE4VR's motion controls plus the flat game's Xbox layout on the Frame's buttons, confirmed in the headset on 2026-10-28. Not tried standalone on the Frame (a Direct3D 12 RE Engine game with a 74 GB install).

| | |
|---|---|
| Steam app | 2050650 (Resident Evil 4, the 2023 remake), 74 GB |
| Engine / VR API | RE Engine, Direct3D 12; the mod talks to SteamVR through OpenVR (OpenXR is also offered) |
| Mod | RE4VR 2.1.6 by Talemann (https://re4vr.com), built on praydog's REFramework |
| Route | Windows PC (RTX 4080 Laptop) streaming to the Frame through SteamVR |
| Frame fixes | a SteamVR binding that keeps RE4VR's own and adds the missing buttons, and a REFramework Lua script that writes them into the game's gamepad |
| Date | 2026-10-27 to 2026-10-28 |

## What it is

RE4VR turns the remake into a first-person motion-controlled game: guns are drawn and aimed with the grips, reloads are manual, and knives, grenades and the flashlight are physical. It ships as an installer that sets up REFramework, removes any other RE4 mods and asks two questions: OpenVR or OpenXR, and Steam or Meta. Since 2.1.4 it has a Steam Frame button layout of its own, and since 2.1.5 it no longer needs the ViGEm bus driver.

## What you see without the fixes

RE4VR's Frame layout is the Quest layout moved onto the Frame's buttons, not the Xbox layout the flat game teaches:

| Frame button | RE4VR 2.1.6 | Flat game (Xbox, control type A-1) |
|---|---|---|
| B | Command Ashley (tap) / map (hold) | Back in menus, crouch |
| X | Manual reload | Reload |
| Right stick click | Crouch | R3 |
| Left / right bumper | Nothing | LB knife / parry, RB run; menu tabs |
| View | Pause (same as Menu) | Map |
| Grips | Gun draw and knife; LB / RB in menus | (none on an Xbox pad) |

The game's tutorials ask for buttons that do nothing, crouch is only on the stick click, menus switch tabs with the grips, and in some menus there is no way back without a keyboard.

## What broke, and why

### 1. Steam Input

With Steam Input on, the controllers track but no button reaches the game. The mod's FAQ says to turn it off for RE4. This is also why the library shortcut below starts the real app rather than `re4.exe`.

### 2. "Fatal D3D error (6, E_OUTOFMEMORY)"

The first launch died with this error. At the same second Brave, RustDesk and SteamVR's web helper also died of out-of-memory. The PC's commit limit (32 GB RAM plus pagefile) was full: Firefox alone held about 20 GB across 92 processes, and the pagefile could not grow because C: was nearly full. RE4 in VR needs a lot of commit. Close the browsers before playing.

### 3. The game ignores XInput during play

RE4VR's `xinput1_4.dll` is not a real XInput: it is a virtual pad (exports `RE4VR_SetPad`, `RE4VR_ReleasePad`, `RE4VR_GetRumble`) that imports nothing but KERNEL32. On load it rewrites `re4.exe`'s XInput imports to point at its internal functions, and its exports are only `jmp` stubs. More importantly, RE4 calls XInput once at startup and then reads the engine's own gamepad object, `via.hid.GamePad`, which is where RE4VR writes its buttons. Hooking XInput (tried first, as a REFramework plugin) adds nothing: the hook fires once and never again.

### 4. RE4VR's VR menu reads its own actions

RE4VR's mod menu (left trigger + Y) does not read the gamepad; it reads RE4VR's OpenVR actions. Its "back" lives on the action that RE4VR binds to the Frame's B button (`Frame_LeftA`). Taking B away from that action leaves no way to back out of the menu. So the fix never removes an RE4VR binding; it only adds to them.

## The fix

Two pieces, both in this repo:

- **A binding** with every RE4VR Frame binding plus five more: both bumpers on REFramework's spare `Block` action, right B and left View on `Heal`, right stick click on `MiniMap`. REFramework declares these actions for other games' Lua scripts; RE4VR does not bind them. The script tells left and right apart by hand.
- **[re4_frame_xbox.lua](../../scripts/re4-remake-vr/re4_frame_xbox.lua)**, a REFramework autorun script. Every frame, after RE4VR has written its input, it reads those actions through REFramework's `vrmod` API and writes the matching buttons into `via.hid.GamePad`'s merged, current and last-input devices (`set_Button`, `set_ButtonDown`, `set_ButtonUp`, with down/up edges of its own). It re-applies at five engine stages (post `UpdateHID`, pre `UpdateBehavior`, `UpdateMotion`, `UpdateGUI`, `LateUpdateBehavior`) because RE4VR's write point is not documented; the writes are idempotent. B, Cancel, R3 and View come only from the physical buttons; it removes any copy RE4VR sends from its Quest-style remaps (Menu or the right stick as back, B as Ashley/map). LB and RB are added to whatever RE4VR sends, because RE4VR drives its grip knife through them.

### Steps (Windows PC)

1. **Install RE4VR** from https://re4vr.com: run `RE4VR_<version>_Setup.exe` and pick **OpenVR** (the installer recommends it for Index, Bigscreen and Steam Frame) and **Steam**. It is unsigned; SmartScreen asks once.
2. **Disable Steam Input** for RE4: Steam → right-click Resident Evil 4 → Properties → Controller → Disable Steam Input.
3. **Start the game once in VR** (Frame connected, SteamVR running), then quit. REFramework writes `bindings_frame.json` and `actions.json` into the game folder on every launch.
4. **Install the Frame controls** with RE4 closed:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\re4-remake-vr\windows\install-pc.ps1 -StopSteamVR
   ```
   It finds RE4 through Steam's library folders, copies the Lua script into `reframework\autorun`, writes `_framepad\re4_frame_binding.json` and selects it for `steam.app.2050650` (`frame_controller_CurrentURL_steamvrinput` and the `_250820_` variant) in `steamvr.vrsettings`. SteamVR rewrites that file while it runs, so the script closes SteamVR first (backup: `steamvr.vrsettings.bak-re4-frame`). Start SteamVR again afterwards.
5. **Optional library entry:** a non-Steam shortcut "Resident Evil 4 (VR)" with the OpenVR flag that runs `steam.exe -applaunch 2050650`. It must start the real app, not `re4.exe`: Steam Input settings belong to the app, and a shortcut to the exe would get its own, enabled. RE4VR loads on every launch, so the normal RE4 entry starts in VR too.

## Controls: 1:1 with flat

| Frame | Game sees | Notes |
|---|---|---|
| A | A (interact, confirm) | RE4VR |
| B | B (back / crouch) | script; also RE4VR's own VR-menu back |
| X | X (reload) | RE4VR's manual reload |
| Y | Y (inventory) | RE4VR; left trigger + Y opens the RE4VR / REFramework menu |
| Left / right bumper | LB (knife, parry) / RB (run), menu tabs | script |
| Left / right trigger | as RE4VR (fire on the right; left trigger + right stick = D-pad) | RE4VR |
| Grips | gun draw, knife, grab; also LB / RB in menus | RE4VR |
| Left stick / click | move / run | RE4VR |
| Right stick / click | turn / R3 | turn by RE4VR, R3 by the script |
| D-pad | D-pad (quick weapons) | RE4VR |
| View | View (map) | script |
| Menu | Start (pause) | RE4VR |

The game's own control type stays at the default, A-1.

## Check it worked

- `reframework\data\re4_frame_xbox.log`: `loaded`, then `entry hits after 600 frames: post UpdateHID=599, pre UpdateBehavior=599, ...` (all five stages), and a `physical buttons <hex>` line for each press (LB `100`, RB `400`, B `40080`, R3 `2000`, View `4000`). No `error` lines.
- `re2_framework_log.txt`: `[ScriptState] Running script ...re4_frame_xbox.lua...`.
- SteamVR's `vrserver.txt`: `Successfully loaded binding file '...\_framepad\re4_frame_binding.json' for app 'steam.app.2050650'`. The line `(frame_hmd) has no configured binding` is normal.

## Status and known issues

- **Reinstalling or updating RE4VR wipes `reframework\`.** Run `install-pc.ps1` again afterwards (it also regenerates the binding from the new `bindings_frame.json`).
- **RE4VR menu settings are easy to knock over with the wrong buttons.** On this PC, one session ended with REFramework's `VR_2DUIScale` and `VR_2DUIDistance` swapped (15 and 1), which put the menus huge and in your face; the REFramework overlay switched back on (RE4VR's `hide_ref_overlay`, toggled by left trigger + Y); and the upscaler changed. If menus suddenly look wrong, check `re2_fw_config.txt` (`VR_2DUIScale=1`, `VR_2DUIDistance=15`) and `reframework\data\re4_vr\re4_vr_bindings.json` (`hide_ref_overlay`), with the game closed.
- **The first-boot setup screen** (language, brightness) did not respond to the Frame controllers once; a mouse got past it. It only appears on the first launch.
- The grips still also switch menu tabs. Removing that would need knowing which LB/RB presses are RE4VR's knife.
- Not tested standalone on the Frame.

## Undo

Delete `reframework\autorun\re4_frame_xbox.lua` and the `_framepad` folder, and remove the two `frame_controller_*` keys under `steam.app.2050650` in `steamvr.vrsettings` (SteamVR closed), or restore `steamvr.vrsettings.bak-re4-frame`. RE4VR itself uninstalls with `unins000.exe` in the game folder.

## Files in this repo

- [re4_frame_xbox.lua](../../scripts/re4-remake-vr/re4_frame_xbox.lua): writes the Frame's bumpers, B, right stick click and View into RE4's engine gamepad.
- [windows/install-pc.ps1](../../scripts/re4-remake-vr/windows/install-pc.ps1): installs the script, builds the binding from RE4VR's own and selects it in SteamVR.

## Credits

- RE4VR by Talemann (https://re4vr.com; support in the Flat2VR Discord). Not included here; get it from its site.
- REFramework by praydog (MIT).
- Control type A-1 reference: GameWith's RE4 controls guide.
