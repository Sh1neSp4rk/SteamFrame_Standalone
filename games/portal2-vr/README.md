# Portal 2 VR

**Status:** Working, with caveats — reaches VR within seconds with no DLL patches; the controller layout has not been confirmed in play.

| | |
|---|---|
| Upstream | portal2vr-roomscale V0.2.2 by Spencer0187, OpenVR, a fork in the same shape as l4d2vr |
| Game data | Portal 2 (Steam 620) |
| Route | Proton + FEX (Proton Experimental, ARM64) |
| Steam entry | Portal 2 620 stays the flat entry (the mod's switcher off) through `flatvr-launch.sh`. "Portal 2 VR" 4037750409 is the VR shortcut, which runs `/usr/bin/steam -applaunch 620 -frame-vr` with the VR flag set |
| Set up | 2026-10-21 |

## What it is

The same shape as Left 4 Dead 2 VR: a `d3d9.dll` proxy that renders the Source engine's Direct3D 9 output to SteamVR through OpenVR and reads a SteamVR action manifest. Unlike l4d2vr, this fork needed none of the FEX timing patches; it starts VR within seconds.

## What broke on the Frame

- **The mod's first load:** by the mod's own note, the first load hangs building a sound cache.
- **The game itself, renderer:** as with Left 4 Dead 2, the mod's `d3d9.dll` only loads when the game runs its Direct3D 9 path, so `-dx9` and a `WINEDLLOVERRIDES` for `d3d9` are required.
- **SteamVR input:** the mod ships no binding for the Frame controllers.

## The fix

- `p2_install.sh` copies the mod over the game folder, backing up each of the 45 originals it overwrites into `~/PCVR/Portal2VR/backup-original`. It pre-seeds the dlc3 sound cache (copying `portal2/maps/soundcache/_master.cache` into `portal2_dlc3/maps/soundcache/`, the copy `UpdateSoundCache.cmd` would do), sets the compat tool to `proton-experimental-arm64`, sets the launch options, and lowers SteamVR's per-app render resolution to 1440 for `steam.app.620`.
- `p2_binding.sh` reuses the L4D2 VR Frame binding. It asserts that Portal 2's and L4D2's `action_manifest.json` list the same action names, copies the `/actions/main` sources from L4D2's `bindings_frame_controller.json`, keeps Portal 2's own pose, skeleton and haptics entries from its Oculus Touch file, and inserts the binding first in the manifest's `default_bindings`.

## Exact commands

The scripts live in this repo under `scripts/portal2-vr/` and are copied to `~/PCVR/Portal2VR/` on the headset. The mod archive is extracted to `~/PCVR/Portal2VR/x/Simple_P2VR_install_v2_roomscale/P2VR_install`. The binding script needs the L4D2 VR install present, since it reads `Left 4 Dead 2/VR/SteamVRActionManifest/bindings_frame_controller.json`.

```bash
ssh frame "bash ~/PCVR/Portal2VR/p2_install.sh"
ssh frame "bash ~/PCVR/Portal2VR/p2_binding.sh"    # also restarts the game through p2_go.sh
```

Launch options on Portal 2 620, as set by `p2_install.sh`:

```
PROTON_LOG=1 WINEDLLOVERRIDES=d3d9=n,b %command% -insecure -dx9 -window -novid +mat_motion_blur_percent_of_screen_max 0 +mat_queue_mode 0 +mat_vsync 0 +mat_antialias 0 +mat_grain_scale_override 0 +snd_surround_speakers 5
```

Drop `PROTON_LOG=1` once settled. SteamVR `resolutionOverride` is 1440, as for L4D2:

```bash
/opt/steamvr/bin/linuxarm64/vrcmd --set-settings-int steam.app.620/resolutionOverride 1440
```

## Controls

The same binding as L4D2 VR, since the two mods share an action set; see the [standard Frame layout](../../FRAME-LAYOUT.md) and the L4D2 VR write-up for the full table. The triggers fire the blue and orange portals (right = blue, left = orange, the primary and secondary slots). Bumpers are jump and use, A is crouch, the menu button pauses, grips are unused. Only the portal triggers have been confirmed in play; the rest of the layout has not.

## Status and known issues

- Runs in VR within seconds of launch.
- Controls beyond the triggers are not yet confirmed in play.
- A Steam file verify would undo the mod, since it overwrites game files.

## Undo

Copy the 45 backed-up originals from `~/PCVR/Portal2VR/backup-original` back over the game folder, clear the launch options on 620, and remove shortcut 4037750409 (`python3 ~/PCVR/bin/steam_shortcuts.py remove 4037750409`). A Steam file verify also restores the game's own files.

## Files in this repo

- [p2_install.sh](../../scripts/portal2-vr/p2_install.sh): installs the mod with backups, seeds the sound cache, sets compat tool, launch options and render resolution.
- [p2_binding.sh](../../scripts/portal2-vr/p2_binding.sh): converts the L4D2 VR Frame binding for Portal 2's action manifest.

## Credits

- portal2vr-roomscale by Spencer0187, the mod this runs.
- l4d2vr by sd805, whose action set and Frame binding this reuses.
- Portal 2 (game data from Steam, not included).
- Valve for Portal 2, OpenVR, SteamVR, Proton and the Steam Frame.

This repo holds only scripts. It contains no game data, no mod binaries and no game binaries.
