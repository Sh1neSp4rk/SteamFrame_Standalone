# F.E.A.R. VR

**Status:** Working — one wrapper swaps a Proton verb so the mod's launcher handoff lands in the same wineserver; fixed 2026-10-21.

| | |
|---|---|
| Upstream | fear-vr v1.7.7 by thefreemike31, OpenXR via Direct3D |
| Game data | F.E.A.R. (Steam 21090), the "FEAR Ultimate Shooter Edition" install |
| Route | Proton + FEX (Proton Experimental, ARM64: it ships the i386 wineopenxr the 32-bit game needs) |
| Steam entry | F.E.A.R. 21090 stays the flat library entry. "F.E.A.R. VR" 2341077394 is a non-Steam shortcut that runs the mod's launcher, where "Play in VR" starts the game |
| Set up | 2026-10-21 |

## What it is

A mod with its own launcher. The launcher patches `FEAR.exe` in memory and then relaunches the game with a `-fearvrhandoff` argument, handing over through shared memory (`Local\FEARVR-Steam-*`). The game renders in Direct3D and reaches the headset through OpenXR, which Proton's wineopenxr bridges to SteamVR.

## What broke on the Frame

- **Proton/FEX, the handoff:** when the launcher relaunched `FEAR.exe` through Steam, Proton started it with its `waitforexitandrun` verb. That verb waits for the running wineserver to exit, so the relaunch landed in a second wineserver and a second prefix session, never found the handoff memory, and Steam reported the game as already running.
- **The mod's installer:** the mod's Setup rejects Steam's `Z:` and `S:` paths because they are links, so it would not install into the real game folder.
- **wineopenxr, runtime selection:** setting `XR_RUNTIME_JSON` for the game breaks it. Proton's native OpenXR setup reads that variable too and Direct3D 11 support then disappears.
- **Proton, 32-bit OpenXR:** the game is 32-bit. Proton Experimental (ARM64) ships the i386 wineopenxr; the registered `C:\openxr\wineopenxr64.json` also serves 32-bit through the system32 to syswow64 redirect.

## The fix

- `fearvr-launch.sh` is the launch-option wrapper on F.E.A.R. 21090. When the command line contains `-fearvrhandoff`, it rewrites `--verb=waitforexitandrun` (or a bare `waitforexitandrun`) to `run`, so `FEAR.exe` joins the launcher's wineserver and finds the handoff memory instead of starting a second prefix session and tripping Steam's "already running" check. Otherwise it replaces `FEAR.exe` in the command with whatever `~/PCVR/FEARVR/mode` selects: `play` (the default, `F.E.A.R. VR.exe`), `diagnose` (`F.E.A.R. VR.exe --diagnose`, a read-only launcher preflight), `setup` (the mod's Setup, silent), or `flat` (the original command, untouched).
- `fearvr-shortcut.sh` is the "F.E.A.R. VR" shortcut's wrapper; it runs the mod launcher inside 21090's prefix by setting `STEAM_COMPAT_DATA_PATH`.
- Install: `fear_setup.sh` points 21090 at `proton-experimental-arm64`, sets the launch option, writes `setup` into the mode file and launches the game once. In setup mode the wrapper runs `F.E.A.R. VR Setup.exe --action install --game "C:\FEAR" --silent --result "C:\FEARVR-Setup\setup-result.json"`, where `C:\FEAR` is a hard-link mirror of the game folder inside the prefix. The new files were then copied into the real folder. The launcher memory-patches `FEAR.exe`; the original is kept as `FEAR.exe.fearvr-memory-original`.
- `XR_RUNTIME_JSON` is left unset.

## Exact commands

The scripts live in this repo under `scripts/fear-vr/` and are copied to `~/PCVR/FEARVR/` on the headset.

```bash
# one-time: compat tool, launch option, silent install of the mod's Setup into the prefix mirror
ssh frame "bash ~/PCVR/FEARVR/fear_setup.sh"

# afterwards: play mode (the default)
ssh frame "echo play > ~/PCVR/FEARVR/mode"

# restart the shortcut cleanly
ssh frame "bash ~/PCVR/FEARVR/fear_go.sh"

# Proton log for the next launch (~/steam-21090.log)
ssh frame "touch ~/PCVR/FEARVR/debug"
```

Launch option on F.E.A.R. 21090:

```
/home/steamos/PCVR/FEARVR/fearvr-launch.sh %command%
```

Logs: `FEARVR-Launcher.log` and `FEARVR-Startup.log` in the game folder; each wrapper invocation is appended to `~/PCVR/FEARVR/last-launch.txt`.

## Controls

SteamVR's automatic layout. Not yet reviewed against the [standard Frame layout](../../FRAME-LAYOUT.md).

## Status and known issues

- Working in VR through the shortcut.
- Do not set `XR_RUNTIME_JSON` for this game.
- Controls have not been converted to the standard layout.

## Undo

The sources do not record an uninstall script. Reversing the setup means: set `~/PCVR/FEARVR/mode` to `flat` or clear the launch option on 21090, remove the "F.E.A.R. VR" shortcut 2341077394 with `python3 ~/PCVR/bin/steam_shortcuts.py remove 2341077394`, restore `FEAR.exe` from `FEAR.exe.fearvr-memory-original`, and remove the mod files from the game folder (or verify the game's files through Steam).

## Files in this repo

- [fear_setup.sh](../../scripts/fear-vr/fear_setup.sh): sets the compat tool and launch option and runs the mod's Setup once in silent mode.
- [fearvr-launch.sh](../../scripts/fear-vr/fearvr-launch.sh): the launch-option wrapper with the `waitforexitandrun` to `run` swap and the mode switch.

## Credits

- fear-vr by thefreemike31, the mod this runs.
- F.E.A.R. (game data from Steam, not included).
- Valve for OpenVR, SteamVR, Proton and the Steam Frame.

This repo holds only scripts. It contains no game data, no mod binaries and no game binaries.
