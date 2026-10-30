# Halo: The Master Chief Collection (flat and with the VR mod)

**Status:** Working. Standalone on the Frame, Halo 3 plays in VR with correct stereo, no weapon flicker and the mod's menu available in gameplay; Halo: CE and ODST play too (Halo 2, Reach and 4 not yet tested on the Frame). The same mod build also runs on a Windows PC streaming to the Frame, with the Frame's own button layout. Online matchmaking (EAC) stays off.

| | |
|---|---|
| Steam app | 976730, 97 GB |
| Engine / VR API | Direct3D 11 game; the mod talks to SteamVR through OpenXR |
| Mod | MCCVR (https://github.com/moistman42069/MCCVR-Halo-Build), built from source with [this repo's patch](../../scripts/halo-mcc/patches/) |
| Route on the Frame | Proton Experimental (ARM64) + FEX, Steam's default for this app |
| Frame fixes | prefix repair, wrapper, x86-64 DXVK beside the exe, patched mod, [frame_quadfix layer (Halo build)](../../tools/frame-quadfix/halo/), Frame controller binding |
| Date | runs since 2026-10-09; VR made good 2026-10-26 |

## What it is

Halo MCC is a Windows x86-64 title with Easy Anti-Cheat. Steam's launch menu offers two entries, "Halo: The Master Chief Collection" and "Halo: MCC Anti-Cheat Disabled". On the Frame the wrapper below turns those two entries into flat and VR. MCCVR is an injected VR mod that hooks Direct3D 11 and Halo's own render code in memory.

## What you see without the fixes

- Press Play on either entry. After about three seconds the button is back to Play. No window, no VR session.
- With the prefix repaired and the stock mod: VR starts, then crashes (`C000001D`) inside Direct3D.
- With that fixed too (stock MCCVR 0.5.1): Halo 3 and ODST freeze on level load; once running, Halo 3 looks cross-eyed and zoomed in, the gun flickers between the VR pose and the flat one in the right eye, the mod's menu never appears during gameplay, and the Frame's View button and D-pad do nothing.

## What broke on the Frame, and why

### 1. Steam install script: the prefix is poisoned by Easy Anti-Cheat's installer

MCC's Steam install script runs `easyanticheat\easyanticheat_eos_setup.exe install` inside the prefix. That installer bundles a Visual C++ 2017 redistributable and writes Microsoft's Windows x86-64 C runtime DLLs into `windows/system32` (and i386 ones into `syswow64`): `ucrtbase.dll`, `msvcp140.dll`, `vcruntime140.dll`, `concrt140.dll`, `vccorlib140.dll`, `vcomp140.dll`, `mfc140*.dll` and about forty `api-ms-win-*.dll` stubs. On a PC that is harmless. On the Frame, Proton's own system DLLs are ARM64 builds, and Wine's own boot process now tries to load Microsoft's x86-64 `ucrtbase.dll` from inside ARM64 code:

```
err:module:import_dll Loading library ucrtbase.dll (which is needed by L"C:\windows\system32\sechost.dll") failed (error c000007b)
err:module:... Importing dlls for L"C:\windows\system32\wineboot.exe" failed, status c0000135
Unhandled exception code c000001d   (in libarm64ecfex.dll)
```

Wine cannot even boot the prefix, so every launch dies in three seconds.

### 2. The VR mod crashes inside Direct3D (ARM64 DXVK)

Once the prefix was repaired the mod injected, reported "headset found on runtime SteamVR/OpenXR 2.18.2", printed "D3D11 hooks installed" and then died with exception `C000001D` (illegal instruction) at an address inside `d3d11.dll`. Proton ARM64's DXVK is a native ARM64 library; the mod's MinHook writes x86-64 trampolines into it. Proton also ships an x86-64 DXVK, and that one works.

### 3. Anti-cheat

EAC has no Linux path unless the publisher enabled it, and it does not run under FEX either way. EAC is never started on the Frame: its bootstrapper can reinstall the VC++ runtime that broke the prefix.

### 4. Halo 3 / ODST froze on level load

The mod's optional manual-reload and holster features patch Halo's native reload code. Under FEX the game's render thread then spun forever on the first level load (ODST and Halo 3; CE was fine). In the newer source, the "native VR action bridge" (`vr_action_mapping`) hooks Halo 3's input code and freezes it the same way, half a second after `Native VR action bridge H3: verified hooks installed`. All three stay off.

### 5. Halo 3 cross-eyed and zoomed (the big one)

Halo 3 rendered each eye with its own symmetric field of view, sized to that eye's lens (the Frame's lenses are not mirror images: left 58.8° out / 60.0° down, right 59.4° / 59.5°), but the mod published one field-of-view value for both eyes: whichever eye rendered last. The left eye then failed the mod's "does the render cover the lens" check, so every frame went to SteamVR as a whole slice labelled with the right eye's angles. The left picture was stretched against how it was drawn, which reads as cross-eyed, magnified and flat. ODST was never affected: it keeps one value per eye.

The fix renders both eyes with one shared view, 1% wider than the widest lens edge of either eye. The published value is then true for both, the check passes, and Halo 3 takes the same "native per-eye FOV + sub-rectangle" path as ODST. The log says `M2: submitting native per-eye FOV; eye 1 cover ... -> rect ...` instead of `M2 WARNING: the symmetric raster cover does not contain the headset's native per-eye frustum`.

### 6. Weapon flicker in the right eye

Halo 3 draws the first-person view as two models (arms and gun, separate render tags) and the mod swaps in the VR pose for each draw. The mod used each frame's pose once and threw it away, and also wiped it whenever an interpolation produced nothing. In about one right-eye pass in six Halo 3 drew from an older pose buffer the mod had never seen, so that draw fell back to the flat pose: arms held out in front with no gun, or the gun in the wrong place. The fix keeps the pose until a newer one replaces it and gives a draw with no pose the last pose of the same model. `FRAME_FP_REUSE=0` turns this off.

### 7. The mod's menu never showed during gameplay

SteamVR on the Frame rejected every frame (`XR_ERROR_POSE_INVALID`) that carried the 3D view plus the crosshair panel plus the head-locked menu panel, so the headset held the last good frame. CE, whose menu works, submits fewer panels. The frame_quadfix layer moves head-locked panels into room space and, while the menu is up, leaves the crosshair panel out. The menu then appears.

### 8. Controls: the mod is built for Touch-style controllers

The mod suggests bindings for Touch, Index, Vive, WMR and the simple controller. SteamVR auto-converts the Touch layout for the Frame, which puts X/Y on the left D-pad and makes the bumpers act like the triggers. The mod also has no Back or D-pad input at all. The Frame has A/B/X/Y on the right controller, a D-pad and View on the left, bumpers and triggers: every Xbox button has a Frame twin, so VR can match flat exactly (see [Controls](#controls-11-with-flat)).

## The fix (standalone on the Frame)

### Step 1: repair the prefix

[repair-mcc-prefix.sh](../../scripts/halo-mcc/repair-mcc-prefix.sh) moves every foreign runtime DLL into a backup folder inside the prefix (`compatdata/976730/polluted-backup-<date>/`) and copies Proton's own versions back. Nothing is deleted. On the test headset the result was `restored=12 backed-up-only=104`.

### Step 2: build the patched mod (on a Windows PC)

The mod needs Microsoft's compiler and shader compiler, so it is built on Windows and only the DLL is copied to the headset. The same build is what a streaming PC uses.

1. Install Visual Studio 2022 Build Tools with the C++ workload (about 7 GB; Microsoft's licence):
   ```powershell
   winget install --id Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
   ```
2. Clone the mod and apply the patch:
   ```powershell
   git clone https://github.com/moistman42069/MCCVR-Halo-Build
   cd MCCVR-Halo-Build
   git checkout b243af2       # the commit the patch was made against
   git am <this repo>\scripts\halo-mcc\patches\0001-steam-frame-halo3-stereo-flicker-tuning.patch
   ```
3. Put the three pinned dependencies where the build preset expects them (`out\deps\openxr-src`, `minhook-src`, `imgui-src`). The commits are in the mod's `CMakeLists.txt`; a shallow fetch by commit is enough:
   ```powershell
   foreach ($d in @(@('openxr-src','https://github.com/KhronosGroup/OpenXR-SDK.git','5267613edf3d937e3d77556a106a65c2f82b25c6'),
                    @('minhook-src','https://github.com/TsudaKageyu/minhook.git','c3fcafdc10146beb5919319d0683e44e3c30d537'),
                    @('imgui-src','https://github.com/ocornut/imgui.git','8936b58fe26e8c3da834b8f60b06511d537b4c63'))) {
       git init -q "out\deps\$($d[0])"; git -C "out\deps\$($d[0])" fetch -q --depth 1 $d[1] $d[2]; git -C "out\deps\$($d[0])" checkout -q FETCH_HEAD }
   ```
4. Build with the CMake that ships inside Build Tools (tests off, so no Python is needed), then stage the runtime files:
   ```powershell
   $vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -products * -property installationPath
   $cmake = "$vs\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
   & $cmake --preset release -DBUILD_TESTING=OFF
   & $cmake --build --preset release --target halo3xr halo3xr_launcher -- /m
   & $cmake --install out\build\release --config Release --prefix ..\stage\ModFiles --component dist
   & $cmake --install out\build\release --config Release --prefix ..\stage --component launcher
   ```
   `..\stage\ModFiles` now holds `HaloMCCVR.dll`, `assets\`, `licenses\`, `nvngx_dlss.dll` and the docs; `..\stage\HaloMCCVRLauncher.exe` is the new launcher.

### Step 3: install the mod on the Frame

1. Install MCCVR 0.5.1 once from its release page (`Halo-MCC-VR.zip`) so the launcher sits at `.../common/Halo The Master Chief Collection/Halo_MCC_VR/HaloMCCVRLauncher.exe`. **Keep that 0.5.1 launcher on the Frame**: it simply starts MCC and injects the DLL beside it, while the newer launcher is a menu that waits for a click you cannot make in the headset.
2. Copy `HaloMCCVR.dll` and `assets\fonts\*` from the build to `/tmp/mccbuild/` on the Frame and run [install_build.sh](../../scripts/halo-mcc/install_build.sh) with MCC closed. It backs up the 0.5.1 DLL once and installs the new one plus the frame_quadfix layer. Leave out `nvngx_dlss.dll` (NVIDIA only).
3. `Halo_MCC_VR/halomccvr.cfg` essentials: `resolution_scale = 0.50`, `vr_action_mapping = 0`, `manual_reload = 0`, `weapon_holsters = 0`, `manual_reload_disable_auto = 0`, `scope_enabled = 0` (the scope draws the world a second time). In MCC's own video settings choose the Performance preset.

### Step 4: give the game x86-64 DXVK

Copy Proton's x86-64 `dxgi.dll`, `d3d11.dll` and `d3d10core.dll` next to the game executable. Wine resolves DLLs from the executable's folder first, so these copies win over the ARM64 ones in `system32`, and the mod's hooks find x86-64 code to patch.

### Step 5: the layer, the wrapper and launch option

The [frame_quadfix layer, Halo build](../../tools/frame-quadfix/halo/) is built on the Frame (clang + lld, no Windows SDK) and registered as an implicit OpenXR layer in the prefix by [mcc_controls.sh](../../scripts/halo-mcc/mcc_controls.sh). It forwards only the Touch profile (so SteamVR honours a Frame binding), adds the View/D-pad bridge, and fixes the menu panel. Copy `tools/frame-quadfix/quadfix.c` and `tools/frame-quadfix/halo/*` to `~/PCVR/HaloMCCVR/frame-quadfix/` on the Frame (keeping the `halo/` subfolder) and the files in `scripts/halo-mcc/` to `~/PCVR/HaloMCCVR/`.

The wrapper [mcc](../../scripts/halo-mcc/mcc) is saved as `/home/steamos/mcc`. On top of the flat/VR mapping it sets the layer mode (`FRAMEXR_QUAD=norm`), keeps Proton's debug log off unless `MCC_LOG=1`, and passes the optional tuning files in `~/PCVR/HaloMCCVR/` to the mod. Launch Options:

```
bash ~/mcc %command%
```

| Steam entry | What Steam would run | What actually runs |
|---|---|---|
| Halo: The Master Chief Collection | `mcclauncher.exe` (starts EAC, then the game) | `MCC-Win64-Shipping.exe -no-eac`: flat, no anti-cheat |
| Halo: MCC Anti-Cheat Disabled | `MCC-Win64-Shipping.exe -no-eac` | `Halo_MCC_VR/HaloMCCVRLauncher.exe`: VR |

### Step 6: the Frame controller binding

[mcc_binding.py](../../scripts/halo-mcc/mcc_binding.py) writes [mcc_frame_binding.json](../../scripts/halo-mcc/mcc_frame_binding.json). SteamVR only accepts it as Halo's layout when it is written over the binding file SteamVR itself generated for the mod's current list of actions:

1. Move any old `~/.config/openvr/config/openxr/steam.app.976730_oculus_touch_*_binding.json` aside.
2. Start [watchbind.sh](../../scripts/halo-mcc/watchbind.sh) in the background, then launch the VR entry once. SteamVR writes a fresh `_0` file; the watcher overwrites it with the Frame layout and makes it read-only. That first launch still uses SteamVR's automatic layout.
3. From the next launch on, the Frame layout loads.

Redo this whenever a mod update or a layer change alters the action list: a read-only binding for an older list makes SteamVR load **nothing**, and every button goes dead (`SetXrInputConfig: Loading 0 bindings` in `vrserver.txt`).

## Controls: 1:1 with flat

| Frame | Sends | Notes |
|---|---|---|
| Right A / B / X / Y | A / B / X / Y | |
| Left / right trigger | LT / RT | |
| Left / right bumper | LB / RB | |
| Left / right grip (80%) | LB / RB | the mod's two-handed grip and holster gestures |
| Left D-pad | D-pad | through the layer's pad bridge |
| Left View | Back | through the pad bridge; held back in Halo CE, where Back is MCC's instant graphics switch and breaks the VR camera |
| Right Menu | Start | |
| Stick clicks | L3 / R3 | L3+R3 together recentres and opens the mod's menu |
| Left stick | move | |
| Right stick | turn (smooth or snap, mod setting) | you aim with the controller |

Each Halo game then follows its own MCC button layout, exactly as in flat play.

## Streaming from a Windows PC (and setting up another PC)

On a PC the Frame-specific Proton problems (steps 1, 4 and the wrapper) do not exist, and the GPU is far faster, but two Frame fixes still matter: the Halo 3 eye fix (it is about the Frame's lens angles, not the GPU) and the Frame controls. Use the same patched build.

1. **Build** as in Step 2 (or copy `stage\` from a PC that already built it; the laptop then needs no Visual Studio).
2. **Build the layer** on the Frame or any Linux box with [tools/frame-quadfix/halo/build.sh](../../tools/frame-quadfix/halo/build.sh) and copy `out/frame_quadfix.dll` and `out/frame_quadfix.json` to the PC. The same DLL works under Proton and on Windows; it does nothing in any process except `MCC-Win64-Shipping.exe`, so other OpenXR games on the PC are unaffected.
3. **Install** with MCC closed (finds MCC through Steam's library folders):
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\halo-mcc\windows\install-pc.ps1 -ModFiles <stage>\ModFiles -Launcher <stage>\HaloMCCVRLauncher.exe -Layer <folder with frame_quadfix.dll + .json>
   ```
   It copies everything into `<MCC>\Halo_MCC_VR`, keeps or creates `halomccvr.cfg` with `vr_action_mapping = 0` and `y_b_start_chord = 0`, and writes `register-frame-layer.reg` / `unregister-frame-layer.reg` with that machine's path.
4. **Register the layer:** double-click `register-frame-layer.reg` (admin prompt). It has to be the machine-wide `HKEY_LOCAL_MACHINE` key: the mod's launcher runs as administrator and starts MCC elevated, and the OpenXR loader ignores per-user layers in elevated processes.
5. **Frame binding:** with SteamVR closed, run `powershell -ExecutionPolicy Bypass -File <MCC>\Halo_MCC_VR\apply-frame-binding.ps1 -StopSteamVR`, then start SteamVR again. It selects `mcc_frame_binding.json` for `steam.app.976730` in `steamvr.vrsettings` (`frame_controller_CurrentURL_openxr` and the `_250820_` variant), which SteamVR uses from the next launch. SteamVR on Windows has the same `frame_controller` driver, so the file is identical to the Frame's. **Do not use the Frame's "overwrite the generated file and lock it" trick on Windows:** SteamVR there rewrites `steam.app.976730_oculus_touch_N_binding.json` (in `<Steam>\config\openxr`) on every launch, a read-only file fails with `Unable to write OpenXR binding` and `Loading 0 bindings`, and every button goes dead. The script unlocks such a file if an older version locked it.
6. **Settings on a PC:** `resolution_scale` can go to 1.0 or higher; on an NVIDIA RTX card the mod's DLSS option works (keep `nvngx_dlss.dll`). Keep `vr_action_mapping = 0` for the 1:1 layout; manual reload and holsters may work on Windows (the freezes were FEX-specific) but were not tested.
7. **Y + B:** `install-pc.ps1` sets `y_b_start_chord = 0` in `halomccvr.cfg`. With the mod's default (1), pressing Y and B together also pauses, which gets in the way of a 1:1 layout where Y and B are separate game buttons.
8. **Library entry (optional):** a non-Steam shortcut "Halo MCC (VR)" to `<MCC>\Halo_MCC_VR\HaloMCCVRLauncher.exe` with "Include in VR Library" ticked. MCC artwork from Steam's library cache can go in `userdata\<id>\config\grid` under the shortcut's id.

The Steam "Anti-Cheat Disabled" entry does not inject the mod on Windows; always start through `HaloMCCVRLauncher.exe`. Confirmed in the headset with the Frame controls on a Windows PC (RTX 4080 Laptop) streaming to the Frame.

## Tuning and diagnostics (patched build)

- `~/PCVR/HaloMCCVR/world_scale` → `FRAME_WORLD_SCALE`: Halo 3 world units per metre (mod default 0.33, higher = smaller world). With the eye fix the default feels right.
- `~/PCVR/HaloMCCVR/stereo_scale` → `FRAME_STEREO_SCALE`: eye separation only (default 1.0).
- `~/PCVR/HaloMCCVR/tso` = `off` drops FEX's x86 memory-order emulation for a frame or two more; it made Halo CE crash on load, so it stays on by default. (On Windows, set the two `FRAME_*` variables in the environment the launcher starts from.)
- `touch .../Halo_MCC_VR/dump_eyes.flag` makes the mod write `HaloMCCVR-eye0.bmp` and `-eye1.bmp`: exactly what each eye receives.
- `HaloMCCVR.log` gets `FRAME-FLICKER` counters every two seconds; the layer writes `MCC/Binaries/Win64/frame_quadfix.log` (pad presses, accepted and rejected frames, details of rejected ones).

## Check it worked

- The repair script prints a verification table; it wants `builtin=1` and `Aarch64` in `system32`, `Intel 80386` in `syswow64`.
- In `HaloMCCVR.log`: `status: session=focused shouldRender=1`, `M2: submitting native per-eye FOV` in Halo 3, no `FAULT` or `C000001D` lines.
- `frame_quadfix.log`: `layer active (Halo MCC process)`, `suggest /interaction_profiles/oculus/touch_controller: forwarded`, `pad bridge: attach with framepad -> 0`, and no `REJECTED` frames when you open the mod menu.
- `vrserver.txt`: `Successfully loaded binding file '.../steam.app.976730_oculus_touch_0_binding.json'` with `Checking input type ... (/user/hand/left/input/view)`.

Performance on the Frame: Halo 3 runs at roughly 18 to 35 fps (CPU-bound: Halo's main thread at 100% of one core under FEX), CE noticeably faster.

## Status and known issues

- **Never let the EAC path run.** Steam's "Verify integrity" or a reinstall may run the install script again, which re-poisons the prefix. If Play starts bouncing back in three seconds again, run the repair script again.
- Online matchmaking needs EAC and is therefore off. Campaign, custom games and co-op by invite are what you get.
- **Xbox sign-in:** the mod's focus hook starves the sign-in box in VR. Sign in once from the flat entry; the token is then cached in the prefix.
- **Do not leave `PROTON_LOG=1` on.** One session grew `~/steam-976730.log` to 11.7 GB, filled the headset's drive and cut the mod's config file off mid-line. The wrapper clears it unless `MCC_LOG=1`.
- Halo 2, Reach and Halo 4 are not yet tested standalone.
- The x86-64 DXVK copies apply to both entries. Flat mode is a little slower and the first run has heavy shader-compile stutter; it settles.

## Undo

```bash
ssh frame 'rm ~/mcc; cd ~/.local/share/Steam/steamapps/common/"Halo The Master Chief Collection" && rm MCC/Binaries/Win64/{dxgi.dll,d3d11.dll,d3d10core.dll} && rm -r Halo_MCC_VR'
# then clear the Launch Options field. The layer's registry value lives in compatdata/976730/pfx/system.reg.
```

On Windows: double-click `unregister-frame-layer.reg`, delete `<MCC>\Halo_MCC_VR`, and remove the two `frame_controller_*` keys under `steam.app.976730` in `steamvr.vrsettings` with SteamVR closed (or restore `steamvr.vrsettings.bak-halo-frame`).

## Files in this repo

- [repair-mcc-prefix.sh](../../scripts/halo-mcc/repair-mcc-prefix.sh): moves the foreign x86-64/i386 runtime DLLs out of the prefix and restores Proton's copies.
- [mcc](../../scripts/halo-mcc/mcc): launch-option wrapper (flat/VR entries, layer mode, log off, tuning files).
- [patches/](../../scripts/halo-mcc/patches/): the MCCVR source patch (Halo 3 eye fix, weapon flicker fix, tuning variables, diagnostics, menu tidy-up).
- [install_build.sh](../../scripts/halo-mcc/install_build.sh): installs a built DLL and the layer on the Frame.
- [mcc_controls.sh](../../scripts/halo-mcc/mcc_controls.sh): builds and registers the layer in the prefix, writes the binding, sets the essential config.
- [mcc_binding.py](../../scripts/halo-mcc/mcc_binding.py) / [mcc_frame_binding.json](../../scripts/halo-mcc/mcc_frame_binding.json) / [watchbind.sh](../../scripts/halo-mcc/watchbind.sh): the Frame controller layout and the routine that gets SteamVR to use it.
- [windows/install-pc.ps1](../../scripts/halo-mcc/windows/install-pc.ps1) / [windows/apply-frame-binding.ps1](../../scripts/halo-mcc/windows/apply-frame-binding.ps1): the same for a Windows PC streaming to the Frame (the binding is selected in `steamvr.vrsettings`, not locked into SteamVR's generated file).
- [tools/frame-quadfix/halo](../../tools/frame-quadfix/halo/): the Halo build of the OpenXR layer.

## Credits

- MCCVR by moistman42069 and its contributors (MCCVR-Halo-Build on GitHub, MIT). The patch here applies to its public source.
- This repo holds only scripts, patches and source, no game data or binaries. The mod is built from its own repository.
