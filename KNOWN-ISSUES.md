# Known issues on the Steam Frame, for platform and mod developers

Findings from running PC VR games and mods standalone on a Steam Frame (SteamOS 0.4.5, SteamVR 2.18.2, Proton 11.0 (ARM64) and Proton Experimental (ARM64), Adreno 750 with the Turnip Vulkan driver and zink for OpenGL). Each entry says what was observed, how it was established, and who could fix it. The per-game folders under [games/](games/) have the full context and log excerpts.

## SteamVR on the Frame

### Legacy input: the simulated Oculus Touch profile drops the axis3 and axis4 ids

- **Observed:** a legacy OpenVR app (SelacoVR) using a legacy binding with `simulated_controller_type` set to Oculus Touch never received presses mapped to the axis3 and axis4 button ids. With no simulated controller type, all eight legacy ids per hand arrive.
- **Impact:** SteamVR's stock Frame legacy layout uses the simulation, so a legacy-input mod sees B, X and Y folded into one id and both bumpers folded into the trigger id. Mods feel "half connected".
- **Workaround:** write a legacy binding without `simulated_controller_type` and select it through `frame_controller_CurrentURL_legacy` ([vrsettings_bind.py](scripts/common/vrsettings_bind.py), [selaco_binding.py](scripts/selaco-vr/selaco_binding.py)).
- **Who:** Valve (SteamVR legacy input simulation).

### Legacy input has eight button ids per hand; the Frame has nine inputs

- **Observed:** legacy OpenVR input exposes `a`, `applicationmenu`, `grip` and the `axis0` to `axis4` presses per hand. The Frame controller has trigger, bumper, grip, stick click, A, B, X, Y and menu on the right, so one input is always unbound (Selaco VR leaves Y and d-pad right unbound).
- **Who:** inherent to legacy input; mods should move to the action manifest API.

### The Frame driver reports no `Prop_Axis<N>Type`

- **Observed:** `ETrackedDeviceProperty Prop_Axis0Type` to `Prop_Axis4Type` come back unset for the Frame controllers. Code that locates the thumbstick by scanning axis types (the OpenVR joystick code in GZDoom-based ports) finds no joystick axis and ignores the stick.
- **Workaround:** fall back to axis 0 when no axis type matches ([selaco_port.py](scripts/selaco-vr/selaco_port.py)).
- **Who:** Valve (frame_controller driver).

### A second `VR_Init` as an Overlay application segfaults inside vrclient.so

- **Observed:** SelacoVR calls `VR_Init` a second time, as `VRApplication_Overlay`, to set up its menu overlay. The Linux runtime logs "called VR_Init 2 times", shuts the client down, and the next interface call segfaults inside `vrclient.so`. The Windows runtime tolerates it.
- **Workaround:** one `VR_Init` per process; the overlay interface is reachable from the scene init.
- **Who:** mod authors porting from Windows; Valve could return an error instead of tearing down.

### `openvr_capi.h` struct packing on Linux

- **Observed:** code using OpenVR's C API with `openvr_capi.h` read every button and axis of `VRControllerState_t` as zero. The C++ header packs the struct 4-byte on Linux; the C header leaves default packing, so the layouts differ and the fields are read from the wrong offsets.
- **Workaround:** pack the C declaration to match (`#pragma pack(push, 4)` around `VRControllerState_t` on Linux).
- **Who:** Valve (openvr_capi.h); anyone using the C API on Linux.

### The left d-pad's click arrives as pulses, and its touch is one shared sensor

- **Observed:** traced from a mod's SteamVR action events (Hollow Knight VR): a held left d-pad click reaches the app as pulses of about 150 ms every 250 ms that stop after about one second even while the button stays down. The d-pad's touch input is a single capacitive sensor, so a resting thumb fires up, left and right together. The digital click never reaches an app as a plain press and release. The driver is read-only with no settings.
- **Impact:** any hold action on the d-pad (walking in a 2D game, held menu scrolling) breaks after a second.
- **Workaround:** bind the d-pad to tap actions only. Where a hold is needed, bind the d-pad touch to a spare action and latch the last pulsed direction while the touch lasts ([FrameVR_HK.cs](scripts/hollow-knight-vr/FrameVR_HK.cs)).
- **Who:** Valve (frame_controller driver).

### Custom OpenXR bindings for Proton apps: single profile, no Touch typing, no stray haptics

- **Observed (Red Faction VR):** SteamVR builds a Proton OpenXR app's input context from auto-generated defaults in `~/.config/openvr/config/openxr/steam.app.<id>_<type>_N_binding.json`, rewritten every launch, and only honours a user-selected custom binding when that context holds a single interaction profile. An app that suggests both Touch and Index bindings keeps its defaults. Making the Index default unwritable (a read-only `{}`) produces `SetXrInputConfig failed. Unable to write` and `Loading 1 bindings`, after which the custom file applies.
- A custom file typed `controller_type: oculus_touch` is treated as Touch paths and pushed through the Frame remap, which drives each hand's trigger and bumper from the one Touch trigger; type it `frame_controller` instead.
- A file carrying a haptic entry for an action the app does not define (`Unknown action ... when loading binding file`) is dropped whole; keep `"haptics": []`.
- **Without a VR restart:** an API layer that forwards only the game's Touch suggestion from `xrSuggestInteractionProfileBindings` ([tools/frame-quadfix](tools/frame-quadfix/), `FRAMEXR_PROFILES`) keeps the context at one profile, and a `frame_controller`-typed binding written over the auto-generated `steam.app.<id>_oculus_touch_0_binding.json` and made read-only is loaded at the next launch (Unreal Revived VR). No `steamvr.vrsettings` edit and no session restart.
- **Who:** Valve (SteamVR OpenXR input for Proton apps).

### Apps started from a non-Steam shortcut may need steam_appid.txt

- **Observed:** a Steamworks game launched through a non-Steam shortcut in its own prefix fails its Steam init (`Steam failed to initialize` in Hollow Knight VR, `[Fatal] Stage 2 Boot Failure: Steamworks is not initialized` in Circuit Superstars VR) until a `steam_appid.txt` with the app id sits in the game folder. The app then connects to SteamVR as `steam.app.<real id>`, while bindings keyed on the shortcut id still apply.

### No XR_KHR_composition_layer_cylinder

- **Observed:** SteamVR's OpenXR runtime on the Frame does not offer `XR_KHR_composition_layer_cylinder`. Quest ports that draw their menus on a curved cylinder layer (Team Beef's CSVR) have to fall back to a flat `XrCompositionLayerQuad` of the arc's width at the arc's distance ([cs_port.py](scripts/counter-strike-vr/cs_port.py)).
- **Who:** Valve (SteamVR OpenXR runtime).

### A custom OpenXR binding naming an unknown action is dropped whole

- **Observed:** SteamVR learns an app's actions only from the app's own suggested bindings. A custom binding file that names an action the app never suggested (a port that adds bumper, view or d-pad actions without a Touch suggestion for them) is dropped entirely: `Loading 0 bindings`, no input at all and no menu pointer.
- **Workaround:** give every new action a suggestion in the app's own interaction profile, then regenerate SteamVR's default binding before locking the Frame binding over it ([cs_rebind.sh](scripts/counter-strike-vr/cs_rebind.sh)).

### No text keyboard inside OpenXR on the Frame

- **Observed:** a native OpenXR app has no system keyboard to call (the Quest builds use Android's); a game's name prompt cannot be answered in the headset (CSVR's multiplayer menu). SteamVR's own keyboard, reachable to OpenVR apps, closes itself when opened for a hidden overlay (see the AvP entry above).
- **Workaround:** write the value from a file or the Steam persona name at launch ([cs_name.py](scripts/counter-strike-vr/cs_name.py)).

### Overlay fallback paths: SetOverlayRaw dies, SetOverlayFromFile leaks, no cross-process textures

- **Observed (Far Cry VR):** `IVROverlay::SetOverlayRaw` stops working for good after about 460 updates (error 23). `SetOverlayFromFile` shows only the first image per path, and each new path leaks about 4.7 MB in `vrcompositor` that is never freed until SteamVR restarts. One process cannot set the texture of another process's overlay (error 12).
- **Workaround:** a native helper process that draws a mirror overlay of its own, copying the game overlay's transform, size, visibility, sort order, bounds, alpha and curvature at about 80 Hz, and feeds it with `SetOverlayTexture` from frames the game writes to a shared file ([tools/far-cry-ovrshim](tools/far-cry-ovrshim/)).
- **Who:** Valve (SteamVR overlay raw and file paths).

### Per-eye XrCompositionLayerQuad pairs are rejected

- **Observed:** a Proton OpenXR game that submits its 2D panel as two quad layers, `eyeVisibility` LEFT and RIGHT, the right one from slice 1 of an `arraySize=2` swapchain (Unreal Revived VR's menu and HUD), has every such `xrEndFrame` rejected by SteamVR on the Frame: `compositor failed EndFrame()`, `XR_ERROR_POSE_INVALID` (-39), with a unit-length quaternion. The panel shows on the monitor and in theater mode, never in the headset.
- **Workaround:** an implicit OpenXR API layer that shows the LEFT quad to both eyes and drops the RIGHT one ([tools/frame-quadfix](tools/frame-quadfix/)); zero rejected frames afterwards.
- **Who:** Valve (SteamVR's OpenXR compositor on the Frame, or wineopenxr's quad-layer translation).

### Identical full-bounds images to both eyes do not fuse on the Frame

- **Observed:** a mod that presents a 2D screen by submitting the same image to both eyes at full texture bounds (Tribes 2 VR's shell: "no eye crop available - submitting full bounds, image will double") shows doubled menus. The Frame's per-eye projections are wide and mirror-asymmetric: raw tangents left -1.65, right 1.22, top -1.73, bottom 1.17. The same pixel sits at a different angle in each eye, so a shared image can never line up.
- **Workaround for mod authors:** crop each eye from the submitted image using the `GetProjectionRaw` tangents, or render the screen quad per eye with the headset projection, or put 2D screens on an overlay. Headsets with symmetric lenses hide this bug.

### SteamVR blanks the world below about 20 fps

- **Observed:** a scene application rendering slower than roughly 20 fps shows a black world while its own menu panels and overlays stay visible and audio keeps playing. It looks like a rendering bug and is a frame-rate problem. Quake VR: Unleashed at 1728x1728 per eye (39 ms a frame) is the reference case.
- **Workaround:** lower the eye resolution until the game holds a rate SteamVR will reproject.
- **Who:** expected compositor behaviour; worth documenting for mod authors.

### SteamVR's keyboard closes itself when opened for a hidden overlay

- **Observed:** `ShowKeyboardForOverlay` on a hidden overlay (the AvP VR port's text entry) opens the keyboard and closes it at once: `KeyboardOpened_Global` then `KeyboardClosed`, with no Done or Back event.
- **Workaround:** detect the close within 3 s and fall back to the mod's own on-screen keyboard ([AVPVR-frame-keyboard.patch](scripts/avp-vr/AVPVR-frame-keyboard.patch)).
- **Who:** Valve.

### `vrcmd --set-settings-string` neither persists nor applies

- **Observed:** selecting a binding with `vrcmd --set-settings-string steam.app.<id>/<key> ...` changes vrserver's in-memory settings only. It is not what vrserver reads when an app connects, and it is gone after a restart.
- **Workaround:** write the per-app section into `~/.config/openvr/config/steamvr.vrsettings` ([vrsettings_bind.py](scripts/common/vrsettings_bind.py)) and restart the VR session with `systemctl --user restart gamescope-session.target`. OpenXR bindings need that restart once; legacy binding files reload per launch after they are selected.
- **Who:** Valve.

### Frame-timing measurements are only valid while the headset is awake

- **Observed:** with the headset asleep SteamVR sets `shouldRender` off; native games skip the eye passes and render only their desktop mirror. Any timing taken then measures the wrong thing. On this tile-based GPU, per-scope GPU timestamp profilers are also unreliable (the first scope absorbs the whole render pass); only frame totals were trustworthy.
- **Who:** documentation; mod authors with built-in profilers.

### Never kill vrserver

- **Observed:** `pkill -9 vrserver` leaves the compositor and headset driver in a state only a full session restart clears. Stop in the Steam menu killed the launch wrapper but left Wine processes alive in the container; the old wineserver then held the prefix lock and the next launch hung in `wineserver -w`. Kill a Proton launch through its systemd scope (`systemctl --user kill --signal=KILL app-steam-app<id>-<pid>.scope`).

## OpenGL on zink and Turnip

### Finish before releasing a swapchain image

- **Observed:** SteamVR can read an OpenXR swapchain image before zink has finished drawing it. The view jitters, worst when turning the head; a menu panel drawn later in the frame looks fine. Quake II VR showed it on the right eye only (the left was implicitly flushed by the mirror window's swap); Quake VR: Unleashed on both eyes.
- **Workaround:** `glFinish()` immediately before `xrReleaseSwapchainImage` for each eye. `glFlush()` is not enough. The cost is pipelining, so GPU time must stay well under the 13.9 ms frame.
- **Who:** Mesa (zink) or SteamVR's OpenXR runtime; mod authors in the meantime.

### Bindless textures crash the driver

- **Observed:** `GL_ARB_bindless_texture` is advertised, and using it crashed inside `libgallium` while the world shader was compiled (Quake VR: Unleashed).
- **Workaround:** do not use bindless textures even though the extension is listed.
- **Who:** Mesa (zink/Turnip).

### Bloom paints the eyes black

- **Observed:** in Quake VR: Unleashed any bloom amount, even 0.08, turned the eye images black through zink while the game ran at 72 Hz and its menus and hand pointers drew normally. Caught with mirror screenshots with the headset awake. Not traced further.
- **Who:** unknown; the mod's bloom pass or zink.

### Framebuffer limits

- **Observed:** a 3456x3456 8x multisampled framebuffer cannot be allocated (`VR: incomplete multisample framebuffer`, black screen) in Quake II VR's shipped config. 1728x1728 with 2x MSAA works.

### Steam's session caps Mesa at OpenGL 4.3

- **Observed:** Steam's game session exports `MESA_GL_VERSION_OVERRIDE=4.3` (and the GLSL override). A native port that asks for a 4.6 core context fails with `GLXBadFBConfig`. zink itself offers 4.6.
- **Workaround:** `unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE` in the launch wrapper. Also `SDL_VIDEODRIVER=x11`, since the OpenXR OpenGL binding available is the Xlib/GLX one.

### No single-buffered GLX fbconfig under gamescope

- **Observed:** a port requesting a single-buffered window (q3vr's `SDL_GL_DOUBLEBUFFER 0`) failed with `GLXBadFBConfig`. Request double buffering; the window is only a mirror.

### Performance envelope

- The game shares the Adreno 750 with the compositor; budget about 10 ms of GPU per frame at 72 Hz. Quake VR: Unleashed measured about 4.6 ms per megapixel plus 4.5 ms fixed, and no setting other than resolution moved it. The recommended 1728x1728 per eye is beyond heavy fragment shaders; 72 Hz held at about 650x650 per eye for that game.

## Proton and FEX

### wineopenxr has no OpenGL graphics binding

- **Observed:** an OpenGL game using OpenXR dies at `wine_xrCreateSession Unhandled graphics binding type: 1000023000` (`XR_TYPE_GRAPHICS_BINDING_OPENGL_WIN32_KHR`). Only D3D11, D3D12 and Vulkan sessions are bridged. All the Quake ports and AvP VR hit this.
- **Who:** Valve (Proton's wineopenxr). Affected games were rebuilt natively instead.

### The container imports only SteamVR's ARM64 OpenXR runtime

- **Observed:** a sideloaded x86-64 OpenXR game runs flat: `Failed to load OpenXR 1 runtime for x86_64-linux-gnu from /opt/steamvr/steamxr_linux64.json: Unable to open "/opt"`. `XR_RUNTIME_JSON` and a symlinked `active_runtime.x86_64.json` did not help.
- **Who:** Valve (pressure-vessel / SteamVR runtime import).

### `SetSkyboxOverride` with OpenGL textures asserts in the ARM64 vrclient bridge

- **Observed:** `fixme:vrclient:set_skybox_override_init Conversion for type 1 is not supported.` followed by `err:msvcrt:_wassert (L"!status",L"../src-vrclient/vrcompositor_manual.c",2264)` and the game dies. Type 1 is `TextureType_OpenGL`. Proton 11.0 (ARM64) asserts; Proton Experimental (ARM64) accepts the call. Ordinary OpenGL eye submits work in both. Seen in Doom 3 BFG VR (Windows build) and Half-Life: VR Mod. The same call also crashed the native ARM64 vrclient, so Doom 3 BFG VR's native build skips it.
- **Who:** Valve (Proton 11 vrclient should return an error, as Experimental does). The two log lines plus the two games are a complete bug report.

### SelacoVR's Windows build dies in a C++ exception at startup

- **Observed:** under Proton Experimental (ARM64) the engine starts, finds its ipk3 and mods, opens OpenAL, then throws a C++ exception ending in `STATUS_NONCONTINUABLE_EXCEPTION` about four seconds in, with `+vr_mode 0` as much as in VR. No crash dialog; `-stdout` prints nothing through Wine; only `WINEDEBUG=+seh,+process` in a Proton log shows it. Not reproduced natively (the native ARM64 build works), so it is the engine under FEX.
- **Who:** FEX or Proton; the mod runs natively instead.

### Harmony patches on Unity native methods recurse forever under FEX

- **Observed:** a BepInEx mod that Harmony-patches Unity native setters (`Transform.set_*_Injected`, `GameObject.set_tag`, `Camera.ResetProjectionMatrix`) overflows the main thread's stack right after SteamVR initialises (DUSK HD VR, Hollow Knight VR, Circuit Superstars VR; all three use the UnityVR_Bepinex core).
- **Workaround:** strip those patches from the plugin when the mod's features do not need them.
- **Who:** FEX (and Harmony's native-method patching). `WINEDEBUG=+seh` alone also overflows Mono's stack under FEX.

### Windows kernel drivers are out of reach

- **Observed:** a mod that drives the game through a virtual Xbox pad via the ViGEmBus driver never produces input, because Proton cannot load the driver. Unity additionally ignores an XInput device unless a real game-controller device exists in the prefix.
- **Workaround:** a `ViGEmClient.dll` and `xinput1_3.dll` pair that share pad state in memory, plus an idle Linux uinput Xbox 360 pad so Wine reports a device ([games/dusk-hd-vr](games/dusk-hd-vr/)).

### Steam Input's virtual pad takes XInput slot 0 through Wine's xinput1_4

- **Observed:** a Rewired-based Unity game (Circuit Superstars VR) loads Wine's own `xinput1_4.dll`, where Steam Input's virtual pad for the shortcut enumerates first, so a second pad provided through an `xinput1_3.dll` shim (Unity's native layer) lands in slot 1 and the game seats the player at pad 2. Steam Input's pad also goes quiet once SteamVR takes the Frame controllers.
- **Workaround:** serve the shim under every XInput name (`xinput1_1`, `xinput1_2`, `xinput1_3`, `xinput1_4`, `xinput9_1_0`) with matching `WINEDLLOVERRIDES`, so the game sees one pad in slot 0 ([cs_xinput14.sh](scripts/circuit-superstars-vr/cs_xinput14.sh)).

### UnityVR_Bepinex mods without a VR-to-pad bridge

- **Observed:** older UnityVR_Bepinex cores have no `vrControllersSupport`; a mod built on one (Circuit Superstars VR) is gamepad-only and gets no input from the Frame controllers once SteamVR owns them. A BepInEx plugin that copies the mod's SteamVR action set onto a ViGEm pad every frame bridges it ([FrameVR_CS.cs](scripts/circuit-superstars-vr/FrameVR_CS.cs)). The mod's `UpdateSpeedHaptics` also throws a NullReferenceException every frame without a bHaptics vest; log noise only.

### ARM64 runtime DLLs in the prefix

- **Observed:** Proton's prefix ships ARM64 builds of `vcruntime140_1.dll` and friends. An x86-64 mod DLL or helper exe that imports them fails to load (Borderlands VR, Deus Ex HR VR). Proton never ships `mfc140u.dll` at all (Metal: Hellsinger VR's Razer plugin).
- **Workaround:** an x86-64 copy beside the executable, which Wine resolves first.

### Install scripts that overwrite the prefix's runtime

- **Observed:** Halo MCC's Steam install script runs the Easy Anti-Cheat setup, whose bundled Visual C++ redistributable writes Microsoft x86-64 runtime DLLs into `system32`. Wine then cannot boot the prefix (`Loading library ucrtbase.dll ... failed (error c000007b)`), and every launch dies in three seconds. "Verify integrity" can reapply it.
- **Who:** Valve (Proton on ARM64 should protect its ARM64 system DLLs from x86-64 redistributables).

### Wine's built-in d3dcompiler_47 rejects SV_ClipDistance

- **Observed:** a game that compiles HLSL at runtime through `d3dcompiler_47` (Unreal Revived's D3D12 renderer, `Scene.vert`) gets a failed compile from Wine's built-in vkd3d-shader on `SV_ClipDistance`, then crashes dereferencing the missing shader right after the VR session begins.
- **Workaround:** Microsoft's x64 `d3dcompiler_47.dll` from a Windows installation next to the exe with `WINEDLLOVERRIDES=d3dcompiler_47=n,b`. The DLL is Microsoft's and is not redistributed here.
- **Who:** Wine / vkd3d-shader.

### Inno Setup "x64compatible" installers refuse Proton's ARM64 prefix

- **Observed:** an installer with `ArchitecturesAllowed=x64compatible` asks Windows which machine types it can run; Proton's ARM64 Wine answers "x86 and Arm64" even with the prefix set to Windows 11, so setup quits with "does not support the version of Windows" (Unreal Revived 0.9.0). Installers whose work is done in PowerShell scripts cannot run in the prefix either.
- **Workaround:** run the installer on a Windows PC with the same target paths the prefix uses, copy the result into the prefix, then remove it on the PC.
- **Who:** Wine (reporting x64 emulation capability on ARM64).

### Engines that leave a crash flag open a dialog nobody can see

- **Observed:** Unreal 227 leaves `System64\Running.ini` after a crash and opens a "not shut down properly" recovery dialog at the next start, invisible in VR. A launch wrapper that deletes the file first avoids it.

### Wine debug logging inside a custom DXVK build can corrupt registers

- **Observed:** fholger's DXVK fork for Far Cry VR crashed at device creation under Proton: its Wine debug-output logging (`__wine_dbg_output`) clobbers ESI in that MSVC build, so `vkGetInstanceProcAddr` became a module handle. `DXVK_LOG_LEVEL=none` avoids the logging path. Noted because the symptom looks like a Frame or FEX problem and is not one.

### Mods that patch Direct3D in memory need x86-64 DXVK

- **Observed:** a VR mod using MinHook to patch `d3d11.dll` crashes with exception `C000001D` (illegal instruction): Proton ARM64's DXVK is a native ARM64 library and the mod writes x86-64 trampolines into it (Halo MCC VR).
- **Workaround:** copy Proton's x86-64 DXVK (`dxgi.dll`, `d3d11.dll`, `d3d10core.dll`) beside the game exe.

### Proton's 32-bit vrclient asserts on Vulkan overlay textures

- **Observed:** a 32-bit OpenVR game that gives `IVROverlay::SetOverlayTexture` a Vulkan texture (Far Cry VR's CryVR, whose DXVK fork draws the HUD and menus on overlays) is aborted by Proton's i386 vrclient bridge: `vroverlay_manual.c:465 !status`. Eye textures submit fine; only the overlay path asserts.
- **Workaround:** a proxy `openvr_api.dll` that intercepts the call, reads the image back asynchronously and hands it to a native helper ([tools/far-cry-ovrshim](tools/far-cry-ovrshim/)).
- **Who:** Valve (Proton's vrclient, i386 overlay texture conversion).

### 32-bit OpenXR works through the i386 wineopenxr

- **Observed:** Proton Experimental (ARM64) ships an i386 wineopenxr, and 32-bit OpenXR games on Direct3D 11 reach SteamVR through it (F.E.A.R. VR, Red Faction VR). Red Faction VR's own README calls SteamVR unsupported because Windows SteamVR has no 32-bit OpenXR runtime; on the Frame it works.

### Easy Anti-Cheat

- **Observed:** EAC's Wine module (`easyanticheat_wine_x64.eac`) is only served for games whose publisher enabled Linux support; without it the game treats anti-cheat as missing and exits quietly (Dragon Ball FighterZ). Games with EAC integrity certificates fail their own startup check ten seconds in with a stubbed `NtRaiseHardError` (Breachers). Proton's EAC runtime does not engage under ARM64 Proton either way.
- **Who:** publishers; Epic.

### TribesNext's Ruby login helper page-faults under FEX

- **Observed:** TribesNext RC2a authenticates Tribes 2 through `rubyintersect.dll` and `msvcrt-ruby190.dll`. Under FEX the Ruby runtime page-faults, the TribesNext scripts then report an unpatched exe, and no account can log in. `-nologin` gives the offline shell only. The TribesNext 20250922 preview (native authentication, advertised Wine support) is untried.

### No readable depth under zink for depth-stereo mods

- **Observed:** a mod mode that reconstructs stereo from the depth buffer (Tribes 2 VR's `stereoMode 2`) finds no usable depth from this OpenGL 1.x-era engine under zink. Per-eye rendering modes are the only option.

### No .NET or Wine Mono in the Proton prefix

- **Observed:** a .NET Framework launcher dies at once with `err:mscoree:load_mono Could not load Mono into this process` (Breachers). UEVR needed the .NET 6 Desktop runtime installed per prefix.

### Steam strips backslashes from launch options

- **Observed:** a Windows path in Launch Options loses its backslashes, in a game's launch options and in a non-Steam shortcut's (Tribes 2 VR's launcher received `C:DynamixTribes2GameDataTribes2.exe`). Anything that needs one (`PROTON_REMOTE_DEBUG_CMD`, DLL overrides with paths, an exe path argument) has to go through a wrapper script that adds it: `/home/steamos/script %command%`.

### Steam's launch prompts do not show in the headset

- **Observed:** a game with several launch entries makes Steam wait on a "which one?" picker and then an interstitial notice (`LaunchApp waiting for user response to ShowLaunchOption`), and neither surfaces in VR, so the game sits at "Launching". `steam steam://launch/<appid>/<entry>` skips the picker and `SteamClient.Apps.ContinueGameAction(<id>)` through the client's debug port answers the notice.

### Steam downloads stall while the headset sleeps

- **Observed:** Steam downloads only in bursts while the headset is asleep (its radio naps), and `appmanifest` `BytesDownloaded` stays 0 until the download commits, so progress looks stuck. Keep the headset awake for large downloads.

### Proton's native OpenXR setup reads `XR_RUNTIME_JSON` too

- **Observed:** setting `XR_RUNTIME_JSON` for a Windows OpenXR game (to point at a mod's own runtime) also redirects Proton's wineopenxr registration and Direct3D 11 support disappears (F.E.A.R. VR). Leave it unset. Wine also looks "elevated" to the OpenXR loader, which then ignores `XR_RUNTIME_JSON` for 32-bit apps; registering the runtime under `Software\Wow6432Node\Khronos\OpenXR\1` in the prefix registry works instead (BioShock VR).

### Strict OpenXR extension dependencies

- **Observed:** SteamVR on the Frame advertises `XR_FB_foveation` and enforces its spec dependency: `xrCreateInstance error: attempted to enable XR_FB_foveation without enabling required XR_FB_swapchain_update_state`. Unity OpenXR plugin 1.14 games (Snapshot VR) request the former without the latter and fall back to a flat window. Unity fixed it in plugin 1.15.
- **Workaround:** an implicit OpenXR API layer that appends the dependency ([install-snapshotvr-fovfix.sh](scripts/snapshot-vr/install-snapshotvr-fovfix.sh)).
- **Who:** game developers (upgrade the plugin); Valve could relax the check.

## Native ARM64 builds

- `/usr/lib/libopenxr_loader.a` is a 14 KB stub, and `sdl2-config --libs` puts `-L/usr/lib` first, so `-lopenxr_loader` links the stub and every `xr*` symbol is undefined. Link `/opt/steamvr/bin/linuxarm64/libopenxr_loader.so` by full path with an rpath.
- The system OpenXR headers are 1.1.40; projects needing newer extensions bring their own.
- GCC 15 defaults to C23: `true`/`false` are keywords, K&R prototypes and implicit `int` are errors. `-std=gnu99` or `-std=gnu17`, `-fcommon`, `-fpermissive` get old engines compiling.
- A plain `inline` function used from another translation unit links on MSVC and not on GNU C99 (no external definition); RealRTCW's game module loaded with an undefined symbol and the campaign died on "VM_Create on game failed". Check every module with `ldd -r x.so | grep 'undefined symbol'`.
- ELF symbol interposition: a game executable that exports symbols its plugin `.so` also defines (Quake II's `R_SetMode`) needs `-Wl,-Bsymbolic` on the modules, or the module calls the executable's copy.
- ARM's `char` is unsigned; `-fsigned-char` fixed garbled GUI text in Doom 3 BFG VR.
- `ptrace` attach is blocked for games; run the game under gdb from inside its launch wrapper instead.
- Linux truncates process names to 15 characters (`RealRTCW.aarch6`); use `pkill -f` with the full name.
- The headset has no Python Pillow, which several ports' setup scripts want for menu art and weapon-wheel icons; the games work without it.
- Quest ports assume Android: an EGL/OpenGL ES session, an Android start-up hook that creates the OpenXR instance, a mobile renderer forced in VR, haptics through an Android service, files under `/sdcard`. Each needs a desktop equivalent (CSVR's port script is the template). Out-of-bounds reads that were harmless on Android can crash here (CSVR's model lookup).
- `gitlab.xiph.org` has answered 502 for days; the libogg, opusfile and vorbis submodules are available at the same commits from the `github.com/xiph` mirrors.
