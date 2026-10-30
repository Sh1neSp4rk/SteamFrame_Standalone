# Titanfall 2 VR

**Status:** Not standalone, working streamed. It never ran on the headset itself; as PC VR streamed from a Windows PC to the Frame it works, with the mod's own controls, when started from the mod's installer window (see *Streaming from a Windows PC*). Confirmed in the headset.

| | |
|---|---|
| Engine / VR API | Northstar (Titanfall 2 modding framework) with the CircuitLord VR mod; OpenXR (`TF2VR_OPENXR`) |
| Route | None on the Frame. PC VR streamed to the headset over SteamVR's wireless link |
| Diagnosed | 2026-10-05, on the PC |

## What it is

A PC VR mod for Titanfall 2 built on Northstar. The CircuitLord VR mod installer keeps Northstar in a `TF2VR` profile folder and starts the game from its own "Launch in VR" button. It is listed here because it shares the symptom "launching from Steam does nothing".

## What you see

Launching from a Steam shortcut either fails outright or runs the game flat. Launching from the installer's own button works, with the Frame as a streamed PC VR headset.

## Why it fails on the Frame

- It is not a Frame title at all. Nothing on the Frame itself is involved; the game runs on the PC.
- A Steam shortcut to `Titanfall2VRLauncher.exe` without `-profile=TF2VR` fails with:

```
Failed to load the Northstar.dll ... (126)
```

- With the profile set, the game runs flat: the VR plugin is gated on an environment variable (`TF2VR_OPENXR`) and arguments that only the installer's own "Launch in VR" button provides.
- Launching from the installer worked (2160x2160 per eye at 144 Hz) until the headset went to standby. SteamVR's wireless link then timed out after 30 seconds of inactivity and quit the session. A relaunch with SteamVR closed crashed on:

```
VRInitError_Driver_WirelessHmdNotConnected
```

## What was tried

- Steam shortcut to `Titanfall2VRLauncher.exe` without `-profile=TF2VR`: Northstar.dll load failure (126).
- Same shortcut with `-profile=TF2VR`: game runs flat, no VR.
- "Launch in VR" from the installer: works until the headset standby drops the wireless link.
- Relaunch with SteamVR closed: `VRInitError_Driver_WirelessHmdNotConnected`.

## What would fix it

- Nothing on the Frame. This is PC VR streaming, not a standalone title.
- What works on the PC: headset on and SteamVR showing Ready first, then "Launch in VR" from the installer (reachable through the SteamVR dashboard's Desktop view), then wait about 35 seconds.

## Streaming from a Windows PC

1. Install the mod with CircuitLord's installer (`CircuitLordVRModInstaller.exe`, kept in the Titanfall 2 folder). It sets up Northstar in the `TF2VR` profile folder.
2. **Library entry:** a non-Steam shortcut to `<Titanfall2>\CircuitLordVRModInstaller.exe` (start in the Titanfall 2 folder) with "Include in VR Library" ticked, so it can be started from the headset. The shortcut on the test PC also passes `-profile=TF2VR`. Do not point a shortcut at `Titanfall2VRLauncher.exe`: without the installer's environment and arguments the game runs flat or fails to load Northstar (see above).
3. Put the headset on and wait for SteamVR to show Ready, start the shortcut, open the SteamVR dashboard's Desktop view, click **Launch in VR** in the installer window and wait about 35 seconds.
4. Keep the headset on: if it goes to standby, SteamVR's wireless link times out after about 30 seconds and the session ends.

The Frame controllers work with the mod's own bindings; nothing was changed for them.

## State left on the headset

Nothing. Nothing on the Frame itself was installed or changed.

## Credits

- Titanfall 2 VR mod by CircuitLord, on the Northstar modding framework.
