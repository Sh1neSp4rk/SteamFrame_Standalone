# Bendy and the Ink Machine VR

**Status:** Working — the catch is the Steam branch, not the Frame; set up 2026-10-20.

| | |
|---|---|
| Upstream | BendyVR 1.2.2 by Team Beef (Team-Beef-Studios/BendyVR), BepInEx plugin, OpenVR |
| Game data | Bendy and the Ink Machine (Steam 622650) on the beta branch "release-1.5" (build 3248927, Unity 2018.2.12f1 Mono) |
| Route | Proton + FEX (Proton 11.0, ARM64) |
| Steam entry | Bendy 622650 stays the flat entry (no BepInEx) through `flatvr-launch.sh`. "Bendy VR" 3641501148 is the VR shortcut, which runs `/usr/bin/steam -applaunch 622650 -frame-vr` with the VR flag set |
| Set up | 2026-10-20 |

## What it is

Team Beef's BepInEx mod for a Unity 2018 game. BepInEx is loaded through Unity Doorstop (`winhttp.dll` beside the exe), the mod's patcher rewrites `globalgamemanagers` on first launch, and the plugin drives SteamVR through OpenVR.

## What broke on the Frame

- **The game itself, engine version:** Steam's default build is Unity 2022 IL2CPP, which the mod cannot load. The mod needs the Unity 2018 Mono build, which lives on the "release-1.5" beta branch.
- **The mod's installer:** the mod ships `TeamBeefInstaller.exe`; the install was done by hand instead.
- **The mod's config:** the shipped `doorstop_config.ini` points `targetAssembly` at the developer's own `F:\` drive.

## The fix

- The branch was switched from a PC with `SteamClient.Apps.JoinAppContentBeta(622650, "release-1.5")`. `install.sh` waits for the beta build to finish installing (polls `appmanifest_622650.acf` for `StateFlags` 4 and a build id different from the old one) and checks for the `Managed` folder before continuing.
- `install.sh` then does what `TeamBeefInstaller.exe` does: backs up every file `Mod/CopyToGame` would overwrite into `~/PCVR/BendyVR/backup-<build>`, copies `Mod/CopyToGame/*` and `Mod/BepInEx` into the game folder, and rewrites `doorstop_config.ini` with a relative `targetAssembly=BepInEx\core\BepInEx.Preloader.dll`.
- The launch option loads Doorstop through Wine's `winhttp` override.
- First launch: BepInEx 5.4.21 started, BendyVRPatcher rewrote `globalgamemanagers` (backup `.bak` alongside), "SteamVR Initialised", title screen reached.

## Exact commands

The scripts live in this repo under `scripts/bendy-vr/` and are copied to `~/PCVR/BendyVR/` on the headset. The mod archive is extracted to `~/PCVR/BendyVR/extracted/BendyVRInstall`.

```bash
# from a PC with the Steam client scripting hook: switch the branch
#   SteamClient.Apps.JoinAppContentBeta(622650, "release-1.5")

# wait for the beta build, install the mod by hand, set the launch option, write uninstall.sh
ssh frame "bash ~/PCVR/BendyVR/install.sh"       # log: ~/PCVR/BendyVR/install.log

# launch through Steam and print the BepInEx and Unity logs after N seconds (default 60)
ssh frame "bash ~/PCVR/BendyVR/launch.sh 60"
```

Launch option on Bendy 622650, as set by `install.sh`:

```
WINEDLLOVERRIDES="winhttp=n,b" %command%
```

Settings: `<game>/BepInEx/config/org.baggyg.vrplugins.bendyvr.cfg` (snap or smooth turn and so on). Logs: `<game>/BepInEx/LogOutput.log` and Unity's `Player.log` under the prefix's `AppData/LocalLow`.

## Controls

The mod's defaults. Not yet reviewed against the [standard Frame layout](../../FRAME-LAYOUT.md).

## Status and known issues

- Working: title screen in VR on the first launch.
- The game must stay on the "release-1.5" beta branch; the default branch's IL2CPP build cannot load the mod.
- Controls have not been converted to the standard layout.

## Undo

```bash
ssh frame "bash ~/PCVR/BendyVR/uninstall.sh"    # then set the beta back to None in Steam
```

`uninstall.sh` removes `BepInEx`, `winhttp.dll`, `doorstop_config.ini` and the mod's plugin DLLs (`LIV_Bridge.dll`, `OVRPlugin.dll`, `openvr_api.dll`, `openvr_mod.cfg`), restores the backed-up files, and clears the launch option.

## Files in this repo

- [install.sh](../../scripts/bendy-vr/install.sh): waits for the beta build, installs the mod by hand with backups, fixes `doorstop_config.ini`, sets the launch option, writes `uninstall.sh`.
- [launch.sh](../../scripts/bendy-vr/launch.sh): launches through Steam and reports BepInEx and Unity logs.

## Credits

- BendyVR by Team Beef (Team-Beef-Studios), the mod this runs.
- BepInEx and Unity Doorstop.
- Bendy and the Ink Machine (game data from Steam, not included).
- Valve for OpenVR, SteamVR, Proton and the Steam Frame.

This repo holds only scripts. It contains no game data, no mod binaries and no game binaries.
