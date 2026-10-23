# XCOM 2 controller layout

**Status:** Working. The game runs; the controls were the problem. Steam loads a 2016 Steam Controller layout that drives a mouse pointer, so the Frame controllers never reached the game's own gamepad scheme.

| | |
|---|---|
| Steam app | 268500, 75 GB |
| Engine / VR API | flat game, no VR |
| Route | Proton + FEX (Steam's default) |
| Fix | Steam Input layout to the Gamepad template; in game, Input Device = Controller |
| Date | worked out 2026-10-08, confirmed working on the headset 2026-10-09 |

## What it is

XCOM 2 is a flat Windows title played on the Frame's theater screen. Nothing about launching it needed fixing. This write-up is only about getting the Frame controllers to drive the game's native gamepad scheme.

## What you see

- The right stick moves a mouse pointer and the triggers click.
- There is no direct ability selection.

## What broke on the Frame

- **Steam Input.** Steam's controller config for the Frame (`Steam Controller Configs/<userid>/config/configset_SteamFrameVirtual.vdf`) maps XCOM 2 to workshop layout 642172159, "XCOM2 Configuration", made in March 2016 for the original Steam Controller. It drives the right trackpad as an absolute mouse, the triggers as mouse buttons, and puts abilities 1-10 on a left-trackpad touch menu. The Frame has no trackpads, so camera panning and the ability radial are silently dropped. The paired Xbox pad config (`configset_controller_xboxone.vdf`) points at the same layout.
- Steam Input is forced on for the game (`UseSteamControllerConfig 2` in localconfig), which is normal on SteamOS.
- **The game itself.** It ships with gamepad support switched off by default (`bForceEnableController = false` in `DefaultInput.ini`; the store lists controller support as none) but the user `XComInput.ini` carries a full set of `XboxTypeS_*` bindings, so the native scheme is there once the game is told to use it.
- An edit made in the layout editor on the headset was reverted to the workshop layout two minutes later (`controller.txt`), which is why it felt like nothing stuck.

## The fix

1. On the headset: XCOM 2, controller settings, change the layout from "XCOM2 Configuration" to the built-in **Gamepad** template (`controller_base/templates/gamepad_joystick.vdf`, a one-to-one xinput mapping).
2. In game, from the main menu only: Options, Interface, Input Device, Controller.
3. Optional: bind the grips to L3/R3 in the layout editor.

No launch options and no ini edits. Editing the configset files over SSH instead needs a Steam restart on the Frame, so the UI route is the simpler one. The same two steps apply to a paired Xbox controller, since Steam's config for that pad points at the same 2016 layout.

## Exact commands

None. Both steps are made in the headset UI.

## Check it worked

The right stick pans the camera instead of moving a pointer, and abilities are selected directly with the gamepad scheme.

## Status and known issues

Confirmed working on the test headset on 2026-10-09. If the layout reverts to "XCOM2 Configuration", reselect the Gamepad template; the game-side Input Device setting is only reachable from the main menu.

## Undo

Select "XCOM2 Configuration" again in the controller settings and set Input Device back to Mouse and Keyboard in the game's Options.

## Credits

No mod is involved. This repo holds only scripts, no game data or binaries.
