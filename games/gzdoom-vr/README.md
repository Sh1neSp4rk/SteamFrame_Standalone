# GZDoom VR: Doom, Brutal Doom, MyHouse, Gun Bonsai, Heretic, Hexen

**Status:** Working. The OpenVR fork of GZDoom runs under Proton on the Frame; seven non-Steam shortcuts share one install and differ only in launch options.

| | |
|---|---|
| Upstream | gzdoomvr 4.13.2.2, https://github.com/hh79/gzdoomvr (OpenVR, OpenGL). Mods: Brutal Doom v21 Gold with the br_vr VR weapon models (https://github.com/ajantaju/br_vr, release RC2); Gun Bonsai 0.10.6 (https://github.com/ToxicFrog/doom-mods); MyHouse (myhouse.pk3); Ermac's Hexen VR 3D weapons (ModDB, work in progress) |
| Game data | Not a Steam game. IWADs supplied by the user (doom.wad, DOOM2.WAD, PLUTONIA.WAD, TNT.WAD, nerve.wad, masterlevels.wad, sigil.wad, sigil2.wad). Heretic and Hexen WADs come from the "Heretic + Hexen" rerelease (Steam 3286930), dos/base folder |
| Route | Proton + FEX (Proton Experimental, ARM64), OpenVR, OpenGL |
| Steam entry | Non-Steam shortcuts with the VR flag, exe gzdoomvr.exe, start dir ~/PCVR/GZDoomVR: Doom VR 3408293163, Brutal Doom VR 3506065631, MyHouse VR 4235418420, Doom VR (Gun Bonsai) 3284308812, Heretic VR 4268466633, Hexen VR 2541150700, Hexen Deathkings VR 2150730901 |
| Set up | 2026-10-05 and 2026-10-06 (Doom entries); 2026-10-21 (Heretic and Hexen) |

## What it is

gzdoomvr is an OpenVR fork of GZDoom. It renders with OpenGL and talks to SteamVR through OpenVR, which is the one OpenGL VR combination Proton on the Frame can bridge. The Windows build runs through Proton Experimental (ARM64) and FEX, the same path Steam's own Windows VR titles use. Nothing in SteamOS, Steam or the headset was modified. The same engine runs Doom, Doom II with mods, Heretic and Hexen; each is its own shortcut with its own launch options and its own Proton prefix.

The engine's bundled WeaponsForVR.pk3 and laser-sight.pk3 give the classic Doom weapons 3D models. `+vr_mode 10` selects OpenVR (SteamVR).

## What broke on the Frame

- **SteamVR input (grip threshold).** Steam's stock Frame legacy binding presses the grip at 10% squeeze. In Heretic and Hexen that blocked attacking: simply holding the controller counted as a grip press. This is where the grip rule in the standard layout comes from.
- **Steam client: compat tool did not stick.** Setting the compat tool immediately after adding the shortcut gave "no compat mapping in config.vdf" because Steam had not registered the new entry yet.
- **Steam client: launch options silently not saved** while the entry was running.
- **The mod itself (Brutal Doom): flat weapons.** br_vr.pk3 targets Brutal Doom v21 Gold. With the v22 test build everything loaded and then the process died right after `P_Init`.
- **The mod itself (MyHouse): flat weapons.** myhouse.pk3 replaces the weapons with smooth-animation versions under new class names (`SmoothPistol` and so on), so the bundled WeaponsForVR models never bind.
- **The game itself (Heretic): sprite weapons.** WeaponsForVR.pk3 is Doom-only, so Heretic shows its original weapon sprites.
- **Harmless noise.** The engine's bundled OpenXR loader logs `xrCreateInstance failed` before falling back to OpenVR, and Steam's `gameoverlayrenderer.so` LD_PRELOAD error appears for every Proton launch on the Frame.

## The fix

- **Grip.** The three Heretic and Hexen entries use `~/PCVR/GZDoomVR/gzdoomvr_frame_binding.json`, a copy of Steam's stock Frame legacy binding with the grip press raised to 80% (`click_activate_threshold 0.8`) and release below 70% (`click_deactivate_threshold 0.7`). `gz_grip.sh` writes it and selects it per app through `frame_controller_CurrentURL_legacy`. Legacy bindings apply without a SteamVR restart.
- **Compat tool.** Set it again a moment later and verify with `grep -A3 '"<appid>"' ~/.local/share/Steam/config/config.vdf`.
- **Launch options.** Stop the entry first; verify with `grep -a` on `userdata/*/config/shortcuts.vdf`.
- **Brutal Doom.** Use brutalv21.pk3.
- **MyHouse.** `make_vrweapons_myhouse.py` generates VRWeapons-MyHouse.pk3: 33 MODELDEF blocks that re-declare the WeaponsForVR models for the Smooth* classes. Load it last. The models show a static ready pose rather than the smooth animations; drop it from the line to get sprites back.
- **Heretic and Hexen WADs.** heretic.wad (SOSR 1.3), hexen.wad (1.1) and hexdd.wad (Deathkings 1.1) are copied from the rerelease's dos/base folder. The rerelease's top-level WADs are the 2025 KEX versions; the DOS ones are what gzdoomvr 4.13 is sure to support. Both Hexen entries load Ermac's Hexen VR 3D weapons.

## Exact commands

The scripts live in this repo under `scripts/gzdoom-vr/` and are copied to `~/PCVR/bin/` on the headset. The shared helpers `steam_shortcuts.py` and `steam_eval.py` are in `scripts/common/`.

On the PC: fetch `gzdoomvr-4-13-2-2.zip` from the gzdoomvr GitHub releases, br_vr RC2 (repackaged as br_vr.pk3) and Gun Bonsai 0.10.6. `scp` the engine folder, the IWADs and the pk3s into `~/PCVR/GZDoomVR/` on the headset.

Add each entry as a non-Steam shortcut over the Steam debug port (this also sets the VR flag and a "PC VR ports" collection), then the compat tool and launch options:

```bash
python3 ~/PCVR/bin/steam_shortcuts.py add "Doom VR" /home/steamos/PCVR/GZDoomVR/gzdoomvr.exe /home/steamos/PCVR/GZDoomVR
python3 ~/PCVR/bin/steam_shortcuts.py list
# via steam_eval.py, or in the headset UI under Properties
SteamClient.Apps.SpecifyCompatTool(3408293163, "proton_experimental")
SteamClient.Apps.SetShortcutLaunchOptions(3408293163, "-iwad DOOM2.WAD -file WeaponsForVR.pk3 +vr_mode 10")
```

Launch options per entry:

| Entry | Launch options |
|---|---|
| Doom VR | `-iwad DOOM2.WAD -file WeaponsForVR.pk3 +vr_mode 10` |
| Brutal Doom VR | `-iwad DOOM2.WAD -file brutalv21.pk3 br_vr.pk3 +vr_mode 10` |
| MyHouse VR | `-iwad DOOM2.WAD -file WeaponsForVR.pk3 myhouse.pk3 VRWeapons-MyHouse.pk3 +vr_mode 10` |
| Doom VR (Gun Bonsai) | `-iwad DOOM2.WAD -file WeaponsForVR.pk3 GunBonsai-0.10.6.pk3 +vr_mode 10` |
| Heretic VR | `-iwad heretic.wad +vr_mode 10` |
| Hexen VR | `-iwad hexen.wad -file hexen_VR_weapons_Ermac_WIP.pk3 +vr_mode 10` |
| Hexen Deathkings VR | `-iwad hexen.wad -file hexdd.wad hexen_VR_weapons_Ermac_WIP.pk3 +vr_mode 10` |

Swap the IWAD or add mods per entry, for example `-iwad doom.wad -file WeaponsForVR.pk3 sigil.wad +vr_mode 10`.

Heretic and Hexen, the MyHouse overlay and the grip binding:

```bash
bash ~/PCVR/bin/hh_setup.sh              # copies the DOS WADs, adds the three shortcuts, sets compat tool and launch options
bash ~/PCVR/bin/hexw_install.sh          # adds Ermac's Hexen VR weapons pk3 to both Hexen entries
python3 ~/PCVR/bin/make_vrweapons_myhouse.py   # rebuilds ~/PCVR/GZDoomVR/VRWeapons-MyHouse.pk3
bash ~/PCVR/bin/gz_grip.sh               # writes gzdoomvr_frame_binding.json and selects it for the Heretic/Hexen entries
```

Check it worked:

```bash
ssh frame "grep -E 'success response from vrserver|Created remote GL texture' ~/.local/share/Steam/logs/vrclient_gzdoomvr.txt | tail -3"
# ... Received success response from vrserver connect
# ... Created remote GL texture ... 1728 x 1728
```

Each entry gets its own Proton prefix, so saves and the ini live under `compatdata/<appid>/pfx/drive_c/users/steamuser/Documents/My Games/GZDoomVR/`.

## Controls

Input is the engine's legacy OpenVR input ("app appears to be using legacy input" in the vrclient log); the Frame controllers work with it. The Doom entries use Steam's stock Frame legacy layout unchanged. The Heretic and Hexen entries use `gzdoomvr_frame_binding.json`: the same stock layout with the grip press raised to 80% and release below 70%.

Deviations from the [standard layout](../../FRAME-LAYOUT.md): the whole layout is still Steam's stock one, not the standard layout; only the grip threshold has been brought in line. Gun Bonsai's options live under Options > Full Options Menu; move its HUD with the sliders there if it is off-screen in VR. MyHouse replaces MAP01, so start a New Game.

## Status and known issues

- Working for all seven entries.
- MyHouse VR weapon models show a static ready pose, not the smooth animations.
- Heretic shows sprite weapons (no VR model pack).
- Hexen's 3D weapons are a work-in-progress pack.
- `xrCreateInstance failed` and the `gameoverlayrenderer.so` LD_PRELOAD error in the logs are harmless.

## Undo

```bash
python3 ~/PCVR/bin/steam_shortcuts.py remove 3408293163      # Doom VR
python3 ~/PCVR/bin/steam_shortcuts.py remove 3506065631      # Brutal Doom VR
python3 ~/PCVR/bin/steam_shortcuts.py remove 4235418420      # MyHouse VR
python3 ~/PCVR/bin/steam_shortcuts.py remove 3284308812      # Doom VR (Gun Bonsai)
python3 ~/PCVR/bin/steam_shortcuts.py remove 4268466633      # Heretic VR
python3 ~/PCVR/bin/steam_shortcuts.py remove 2541150700      # Hexen VR
python3 ~/PCVR/bin/steam_shortcuts.py remove 2150730901      # Hexen Deathkings VR
rm -rf ~/PCVR/GZDoomVR ~/.local/share/Steam/steamapps/compatdata/{3408293163,3506065631,4235418420,3284308812,4268466633,2541150700,2150730901}
```

## Files in this repo

- [gz_grip.sh](../../scripts/gzdoom-vr/gz_grip.sh): copies Steam's stock Frame legacy binding with the grip at 80%/70% and selects it for the Heretic and Hexen entries.
- [gzdoomvr_frame_binding.json](../../scripts/gzdoom-vr/gzdoomvr_frame_binding.json): the resulting legacy binding file.
- [hh_setup.sh](../../scripts/gzdoom-vr/hh_setup.sh): copies the DOS Heretic and Hexen WADs from the rerelease and adds the three shortcuts.
- [hexw_install.sh](../../scripts/gzdoom-vr/hexw_install.sh): installs Ermac's Hexen VR weapons pk3 and adds it to both Hexen entries.
- [make_vrweapons_myhouse.py](../../scripts/gzdoom-vr/make_vrweapons_myhouse.py): builds VRWeapons-MyHouse.pk3, the MODELDEF overlay for MyHouse's Smooth* weapon classes.
- [steam_shortcuts.py](../../scripts/common/steam_shortcuts.py), [steam_eval.py](../../scripts/common/steam_eval.py): shared shortcut and Steam-client helpers.

## Credits

- gzdoomvr by hh79 (OpenVR fork of GZDoom).
- Brutal Doom VR weapon models by ajantaju (br_vr). Gun Bonsai by ToxicFrog. Hexen VR weapons by Ermac.
- Valve for OpenVR, SteamVR and Proton.
- This repo holds only scripts and a generated overlay pk3 recipe. No game data, WADs, mods or binaries are included.
