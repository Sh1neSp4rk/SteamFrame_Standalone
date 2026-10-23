# Half-Life: VR Mod (the original Half-Life)

**Status:** Dead end, for now — Proton 11's VR bridge aborts the game over an OpenGL skybox assertion; Proton Experimental gets past that, after which the mod's own VR setup fails a step later and falls back to a flat window, and the mod was uninstalled before that final error message was captured.

| | |
|---|---|
| Steam app | 1908720, 4.1 GB (ships its own GoldSrc engine and Half-Life content; Half-Life itself need not be installed) |
| Engine / VR API | GoldSrc, 32-bit, OpenGL; OpenVR via the mod's `openvr_api.dll` |
| Route | Proton 11.0 (ARM64) + FEX, Steam's default; also Proton Experimental (ARM64) |
| Diagnosed | 2026-10-10 |

## What it is

A Steam-distributed VR mod for the original Half-Life. It ships its own GoldSrc engine and content, so the base game does not need to be installed. The app has two launch entries: the VR game (`hl.exe` with the mod's arguments) and a .NET config tool, `HLVRConfig.exe`, which is a separate entry and is never involved in the failure.

## What you see

Press Play, the headset blinks into the game's loading state and drops back to SteamVR Home a few seconds later. Steam may keep showing the game as running until you stop it.

## Why it fails on the Frame

### Proton 11.0: the skybox assertion in Proton's compositor bridge

- Steam's launch entry is fine: it starts `hl.exe` directly with the mod's arguments. The engine loads, loads the mod's `client.dll` and `openvr_api.dll`, and connects to SteamVR. `vrclient_hl.txt` shows a 256x256 GL texture reaching the compositor. Then, in the Proton log:

```
fixme:vrclient:set_skybox_override_init Conversion for type 1 is not supported.
err:msvcrt:_wassert (L"!status",L"..\\src-vrclient\\vrcompositor_manual.c",2264)
```

- Type 1 is `TextureType_OpenGL`. The mod's source (`VRHelper::Init()` in `src/cl_dll/VRHelper.cpp`) calls `SetSkybox("desert")` unconditionally right after the compositor comes up, and `SetSkybox` builds six OpenGL textures and calls `IVRCompositor::SetSkyboxOverride`.
- The only setting that touches it, `vr_hd_textures_enabled`, picks HD or standard textures; both paths are OpenGL. None of the mod's 127 `vr_` cvars disables the skybox.
- On the Proton side, the published source of `vrcompositor_manual.c` (branch proton_11.0) converts DirectX 11 and 12 textures for the skybox, passes Vulkan through, and only prints that FIXME for anything else. Valve's ARM64 build of Proton is different: it routes textures through a manual conversion for the aarch64 compositor and contains an `assert(!status)` at line 2264 that the public tree does not have. When the OpenGL conversion fails, the assert fires and the game process dies.
- Frame submits of ordinary OpenGL eye textures work (GZDoom VR proves it), so this is specific to the skybox override path. Doom 3 BFG VR hit the same assertion under Proton.

### Proton Experimental: past the skybox, then the mod gives up

- With Proton Experimental (ARM64) forced, the assertion is gone: SteamVR's client log for the game shows `SetSkyboxOverride with 6 textures` accepted, the scene focus captured and a first 256x256 OpenGL texture delivered to the compositor.
- 50 milliseconds later the same log shows `VR_Shutdown called`, and the game then sits as a flat window in the theater until you quit it.
- In the mod's source the only route to `VR_Shutdown` is its own `VRHelper::Exit(message)` error handler, which fires when OpenGL function or framebuffer setup fails, when a GL error is caught on the first frame, or on a SteamVR quit event. It prints the message to the console and to stderr and shows a popup.
- That message was never captured: the one run armed with `-condebug` and Proton logging ended when the headset was power-cycled two seconds after the process started, and the mod was uninstalled afterwards.

### A second problem: Steam's launch prompts do not show in the headset

- This app has two launch entries. Pressing Play makes Steam wait on a "which one?" picker, and after that on a notice dialog, before it creates any process. In the headset neither popup surfaced, so the game sat at "Launching" indefinitely with nothing in `gameprocess_log.txt`.
- Steam's console shows it plainly: `LaunchApp waiting for user response to ShowLaunchOption`, then `... to ShowInterstitials`.
- Workaround: launching the VR entry directly with `steam steam://launch/1908720/vr` on the headset skips the picker, and `SteamClient.Apps.ContinueGameAction(<action id>)` through the debug port answers the notice. The action id is in `console_log.txt`. Any multi-entry game on the Frame can hit this.

## What was tried

- Stock launch on Proton 11.0 (ARM64): the skybox assertion, reproducibly, two seconds in.
- Proton Experimental (ARM64): skybox accepted, then the mod's own VR shutdown 50 ms later; game continues flat.
- Searched the mod for a skybox or VR-init switch: none exists among its 127 `vr_` cvars.
- Logged run to capture the error message: lost to a headset power-cycle; mod uninstalled on 2026-10-10 before a retry.

## What would fix it

- **Valve:** the Proton 11 bridge should return an error from `set_skybox_override_init` for OpenGL instead of asserting; Experimental already behaves. The two log lines above plus the Doom 3 BFG VR case are a complete bug report for the Proton issue tracker.
- **Next step if revisited:** reinstall, force Proton Experimental (ARM64), set launch options `PROTON_LOG=1 %command% -condebug`, launch from the headset and answer the two prompts, let it fail once, then read `valve/qconsole.log` and the stderr lines in `~/steam-1908720.log` for the `VRHelper::Exit` message. That message names the failing OpenGL step, which is the actual blocker.
- **The mod:** its maintainer takes issues on GitHub.

## State left on the headset

The mod is uninstalled. Its launch options were cleared. The Proton Experimental (ARM64) override is still recorded for the app, which is harmless and is the version to use if it is ever reinstalled. A stray `steamapps/common/Half-Life` folder (172 KB, two empty game folders and a log) is left over from an earlier Half-Life install and can be deleted.

## Credits

- Half-Life: VR Mod by 7empest (maintainer, GitHub).
