# Snapshot VR

**Status:** Working. The game starts flat because its Unity build asks for one OpenXR extension without the companion extension the spec requires; a 70 KB implicit OpenXR API layer in the home folder adds the missing name.

| | |
|---|---|
| Steam app | 1133580 (SteamVR 2.18.2 at the time) |
| Engine / VR API | Unity 2022.3, Unity OpenXR plugin 1.14.3, OpenXR |
| Route | Proton 11.0 (ARM64) + FEX |
| Fix | implicit OpenXR API layer in `~/.local/share/openxr` |
| Date | fixed 2026-10-09 |

## What it is

Snapshot VR is a Unity OpenXR title. On the Frame it runs through Proton, with wineopenxr bridging to SteamVR's OpenXR runtime. The fix here is not specific to the game: it is an OpenXR layer that corrects an extension request any Unity OpenXR 1.14-era build makes.

## What you see

The game opens as a flat window in the theater with keyboard-and-mouse input. Controllers do nothing useful.

## What broke on the Frame

- **The game itself (Unity OpenXR plugin 1.14).** Snapshot VR's Foveated Rendering feature asks the runtime for `XR_FB_foveation`, `XR_FB_foveation_configuration` and `XR_FB_foveation_vulkan`, but not `XR_FB_swapchain_update_state`, which the OpenXR spec lists as a required dependency of `XR_FB_foveation`.
- **SteamVR/OpenXR runtime.** SteamVR on the Frame checks that dependency and refuses to create the OpenXR instance. Unity then gives up on VR and runs flat.

From `~/.local/share/Steam/logs/xrclient_SnapshotVR.txt`:

```
xrCreateInstance: Application is requesting the following extensions:
    XR_EXT_user_presence, XR_FB_foveation, XR_FB_foveation_configuration, XR_FB_foveation_vulkan,
    XR_KHR_vulkan_enable, XR_KHR_composition_layer_depth, XR_KHR_visibility_mask, XR_META_performance_metrics
[Error] xrCreateInstance error: attempted to enable XR_FB_foveation without enabling required XR_FB_swapchain_update_state
```

Unity's `Player.log` then shows `xrCreateInstance: XR_ERROR_VALIDATION_FAILURE` and `Failed to initialize subsystem OpenXR Display`.

A PC is fine because SteamVR on Windows does not advertise `XR_FB_foveation`, so Unity never asks for it. The Frame advertises it because the headset supports foveated rendering. Games built with Unity OpenXR 1.15 or newer request the dependency correctly (WRATH: Aeon of Ruin VR, built with 1.17, runs fine).

## The fix

A tiny implicit OpenXR API layer, `XR_APILAYER_LOCAL_fb_foveation_depfix`. It sits between the game and SteamVR and, only when a game enables `XR_FB_foveation` without `XR_FB_swapchain_update_state`, appends the missing name. Every other call passes straight through.

The installer script [install-snapshotvr-fovfix.sh](../../scripts/snapshot-vr/install-snapshotvr-fovfix.sh):

- writes the layer's C source to `~/.local/share/xr_fovfix/`
- writes a manifest to `~/.local/share/openxr/1/api_layers/implicit.d/` (the folder the OpenXR loader scans for implicit layers, which the Steam Linux Runtime container shares with games)
- compiles the library with `gcc` on the Frame, or installs a prebuilt `~/libXrApiLayer_fovfix.so`, with an atomic `mv`

Nothing needs root; everything lives under the `steamos` home folder and survives SteamOS updates. The `.so` built from this source has SHA-256 `cf1cf35709303eab38259ff06e0755f3b6e2ee72be12aa4ab75e04a255833698`.

## Exact commands

The script lives in this repo under `scripts/snapshot-vr/`. Needs SSH, `gcc` on the Frame (or a prebuilt `libXrApiLayer_fovfix.so` copied to the home folder first), and the game installed.

```bash
scp scripts/snapshot-vr/install-snapshotvr-fovfix.sh steamos@frame.local:~/
# (and the prebuilt .so too, if you are not compiling)

# the sed only strips Windows line endings
ssh steamos@frame.local "sed -i 's/\r$//' install-snapshotvr-fovfix.sh && bash install-snapshotvr-fovfix.sh"
```

Expected output: `Compiling layer with gcc...` (or `installing prebuilt`), `Installed:` listing two files, `Done.`

Quit Snapshot VR if it is running and launch it again. It comes up in VR. No launch options are needed.

## Check it worked

The headset is the first test: Snapshot VR renders in VR and the controllers track. Underneath, the layer's own log gains lines each time the game starts:

```bash
ssh steamos@frame.local cat .local/share/xr_fovfix/xr_fovfix.log
```

```
[pid 24417] app 'Unity Application' (engine 'Unity') enabled XR_FB_foveation without XR_FB_swapchain_update_state -> adding XR_FB_swapchain_update_state
[pid 24417] xrCreateInstance returned -4
[pid 24417] app 'Unity Application' (engine 'Unity') enabled XR_FB_foveation without XR_FB_swapchain_update_state -> adding XR_FB_swapchain_update_state
[pid 24417] xrCreateInstance returned 0
```

The `-4` before the `0` is normal: Unity first asks for OpenXR 1.1, SteamVR on the Frame offers 1.0, Unity retries. An empty log means the loader did not find the layer; check both files exist in `implicit.d` and that `library_path` in the manifest points at the `.so`. `xrclient_SnapshotVR.txt` no longer shows the refusal and goes on to `Initializing CVulkanVRRenderer` and `XR_SESSION_STATE_FOCUSED`.

## Status and known issues

- The layer only acts when a game enables `XR_FB_foveation` without its dependency; every other game passes through untouched. Any other Unity OpenXR 1.14-era title that shows the same flat-window symptom is fixed by it as well, which is why it is worth leaving installed.
- Per-game off switch: launch options `DISABLE_XR_FOVFIX_LAYER=1 %command%`. `XR_FOVFIX_MODE=strip %command%` removes the foveation extensions instead of adding the dependency; it exists for troubleshooting and was not needed.
- Two harmless messages remain: `Oculus Platform Runtime was not found` in Player.log, and a second OpenXR startup a minute or two in when the game loads a level.
- Once Snapshot VR ships on Unity OpenXR 1.15 or newer, the layer has nothing left to do. The developer-side fix is one package upgrade (plugin 1.15 enables `XR_FB_swapchain_update_state` by default).

## Undo

```bash
rm ~/.local/share/openxr/1/api_layers/implicit.d/XrApiLayer_fovfix.json \
   ~/.local/share/openxr/1/api_layers/implicit.d/libXrApiLayer_fovfix.so
rm -r ~/.local/share/xr_fovfix
```

## Files in this repo

- [install-snapshotvr-fovfix.sh](../../scripts/snapshot-vr/install-snapshotvr-fovfix.sh): writes the layer source and manifest, compiles or installs the library.

## Credits

No mod is involved; the API layer was written for this project. This repo holds only scripts, no game data or binaries.
