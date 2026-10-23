# frame_quadfix: an OpenXR API layer for Proton games on the Steam Frame

A small x86-64 Windows OpenXR API layer, built on the Frame itself with clang and lld-link and no Windows SDK, that sits between a Proton game and SteamVR's OpenXR runtime (through wineopenxr). Written for [Unreal Revived VR](../../games/unreal-revived-vr/); the two things it does apply to other games.

## What it fixes

1. **Per-eye quad layers.** SteamVR on the Frame rejects every `xrEndFrame` that carries a pair of `XrCompositionLayerQuad` layers with `eyeVisibility` LEFT and RIGHT (the right one from slice 1 of a texture array): `compositor failed EndFrame()`, `XR_ERROR_POSE_INVALID`, even with a unit quaternion. The game's menus and HUD never reach the headset. The layer shows the LEFT quad to both eyes and drops the RIGHT one; frames are then accepted. `FRAMEXR_QUAD` selects the mode: `both` (default), `drop` (all quads dropped, diagnostic) or `pass` (untouched, diagnostic). Every mode also normalises quad orientations.
2. **One interaction profile.** SteamVR only honours a custom Frame binding for a Proton OpenXR app when the app's input context holds a single interaction profile (see [KNOWN-ISSUES.md](../../KNOWN-ISSUES.md)). The layer forwards only the game's Oculus Touch suggestion from `xrSuggestInteractionProfileBindings`. `FRAMEXR_PROFILES=all` disables that. With a `frame_controller`-typed binding written over the auto-generated, read-only `steam.app.<id>_oculus_touch_0_binding.json`, SteamVR applies the Frame layout with no VR session restart.

It logs to `frame_quadfix.log` next to the game: the first quads seen in full, then accept and reject counts every 600 frames, split by whether the frame had quads.

## Build and install

`build.sh` compiles `quadfix.c` freestanding (`clang --target=x86_64-pc-windows-msvc`, importing a handful of `msvcrt` functions through a generated `.def`), writes the layer manifest `frame_quadfix.json`, copies both next to the game's exe, and registers the manifest as an implicit layer in the prefix's `system.reg` under `Software\Khronos\OpenXR\1\ApiLayers\Implicit` (HKLM is read even though Wine runs "elevated"). The game must be closed and its `wineserver` gone before the registry edit; the script checks. `DISABLE_FRAME_QUADFIX=1` in the environment turns the layer off.

The script's paths are Unreal Revived's (`~/PCVR/UnrealRevivedVR`, `C:\Games\Unreal Revived\System64`); change them for another game. The OpenXR headers (`openxr/openxr.h`, `openxr/openxr_loader_negotiation.h`) come from the Khronos OpenXR-SDK; the Frame has them under `/usr/include`.

## Files

- [quadfix.c](quadfix.c): the layer.
- [build.sh](build.sh): build, manifest, install and registration.

MIT, like the rest of this repository.
