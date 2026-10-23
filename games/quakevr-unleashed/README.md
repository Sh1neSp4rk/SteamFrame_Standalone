# Quake VR: Unleashed

**Status:** Working, with caveats. Native ARM64 build runs at 72 Hz only at a reduced eye resolution; the per-pixel shader is heavy for the Adreno 750, bloom must stay off, and controls are still the mod's Touch defaults.

| | |
|---|---|
| Upstream | quakevr by Vittorio Romeo, https://github.com/vittorioromeo/quakevr, tag v1.1.0-beta3 (commit 19c014e). Ironwail engine, OpenXR, OpenGL 4.6, C++ (Zancle library) |
| Game data | Steam's Quake: `Id1/PAK0.PAK` linked as lowercase `id1/pak0.pak`, hipnotic, rogue, plus the `quakevr` mod folder from the Windows release |
| Route | Native ARM64 build (OpenXR, OpenGL via zink). The Proton route was a dead end |
| Steam entry | "Quake VR" 2813758474, native shortcut, no compat tool, VR flag |
| Set up | 2026-10-22 (the Proton attempt was 2026-10-06); controls still the mod's Touch defaults |

## What it is

Vittorio Romeo's full reimagining of Quake for VR: hand interactions, physics, gore, new weapon models and its own sounds. It runs on the Frame after a long day of driver quirks, at a resolution the Adreno can afford. The Team Beef port is the better fit for Quake as it was; this one stays for its extras.

## What broke on the Frame

- **Proton/FEX and wineopenxr (dead end, 2026-10-06).** The Windows x86-64 build was tried as a sideloaded OpenXR shortcut. The engine, graphics and audio ran; VR never attached. Proton's OpenXR bridge needs an x86-64 OpenXR runtime inside the Steam Linux Runtime container, and pressure-vessel imports only SteamVR's ARM64 one: `Failed to load OpenXR 1 runtime for x86_64-linux-gnu from /opt/steamvr/steamxr_linux64.json: Unable to open "/opt"`. `XR_RUNTIME_JSON` and a symlinked `active_runtime.x86_64.json` did not help. Even then the OpenGL binding would have stopped it (`wine_xrCreateSession Unhandled graphics binding type: 1000023000`). Not fixable from user space.
- **Toolchain.** gcc cannot build the Zancle library the mod uses. The system OpenXR headers (1.1.40) lack `XR_META_body_tracking_full_body`, used by `vr_bodytrack_xr.cpp`; pkg-config's `Cflags` lost to `/usr/include`. The system `libopenxr_loader.a` is LTO-only.
- **x86 intrinsics.** `vr_ao.cpp` (the ambient-occlusion bake) and `vr_audio.cpp` use SSE and AVX intrinsics with an AVX target attribute.
- **OpenGL/zink: driver crash while compiling the world shader.** A `libgallium` thread crashed right after `link world|OIT 0; DITHER 0; MODE 1`. Cause: bindless textures (`GL_ARB_bindless_texture` is advertised but crashes). The game's automatic "GL safe mode" then kicked in on the next start and drew nothing usable.
- **OpenGL/zink: jittering menu and world, worse with head movement.** SteamVR reads the eye images before zink has finished them.
- **OpenGL/zink: black world at a full 72 Hz, menu fine, green hand pointers visible.** Any bloom, even the Low preset's 0.08, paints the eye images black. Found by mirror screenshots with the headset awake (the mirror is a crop of the game's own eye texture). Not traced in `vr_bloom.cpp` yet.
- **Performance.** With the headset worn, the eyes cost about 4.6 ms per megapixel plus 4.5 ms a frame: 39 ms at the recommended 1728x1728 per eye, 23 ms at 70%, 14 ms at 50%, 8 to 9 ms at about 650x650. Below roughly 20 fps SteamVR blanks the world while still showing menu panels, so a "black world with sound" is a frame-rate problem. Nothing else moved the number: retro mode, PBR, TAA, dynamic-light and map-light shadows and their filtering, specular, fog, tone mapping, the FSR upscaler, the hidden-area mask, float depth, single-pass stereo, particles, decals, the body, lightmaps, the sky, texture filtering, the desktop mirror and the graphics presets all measured within the noise of looking around. Overdraw is fine (the game's fragment counter reports shaded/kept = 1.0). Normal maps/parallax and shadowed map lights took frames to 150 ms in earlier tests.
- **Measurement trap.** With the headset asleep SteamVR sets `shouldRender` off, the game stops rendering the eyes and the profiler times the 1280x720 mirror window; a morning of unfocused tests wrongly said the cost was resolution-independent. The per-pass GPU timers are also meaningless on this tile-based GPU (the first scope absorbs the whole render pass).

## The fix

- Tag v1.1.0-beta3 has the author's own Linux OpenXR backend (`vr_xr_linuxgl.cpp`, GLX and EGL); master (1.0.1) does not. Sparse, shallow clone of `Quake/`, `CMakeLists.txt`, `VERSION`, `Misc/`, `docs/` and `Windows/OpenXR/include`.
- `q1_build.sh` builds with clang 19 and ninja, a pkg-config shim (`openxr.pc`) pointing at SteamVR's ARM64 `libopenxr_loader.so` with an rpath, and the repo's OpenXR 1.1.63 headers forced in with `-I`.
- `q1_port.py` routes the SSE and AVX intrinsics in `vr_ao.cpp` and `vr_audio.cpp` through SIMDe (`SIMDE_ENABLE_NATIVE_ALIASES`, headers in `~/PCVR/QuakeVR/simde`, MIT) on non-x86 and keeps the AVX target attribute x86-only. It also adds two environment switches: `QVR_GLSAFE_OFF=<mask of VR_GLSAFE_* features>` turns single GL features off (the "vendor workaround" path) without full safe mode, and `QVR_XR_SYNC` (0 upstream behaviour, 1 `glFlush`, 2 `glFinish` before each `xrReleaseSwapchainImage`).
- `quakevr-run.sh` sets `QVR_GLSAFE_OFF=2` (bindless off), `QVR_XR_SYNC=2` (glFinish; glFlush does not fix it), `SDL_VIDEO_X11_FORCE_EGL=0` (SteamVR needs the GLX binding), and launches with `-noglsafe +vr_backend openxr` so safe mode cannot switch itself on.
- `vr_bloom 0`.
- Resolution is the only lever. The on-headset `q1_lockin.sh` (not in this repo) writes `quakevr/autoexec.cfg` and the saved config:

```
vr_graphics_preset 1        // Low: dynamic-light shadows, no normal maps or map-light shadows
vr_bloom 0                  // black eyes through zink
vr_light_contrast 1         // Quake's own lighting; the mod's 2.5 darkens the shade
vr_gamma 0.9
vr_xr_eye_scale 0.85        // eye images at 85% of recommended
vr_dynres 1                 // dynamic resolution inside them...
vr_dynres_min 0.5           // ...between 50% and 100%,
vr_dynres_target 0.8        // aiming at 80% of the 13.9 ms budget
vr_dynres_log 1
vr_upscale_sharpness 0.85   // FSR sharpening (0.5 default), out to 60 degrees
vr_upscale_radius 60
vr_profile 1                // timing report every 5 s in the console log
vr_profile_interval 5
// ironwail.cfg: vid_fsaa "0" (was 4x MSAA), gl_texture_anisotropy "8"
```

Expect it softer than the other Quakes. The remaining levers are the dynres floor, the eye-image scale, or a real fix to the shader cost.

## Exact commands

The scripts live in this repo under `scripts/quakevr-unleashed/` and are copied to `~/PCVR/QuakeVR/` on the headset (the run script to `~/PCVR/QuakeVR-game/`).

```bash
ssh frame "bash ~/PCVR/QuakeVR/q1_build.sh"      # clang, ninja, pkg-config shim to SteamVR's loader; output ~/PCVR/QuakeVR/build/ironwail
```

`~/PCVR/QuakeVR-game`: the `ironwail` binary, lowercase links into Steam's Quake (`Id1/PAK0.PAK` as `id1/pak0.pak`), `hipnotic`, `rogue`, and the `quakevr` mod folder from the Windows release. `quakevr-run.sh` runs `./ironwail -basedir "$PWD" -game quakevr -noglsafe +vr_backend openxr`; log `quakevr-last.log`, per-run logs in `quakevr/logs/<date>/`, crash reports in `quakevr/crash/`. The run script sources `env.test` for test environment variables and expands `QVR_EXTRA` for test arguments.

```bash
ssh frame 'python3 ~/PCVR/bin/steam_shortcuts.py add "Quake VR" /home/steamos/PCVR/QuakeVR-game/quakevr-run.sh /home/steamos/PCVR/QuakeVR-game'
```

Measurement tools on the headset in `~/PCVR/QuakeVR/` (not in this repo): `q1_sweep.sh "name|cmds" ...` loads E1M1 with the profiler on and steps through cumulative console-command changes 500 frames apart, `q1_report.sh` prints GPU ms and fps before each step; `q1_profile.sh "cmds" "launch args" "ENV=val"` for one launch; `q1_shot.sh` for mirror screenshots per config (how bloom was caught); `q1_relaunch.sh` sets `QVR_EXTRA` and relaunches through Steam. Measure only with the headset awake and worn, and trust frame totals only.

## Controls

Still the mod's Oculus Touch defaults: left trigger off-hand attack, bumpers grab, A jump, B/Y weapon cycling. Not converted to the [standard layout](../../FRAME-LAYOUT.md).

## Status and known issues

- Working at 72 Hz at about 85% eye scale with dynamic resolution between 50% and 100%, softer than the other Quakes.
- Bloom paints the eyes black through zink; the Medium and higher presets and the menu's Bloom slider turn it back on. Not traced in `vr_bloom.cpp`.
- Bindless textures crash the driver; kept off through `QVR_GLSAFE_OFF=2`.
- Controls not on the standard layout.
- The game fetches the Quaddicted map index on start; harmless.
- Someone else is doing the same port: https://github.com/kblood/quakevr, "experimental native ARM64/Linux OpenXR port for Steam Frame, performance optimization in progress". Worth comparing notes.

## Undo

```bash
ssh frame "python3 ~/PCVR/bin/steam_shortcuts.py remove 2813758474; rm -rf ~/PCVR/QuakeVR ~/PCVR/QuakeVR-game"
# the quakevr mod folder inside Steam's Quake is listed in ~/PCVR/QuakeVR/installed-files.txt
```

## Files in this repo

- [q1_port.py](../../scripts/quakevr-unleashed/q1_port.py): idempotent patch routing SSE/AVX through SIMDe on ARM and adding the `QVR_GLSAFE_OFF` and `QVR_XR_SYNC` switches.
- [q1_build.sh](../../scripts/quakevr-unleashed/q1_build.sh): clang/ninja build with the pkg-config shim and the repo's OpenXR headers.
- [quakevr-run.sh](../../scripts/quakevr-unleashed/quakevr-run.sh): the Steam launch wrapper with the zink workarounds.
- [steam_shortcuts.py](../../scripts/common/steam_shortcuts.py): shared shortcut helper.

## Credits

- Quake VR by Vittorio Romeo (vittorioromeo/quakevr), on the Ironwail engine. SIMDe (MIT) for the intrinsics.
- Valve for OpenVR, SteamVR and the OpenXR runtime on the Frame.
- This repo holds only patches and scripts. No game data, mod assets or binaries.
