# Metal: Hellsinger VR

**Status:** Working. A permanent black screen, fixed with one file: a Razer keyboard-lighting plugin needs `mfc140u.dll`, which Proton has never shipped.

| | |
|---|---|
| Steam app | 2878270 |
| Engine / VR API | Unity, OpenXR |
| Route | Proton 11.0 (ARM64) + FEX (fails the same on Experimental) |
| Fix | copy mfc140u.dll into the game folder |
| Date | fixed 2026-10-09 |

## What it is

The Steam VR build of Metal: Hellsinger, a Unity OpenXR title. It runs under Proton on the Frame once a single missing Microsoft library is placed next to the executable.

## What you see

- The "Up next" card with the logo appears, then black. No music, no intro video, no menu.
- Steam still shows the game as running and you can quit it from the Steam menu.
- Streaming from a PC is unaffected.

## What broke on the Frame

- **The game itself.** It ships a Razer Chroma plugin, `MetalVR_Data/Plugins/x86_64/CChromaEditorLibrary64.dll`. That plugin depends on `mfc140u.dll`, the Microsoft Foundation Classes runtime.
- **Proton.** Proton provides the common Visual C++ runtime files but has never shipped MFC, so the prefix has no `mfc140u.dll` at all.
- **Why it is black rather than a crash.** When the plugin fails to load, Unity throws inside the game's `Main.Initialize` coroutine. An exception ends a coroutine, so everything scheduled after the Chroma controller (audio, intro, menu) never runs. The VR session is already open by then, hence black rather than a crash to the dashboard.

From the game's `Player.log` in the prefix:

```
DllNotFoundException: Unable to load DLL 'CChromaEditorLibrary64'
  at RazerChromaController..ctor (Messenger messenger)
  at Main+<Initialize>d__66.MoveNext ()
```

The flat Metal: Hellsinger demo failed the same way on Linux in 2022 and players fixed it by installing `vcrun2015` into the prefix with protontricks, which installs this same file. Copying it by hand is the equivalent on a headset with no protontricks.

## The fix

Put a 64-bit `mfc140u.dll` next to `MetalVR.exe` in the game folder. The file must sit beside `MetalVR.exe`, not inside `MetalVR_Data`. Take it from `C:\Windows\System32` on a Windows PC, never from `SysWOW64` (that one is 32-bit).

Any route that lands the file there works: scp over SSH, Frame Control or FramePort (free file-transfer apps for the Frame), or a USB stick in Desktop mode with the Dolphin file manager.

## Exact commands

1. Enable Developer Mode and set a user password on the Frame.
2. On a Windows PC, in PowerShell, copy your own 64-bit copy of the file into the game folder on the headset:

```bash
scp C:\Windows\System32\mfc140u.dll steamos@frame.local:.local/share/Steam/steamapps/common/MetalHellsingerVR/
```

If the game is on the microSD card, find the card's name and use that path instead:

```bash
ssh steamos@frame.local ls /run/media/steamos
scp C:\Windows\System32\mfc140u.dll steamos@frame.local:/run/media/steamos/External-00/steamapps/common/MetalHellsingerVR/
```

3. If the game is currently stuck on the black screen, quit it from the Steam menu. Launch it again. The Funcom intro plays with sound within about 15 seconds, then the menu.

No launch options are needed.

## Check it worked

```bash
ssh steamos@frame.local "grep -c CChromaEditorLibrary .local/share/Steam/steamapps/compatdata/2878270/pfx/drive_c/users/steamuser/AppData/LocalLow/TheOutsiders/MetalVR/Player.log"
```

`0` means the plugin loaded and any remaining problem is something else. `1` or more means the game still cannot see the DLL (wrong folder, 32-bit copy, or the game lives on the card).

## Status and known issues

- Game updates and Verify Integrity leave the extra file alone. Uninstalling and reinstalling removes it; repeat the copy if the black screen returns.
- The plugin now loads but finds no Razer software, which is the same as any PC without Synapse. Harmless.
- Only use your own Windows copy of the file or Microsoft's redistributable. DLL download sites are a malware risk.
- Renders at 1728x1728 per eye at 72 Hz; lower the in-game preset if it stutters.
- The same fix likely applies to any other Unity game that bundles `CChromaEditorLibrary64.dll` and black-screens on the Frame.

## Undo

```bash
ssh steamos@frame.local rm .local/share/Steam/steamapps/common/MetalHellsingerVR/mfc140u.dll
```

## Credits

No mod is involved. This repo holds only scripts, no game data or binaries; `mfc140u.dll` is Microsoft's and is not distributed here.
