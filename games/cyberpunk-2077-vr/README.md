# Cyberpunk 2077 VR: CyberpunkVRPort streamed from a Windows PC, with a flat entry kept

**Status:** Installed on a Windows PC and streamed to the Frame. The flat launch from Steam's normal entry is confirmed (the VR plugin stays out of the process). The VR launch through the "Cyberpunk 2077 (VR)" entry has not yet been checked in the headset. Not tried standalone on the Frame.

| | |
|---|---|
| Steam app | 1091500 (Cyberpunk 2077), game version 2.5, build 26161058 |
| Engine / VR API | REDengine 4, Direct3D 12; the mod renders stereo through OpenXR (SteamVR's runtime) and also supports OpenVR |
| Mod | dariulone's [CyberpunkVRPort](https://github.com/dariulone/cyberpunk-vr-port) 0.2.1 (MIT), a [RED4ext](https://github.com/wopss/RED4ext) 1.31.0 plugin |
| Route | Windows PC (RTX 4080 Laptop) streaming to the Frame through SteamVR |
| Frame fixes | a launch wrapper that runs the game flat unless `-vr` is passed, with a separate settings file per mode; a "Cyberpunk 2077 (VR)" shortcut that passes `-vr` |
| Date | 2026-11-04 |

## Why this mod

Luke Ross's R.E.A.L. VR mod for Cyberpunk 2077 was taken down by CD Projekt in January 2026 and was left out of his free re-release of the suite in March 2026, so it is no longer obtainable. CyberpunkVRPort is the open-source replacement: 6-DoF head tracking, real per-eye stereo rendering, a full-body avatar with motion-controlled hands, VR weapon aiming, physical reload and melee, and an in-headset settings overlay (F10). Its README says the Steam Frame is driven through the native `XR_VALVE_frame_controller_interaction` profile when the runtime exposes it, with Oculus Touch emulation as the fallback. Controller input is merged into the game's own gamepad input, so the game's Settings > Key Bindings > Controller page applies in VR.

## What it needs

- Cyberpunk 2077 **2.5** (the plugin matches engine offsets to that build; 2.31 does not work).
- RED4ext 1.31.0 or newer: `bin\x64\winmm.dll` plus `red4ext\RED4ext.dll`.
- The port: `red4ext\plugins\cyberpunkvrport\` (plugin, shaders, grips, Lua mods, scripts, its own archive and TweakDB records) and `bin\x64\openvr_api.dll`. Cyber Engine Tweaks, ArchiveXL, TweakXL, Codeware and redscript are not needed; the plugin carries its own copies of what it uses.
- An OpenXR runtime running before the game. SteamVR is the active runtime on the test PC; the wrapper starts it if it is not up.
- The companions the port lists, installed on the test PC as well: Visual Holsters 1.4, Equipment-EX 1.2.10, Nova Optics 1.4.2 and More Occluders (Scripted 0.4) from Nexus (a login is needed there), plus what they need themselves: Native Settings UI (Nexus) and Cyber Engine Tweaks, ArchiveXL, TweakXL, Codeware and redscript (GitHub releases). All drop into the game root and none overwrites a game file. The plugin loads without them; holster visuals, the wardrobe and the exposure fix are what they add.

## Keeping a flat launch

The plugin loads whenever RED4ext finds its DLL, and on its first start it merges a VR preset (graphics, every control binding, HUD and comfort values) into the game's `UserSettings.json`. Two things keep the normal library entry flat and untouched:

1. **RED4ext's ignore list.** `red4ext\config.ini` is TOML; `ignored = [ "cyberpunkvrport" ]` under `[plugins]` makes RED4ext skip the plugin by its DLL name. [cp77-launch.cmd](../../scripts/cyberpunk-2077-vr/cp77-launch.cmd) copies [red4ext-config.flat.ini](../../scripts/cyberpunk-2077-vr/red4ext-config.flat.ini) or [red4ext-config.vr.ini](../../scripts/cyberpunk-2077-vr/red4ext-config.vr.ini) over it before every launch.
2. **One settings file per mode.** The wrapper keeps `_vr\profiles\UserSettings.flat.json` and `UserSettings.vr.json`, copies the right one into `%LOCALAPPDATA%\CD Projekt Red\Cyberpunk 2077\` before the game starts and saves it back after the game exits. The VR preset therefore lands only in the VR profile.

The wrapper then starts `bin\x64\Cyberpunk2077.exe` directly (no REDlauncher) and waits for it. Steam's `-applaunch` passes extra arguments through to the launch option, so a non-Steam shortcut running `steam.exe -applaunch 1091500 -vr` is the VR entry and the game's own entry stays flat.

## Steps (Windows PC)

1. **RED4ext:** extract `red4ext-<version>.zip` from its [releases](https://github.com/wopss/RED4ext/releases) into the game root (the folder with `bin\`, `r6\`, `archive\`).
2. **The port:** extract `CyberpunkVRPort-<version>.zip` from its [releases](https://github.com/dariulone/cyberpunk-vr-port/releases) into the same root. Nothing it adds already exists in a clean install.
3. **The wrapper:** create `<Cyberpunk 2077>\_vr\` and copy [cp77-launch.cmd](../../scripts/cyberpunk-2077-vr/cp77-launch.cmd), [red4ext-config.flat.ini](../../scripts/cyberpunk-2077-vr/red4ext-config.flat.ini) and [red4ext-config.vr.ini](../../scripts/cyberpunk-2077-vr/red4ext-config.vr.ini) into it. The wrapper finds the game root from its own location.
4. **Launch option** on Cyberpunk 2077 (Properties > General): `"<Cyberpunk 2077>\_vr\cp77-launch.cmd" %command%`
5. **Library entry:** Add a Non-Steam Game pointing at `steam.exe` with the launch options `-applaunch 1091500 -vr`, name it "Cyberpunk 2077 (VR)" and tick "Include in VR Library". The normal entry stays flat.
6. **Art:** [make_vrart.py](../../scripts/common/make_vrart.py) builds the red "CYBERPUNK VR" tiles for the shortcut from Steam's CDN art, and the same tiles with a blue "STREAM FROM PC" pill for the headset's grid folder, where the PC's shortcuts show up for streaming.

The first VR launch shows the port's launcher window (render resolution, DEBUG off) and merges its preset into the VR profile; `bin\x64\vrport.ini` then records `first_launch=0`.

## Check it worked

- `_vr\cp77-launch.log`: `start mode=flat` or `start mode=vr ... -vr`, `launching Cyberpunk2077.exe`, then `game exited` and `saved <mode> profile`.
- `red4ext\logs\red4ext-<date>.log`: `0 plugin(s) loaded` on a flat launch, the cyberpunkvrport plugin listed on a VR launch.
- VR launch: `bin\x64\cyberpunkvrport.log` appears, and the port's launcher window opens before the game.

## Status and known issues

- VR not yet confirmed in the headset; the Frame controller mapping (the port's own layout, which mirrors the game's gamepad bindings) is unverified.
- The companions and their frameworks are not VR-only: a flat launch also loads Cyber Engine Tweaks (it asks for an overlay key on its first run), the Equipment-EX wardrobe, Visual Holsters and Nova Optics. Verified: with all of them installed the flat launch still logs the three framework plugins, a clean redscript compile and the VR plugin ignored.
- The wrapper is a `.cmd`, so a console window sits behind the game for the session. Harmless when streaming.
- Killing the game instead of quitting skips the settings save for that run; the next launch of the same mode restores the previous profile.
- Standalone on the Frame was not attempted: an 81 GB Direct3D 12 game with an x86-64 RED4ext plugin chain under FEX is out of scope for now.

## Files in this repo

- [cp77-launch.cmd](../../scripts/cyberpunk-2077-vr/cp77-launch.cmd): the flat / VR launch wrapper.
- [red4ext-config.flat.ini](../../scripts/cyberpunk-2077-vr/red4ext-config.flat.ini), [red4ext-config.vr.ini](../../scripts/cyberpunk-2077-vr/red4ext-config.vr.ini): the two RED4ext configs it switches between.
- [../common/make_vrart.py](../../scripts/common/make_vrart.py): the Pillow art builder (red VR pill, optional blue stream pill).

## Credits

- CyberpunkVRPort by dariulone (MIT); VR driving by iPowerTech. RED4ext by WopsS (MIT). None of them is included here.
