# Dragon Ball FighterZ

**Status:** Dead end — anti-cheat. The game's Easy Anti-Cheat client needs a Linux-side module that only publishers who opted into Proton support receive, and nothing in the launch chain can supply it.

| | |
|---|---|
| Steam app | 678950, 7 GB |
| Engine / VR API | Unreal 4 (project "RED"), Direct3D 11; flat game, no VR |
| Anti-cheat | Easy Anti-Cheat (classic, game id 183); Valve rating "Unsupported anti-cheat configuration" |
| Route | Proton 11.0 (ARM64) + FEX, Steam's default compat tool, left at default |
| Diagnosed | 2026-10-09, eight test launches |

## What it is

Dragon Ball FighterZ is a flat Windows game on Unreal 4 with Direct3D 11. It was tested on the Frame as a plain Proton title. `DBFighterZ.exe` at the install root is the Easy Anti-Cheat launcher. The real game is `RED/Binaries/Win64/RED-Win64-Shipping.exe`.

## What you see

Steam shows the game running, then about a minute later it is back to Play. Every attempt since 6 October ended this way, by itself, with exit code 0 and no error shown.

## Why it fails on the Frame

- The launcher step works. Under Proton the EAC launcher is handled by Proton's EAC shim, which reports success in `gamelauncher.log` ("Easy Anti-Cheat successfully loaded in-game") and starts the game with `-eac-nop-loaded`.
- The game then takes about 55 seconds to initialise under FEX (the 184 MB exe has to be translated), creates its 1280x720 Unreal window and a working DXVK swapchain, and one second later initialises its own anti-cheat client. With file tracing on, that step reads:

```
GetFileAttributesW "S:/.../DRAGON BALL FighterZ/EasyAntiCheat/easyanticheat_x64.dll"
Loaded "S:\...\EasyAntiCheat\easyanticheat_x64.dll"
CreateFileW "C:\users\steamuser\AppData\Roaming\EasyAntiCheat\183\easyanticheat_wine_x64.eac"
warn: Unable to create file ... easyanticheat_wine_x64.eac (status c0000034)   <- not found
Unloaded "S:\...\EasyAntiCheat\easyanticheat_x64.dll"
```

- `easyanticheat_wine_x64.eac` is the Wine build of the EAC client. Epic's servers hand it to the launcher only for games whose publisher turned on Linux support in the EAC backend. The launcher's `183/loader.log` shows it contacting the CDN and getting nothing to download.
- Without that module the client fails to start, and the game treats that as "anti-cheat missing": it tears down audio, closes its window about three seconds after showing it, flushes its ini files and exits normally. No dialog is shown.
- How the cause was narrowed down: windowed mode, Proton Experimental (ARM64), bypassing the launcher with a wrapper (with and without `-eac-nop-loaded`), and renaming `EasyAntiCheat_x64.dll` so the client could not load at all made no difference. The last one fails the same initialisation, so it fails the same way.

### The Windows modding trick, and why it does not transfer

On Windows, the Unverum mod manager runs this game without anti-cheat for offline modded play. Its current source does not patch any bytes. It makes a plain copy of the exe named `RED-Win64-Shipping-eac-nop-loaded.exe` and launches that, because the game's EAC integration treats an executable with that name as "anti-cheat deliberately not loaded".

That was tried on the Frame too. The renamed copy still loads `EasyAntiCheat_x64.dll`, the DLL still fails for lack of its Wine module, and the game still quits at the same point. On Windows the DLL initialises fine and simply does nothing in that mode. Under Wine it cannot initialise at all, and the game does not distinguish the two.

Older Unverum releases shipped byte-patched executables for this game. That is the only remaining route and it was not pursued.

## What was tried

- Stock launch on Proton 11.0 (ARM64): exits by itself about a minute in, exit code 0.
- Windowed mode: no difference.
- Proton Experimental (ARM64): no difference.
- Wrapper that bypasses the EAC launcher and starts `RED-Win64-Shipping.exe` directly, with and without `-eac-nop-loaded`: no difference.
- Renaming `EasyAntiCheat_x64.dll` so the client cannot load at all: same failure at the same point.
- The Unverum trick (a copy of the exe named `RED-Win64-Shipping-eac-nop-loaded.exe`): same failure at the same point.
- File tracing to attribute the exit to the missing `easyanticheat_wine_x64.eac`.

## What would fix it

- **The publisher:** enable Easy Anti-Cheat's Linux module for the game. That is the Steam Deck "Verified" path and it would make the Frame work too, FEX permitting. Valve's compatibility tests already flag exactly this.
- **Next step if revisited:** none from user space. The only remaining route is a byte-patched executable from older Unverum releases, which was not pursued.

## State left on the headset

Launch options are empty, the compat tool is Steam's default, the renamed copy and the test wrapper were removed, and the install is untouched.

## Credits

- Unverum mod manager, whose source documents the `-eac-nop-loaded` executable-name behaviour.
