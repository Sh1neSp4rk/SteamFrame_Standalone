# Tribes 2 VR

**Status:** Dead end. The mod runs under Proton, but TribesNext's login helper crashes under FEX and the mod's 2D screens cannot fuse on the Frame's asymmetric lenses. Tried and uninstalled on 2026-10-23.

| | |
|---|---|
| Mod | [Bruhlitz/Tribes2VRmod](https://github.com/Bruhlitz/Tribes2VRmod), test build QOL-24 (folder `tribes2vr-QOL-24`: `tribes2vr.dll`, `tribes2vr.ini`, `tribes2vr_launcher.exe`). 32-bit MinGW DLL plus a launcher that starts the game and injects; OpenVR legacy input; OpenGL hooks on `wglSwapBuffers` and byte-patched exe addresses |
| Game | Tribes 2 (Steam app id 25034, free: `tribes2gsi.exe` from TribesNext, a Wise installer with no silent switch) plus TribesNext RC2a (NSIS, `/S`) |
| Route | Proton Experimental (ARM64) + FEX, in a shortcut-only prefix |
| Tried | 2026-10-23; everything removed the same day |

## What it is

A VR mod for the 2001 Tribes 2, injected into the free TribesNext-patched game: head tracking, a per-eye frustum, arm IK and legacy OpenVR controller input, with the 2D shell either on a menu overlay or submitted as a flat image.

## What you see

The game and the mod start. In the headset the 3D world renders with tracking, but the shell menus are doubled and never fuse, and TribesNext's login screen cannot authenticate.

## Why it fails on the Frame

- **FEX, TribesNext RC2a's login.** RC2a authenticates through a Ruby helper (`rubyintersect.dll` plus `msvcrt-ruby190.dll`). Under FEX it page-faults inside the Ruby runtime, so the TribesNext scripts then report an unpatched exe ("not a patched exe") and no account can log in or be created. `-nologin` reaches the offline LAN and Training shell only.
- **The mod, 2D screens on asymmetric lenses.** In the shell the mod submits one identical image to both eyes at full texture bounds. Its own log says so:

  ```
  no eye crop available - submitting full bounds, image will double
  ```

  The Frame's per-eye projections are wide and mirror-asymmetric (raw tangents left -1.65, right 1.22, top -1.73, bottom 1.17), so the same pixel lands at a different angle in each eye and the menus never fuse, with `menuOverlay` true or false.
- **The mod's other presentation modes.** The default crop mode (`frustumMode 3`) needs the game to draw a 144 degree vertical field of view to fill the lens, which it cannot ("VERTICAL IS SHORT ... stretched 407% taller"). Depth stereo (`stereoMode 2`) needs readable depth, and this engine leaves none behind under zink. `frustumMode 2` (the headset's per-eye projection) with `stereoMode 1` was configured for the 3D world but not tested before the decision to stop.

## What worked

- The mod needs a 32-bit `openvr_api.dll` beside it and does not ship one; the OpenVR SDK's `bin/win32` copy works through Proton's vrclient bridge.
- OpenVR came up at 72 fps, every engine hook (camera, frustum, arm IK, `Con::evaluate`) verified its byte signature against the RC2a-patched exe, and legacy controller input was alive.
- Steam strips backslashes from shortcut launch options, so the launcher's `C:\...\Tribes2.exe` argument arrived as `C:DynamixTribes2GameDataTribes2.exe`. The shortcut wrapper appended the Windows path itself; the launcher forwards extra arguments such as `-nologin` to the game.
- The Wise installer has no silent switch and was clicked through in the headset; TribesNext RC2a installed silently with `/S`.

## What would fix it

- **Online play:** the TribesNext 20250922 preview drops Ruby for native authentication and advertises Wine support. It was the untried next step, with the caveat that the mod's byte signatures are tied to a specific exe.
- **The shell, for the mod author:** a 2D-screen path that crops each eye from the submitted image using the `GetProjectionRaw` tangents (as the crop mode already does for 3D frames, but assuming the screen's own field of view instead of a game frustum), or that renders the screen quad per eye with the headset projection, would make the shell usable on wide-FOV headsets. Driving the menus through the SteamVR dashboard's desktop view would have been the workaround.
- **The 3D world:** test `frustumMode 2` with `stereoMode 1`.

## State left on the headset

The shortcut, its Proton prefix (with the game inside) and the mod folder were removed. The mod's READ-ME and a sha256 list of the downloads were kept for reference. The setup, launch and patch scripts from the attempt are not in this repository; say so in an issue if a retry needs them.

## Credits

- Bruhlitz for Tribes2VRmod; the TribesNext project for keeping Tribes 2 playable.
- Tribes 2 by Dynamix (game data not included).
