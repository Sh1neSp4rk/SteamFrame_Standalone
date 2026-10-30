# Monster Hunter Rise VR: REFramework VR with the Frame as an Xbox pad

**Status:** Working, streamed from a Windows PC. The Frame controllers act as a 1:1 Xbox pad, confirmed in the headset; a flat launch from Steam's normal entry stays flat. Not tried standalone on the Frame.

| | |
|---|---|
| Steam app | 1446780 (Monster Hunter Rise), build 17920865 |
| Engine / VR API | RE Engine, Direct3D 12; REFramework's VR talks to SteamVR through OpenVR |
| Mod | praydog's REFramework, nightly-01433: the universal `REFramework.zip` (`dinput8.dll`) plus `VR.zip` (`openvr_api.dll`) |
| Route | Windows PC (RTX 4080 Laptop) streaming to the Frame through SteamVR |
| Frame fixes | a launcher that turns VR on only for the VR entry, an XInput plugin that makes the Frame a gamepad, and its binding |
| Date | 2026-10-28 |

## What it is

REFramework's VR mode puts Rise in the headset as a third-person game in stereo with head tracking. There are no motion controls: you play with a gamepad. REFramework starts VR whenever `openvr_api.dll` sits beside `MonsterHunterRise.exe`, and `dinput8.dll` (REFramework itself) can stay in the game folder for flat play.

## What you see without the fix

The picture is fine, but the Frame controllers do nothing. For Rise, REFramework's VR uses the controllers only to recenter: its "VR controllers to RE Engine input" path is a TODO for this game, and with no real gamepad connected the game gets no input at all.

## What broke, and why

### Attempt 1: writing into the game's pad object (failed)

A REFramework Lua script ORed button bits into Rise's own pad (`snow.Pad.Device`: its `hard`, `app` and `sys` button words) after the game updated it. The result was the wrong buttons and a dead left stick: `app` already holds bits remapped through the key config, and `hard` is rebuilt from the layer below on every update. That approach works in Resident Evil 4 (a different object, `via.hid.GamePad`, which RE4VR also writes), not here.

### The fix: be the gamepad

Rise reads XInput every frame and nothing else feeds it, so the simplest place is XInput itself. [mhrise_framepad.c](../../scripts/mhrise-vr/mhrise_framepad.c) is a REFramework plugin (`reframework\plugins\mhrise_framepad.dll`) that:

- inline-hooks `xinput1_4`'s `XInputGetState`, its `XInputGetStateEx` twin (ordinal 100) and `XInputGetCapabilities` with MinHook. Inline, not through the import table, because the packed exe resolves XInput at runtime.
- while `openvr_api.dll` is loaded, reports XInput user 0 as a connected Xbox pad built from REFramework's own OpenVR actions, read in-process through `VR_GetGenericInterface("IVRInput_010")` (same process, same action manifest). Left and right are told apart by restricting each read to one hand.
- merges a real pad on user 0 if there is one, and passes everything through untouched on a flat launch.

REFramework's action manifest has no bumper or X/Y actions of its own, so the binding borrows actions that REFramework only uses for other games: X and Y on `Block` and `Heal`, both bumpers on `RE2_Quickturn` (left or right hand = LB or RB), Menu and View on `SystemButton` (right = Start, left = Back). [mhrise_frame_binding.json](../../scripts/mhrise-vr/mhrise_frame_binding.json) is the whole binding. REFramework rewrites `actions.json` and its default bindings on every launch, which is why the binding lives elsewhere and is selected in `steamvr.vrsettings`.

## Steps (Windows PC)

1. **REFramework:** from praydog's REFramework nightly releases, put `dinput8.dll` from `REFramework.zip` in the game folder, and keep `openvr_api.dll` from `VR.zip` in a `_vr` folder inside the game folder (not beside the exe).
2. **The VR launcher:** copy [Launch-MHRiseVR.ps1](../../scripts/mhrise-vr/Launch-MHRiseVR.ps1) into `_vr`. It copies `openvr_api.dll` beside the exe, runs `steam.exe -applaunch 1446780`, waits for the game to exit, deletes the DLL again (retrying while it is still locked) and logs to `_vr\launcher.log`. It assumes Steam is in `C:\Program Files (x86)\Steam`.
3. **The plugin:** build it with MinGW gcc (WinLibs) and the MinHook 1.3.3 source:
   ```
   gcc -O2 -shared -o mhrise_framepad.dll mhrise_framepad.c <minhook>/src/*.c <minhook>/src/hde/hde64.c -I<minhook>/include -static-libgcc
   ```
   and put it in `reframework\plugins\`.
4. **The binding:** copy `mhrise_frame_binding.json` into `_vr` and select it with SteamVR closed:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\common\vrsettings_bind.ps1 -App steam.app.1446780 -Kind steamvrinput -Binding "<Rise>\_vr\mhrise_frame_binding.json" -StopSteamVR
   ```
5. **Library entry:** in Steam, Add a Non-Steam Game pointing at `powershell.exe` with the launch options `-ExecutionPolicy Bypass -WindowStyle Hidden -File "<Rise>\_vr\Launch-MHRiseVR.ps1"`, name it "Monster Hunter Rise (VR)" and tick "Include in VR Library". The normal Monster Hunter Rise entry stays flat.
6. If presses register twice, turn Steam Input off for Rise (Properties → Controller); with it on, Steam can expose a second pad.

## Controls: 1:1 with flat

| Frame | Game sees |
|---|---|
| A / B / X / Y | A / B / X / Y |
| Left / right bumper | LB / RB |
| Left / right trigger | LT / RT (analog) |
| Sticks and clicks | left / right stick, L3 / R3 |
| D-pad | D-pad |
| Menu / View | Start / Back |
| Grips | not sent to the game |

Rise's own controller settings and key config then apply exactly as with an Xbox pad.

## Check it worked

- `reframework\data\mhrise_framepad.log`: `hook XInputGetState: MH_OK`, `hook XInputGetStateEx(#100): MH_OK`, `hook XInputGetCapabilities: MH_OK`, then `OpenVR input ready (left=... right=...)` once the headset session is up.
- `_vr\launcher.log`: `openvr_api.dll installed, launching`, `game running`, and after quitting `cleanup done (dll present: False)`.
- SteamVR's `vrserver.txt` loads `mhrise_frame_binding.json` for `steam.app.1446780`.

## Status and known issues

- If the game is killed and `cleanup done` never runs, `openvr_api.dll` stays beside the exe and the next normal launch starts in VR. Delete it, or run the VR entry once and quit normally.
- A REFramework update that changes its action names needs the binding redone.
- Not tried standalone on the Frame.

## Files in this repo

- [mhrise_framepad.c](../../scripts/mhrise-vr/mhrise_framepad.c): the XInput plugin.
- [mhrise_frame_binding.json](../../scripts/mhrise-vr/mhrise_frame_binding.json): the Frame binding.
- [Launch-MHRiseVR.ps1](../../scripts/mhrise-vr/Launch-MHRiseVR.ps1): VR on for this launch only.
- [../common/vrsettings_bind.ps1](../../scripts/common/vrsettings_bind.ps1): selects the binding.

## Credits

- REFramework by praydog (MIT). MinHook by Tsuda Kageyu (BSD-2-Clause). Neither is included here.
