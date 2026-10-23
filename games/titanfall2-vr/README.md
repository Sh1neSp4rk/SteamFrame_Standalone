# Titanfall 2 VR

**Status:** Not standalone — this never ran on the headset; it is a PC VR mod streamed to the Frame, and it only starts correctly from the mod's own installer window on the PC.

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

## State left on the headset

Nothing. Nothing on the Frame itself was installed or changed.

## Credits

- Titanfall 2 VR mod by CircuitLord, on the Northstar modding framework.
