# ovrshim and hudbridge: overlays for a 32-bit OpenVR game under Proton on the Steam Frame

Two helpers written for [Far Cry VR](../../games/far-cry-vr/) that get a Proton game's overlay HUD into the headset when Proton's 32-bit OpenVR bridge cannot. The problem and the fix are generic enough to reuse.

## The problem

- Proton's i386 vrclient asserts and aborts the game in `IVROverlay::SetOverlayTexture` when the texture is Vulkan (`vroverlay_manual.c:465 !status`). CryVR draws its HUD and menus that way.
- SteamVR's fallback paths do not hold up: `SetOverlayRaw` stops for good after about 460 updates (error 23); `SetOverlayFromFile` shows only the first image per path and leaks about 4.7 MB in `vrcompositor` per new path until SteamVR restarts.
- SteamVR refuses to let one process set another process's overlay texture (error 12).

## The fix

**ovrshim** (`ovrshim.c`, `build.sh`) is a 32-bit proxy `openvr_api.dll`, built on the Frame with `clang --target=i686-pc-windows-msvc` and lld-link, with no imports (kernelbase is found through the PEB). Every export forwards to the mod's own library, renamed `openvr_api_real.dll`, except `VR_GetGenericInterface`, which patches slot 60 (`SetOverlayTexture`) of the `IVROverlay_026` vtable it hands out. The hook validates the texture, reads the overlay image back asynchronously (blit and downscale to 1024 pixels, double-buffered, only changed frames, at most every 33 ms) and writes it into `/tmp/farcryvr_bridge_<n>.shm` with a seqlock header and RGBA pixels. `FRAMEVR_HUD` selects `bridge` (default), `raw`, `file`, `skip` or `pass`; `FRAMEVR_HUD_EVERY`, `_MAX`, `_MS`, `_OPAQUE` and `_STRESS` tune it, `FRAMEVR_INPUT_LOG=1` logs IVRInput calls. Log: `ovrshim.log` in the game's working directory.

**hudbridge** (`hudbridge.cpp`, `build_bridge.sh`) is a native aarch64 OpenVR overlay application. It maps the shared files, uploads changed frames to its own Vulkan images and calls `SetOverlayTexture`, the path native apps use. It tries the mod's overlay by key first; since SteamVR refuses it, it draws a mirror overlay that copies the game overlay's transform, width, visibility, sort order (plus one), bounds, alpha and curvature about 80 times a second. The game overlay keeps one transparent pixel so the laser pointer still hits it. `hudbridge <pid>` follows that process and exits with it. Headers come from SteamVR's `hellovr_vulkan` sample on the Frame and it links the system `libopenvr_api.so`.

Reusing it for another game means changing the overlay keys and the shared-file prefix in both sources, and the install paths in `build.sh`.

## Files

- [ovrshim.c](ovrshim.c), [build.sh](build.sh): the proxy DLL and its build and install into `Bin32`.
- [hudbridge.cpp](hudbridge.cpp), [build_bridge.sh](build_bridge.sh): the native helper.

MIT, like the rest of this repository. Neither built binary is included.
