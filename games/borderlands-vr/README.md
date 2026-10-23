# Borderlands GOTY Enhanced VR

**Status:** Parked. A 64-bit Direct3D 11 mod with in-process OpenXR, loaded through a dxgi.dll proxy. Two of three Frame problems were solved; the third needs a change in the mod. Uninstalled by the user on 2026-10-21.

| | |
|---|---|
| Steam app | Borderlands GOTY Enhanced (Gearbox `Launcher.exe` then `BorderlandsGOTY.exe`) |
| Engine / VR API | 64-bit Direct3D 11; the mod does OpenXR in-process |
| Mod | BL1GOTYVR V0.5.7.3 by Mastersellz, https://github.com/Mastersellz/BL1GOTYVR |
| Route | Proton + FEX (DXVK for Direct3D 11) |
| Fix | two of three fixed; the swapchain failure is open |
| Date | diagnosed 2026-10-21 |

## What it is

BL1GOTYVR turns Borderlands GOTY Enhanced into a VR game by proxying `dxgi.dll`, hooking Direct3D 11 and running its own OpenXR session inside the game process. Steam launches Gearbox's `Launcher.exe`; a wrapper (`bl1vr-launch.sh`) swapped it for `BorderlandsGOTY.exe`.

## What you see

With the stock mod the game runs flat and the mod never loads. With the two Frame fixes below the mod loads, hooks Direct3D 11, and then the game crashes when its swapchain is created.

## What broke on the Frame

- **Proton prefix: the wrong `vcruntime140_1.dll`.** The prefix's `vcruntime140_1.dll` is ARM64, so the x86-64 `BL1GOTYVR.dll` could not load. Solved: an x86-64 copy beside the exe (for example from `compatdata/2672470/pfx/drive_c/windows/system32/vcruntime140_1.dll`).
- **The mod's dxgi proxy versus DXVK.** The upstream proxy refuses to load unless all 20 Windows dxgi exports resolve, and DXVK has five. It unloaded itself and the game's D3D11 probe failed (`D3D11 is not supported ... fallback`). Solved: `frame_dxgi_proxy`, a C port that forwards only `CreateDXGIFactory*`, built with clang and lld-link (no Windows SDK). With it, the mod loads and installs its D3D11 hooks.
- **DXVK swapchain: still broken.** The game's swapchain then fails in DXVK and the mod crashes using it:

```
Failed to create Vulkan surface, VK_ERROR_OUT_OF_HOST_MEMORY
```

  The crash is at `BL1GOTYVR.dll+0x8A15`. Same with and without a nested gamescope. Suspected: the mod's square-display spoof (it hooks `GetClientRect` / `GetMonitorInfo` / `EnumDisplaySettings`) or its hidden 100x100 probe window. The spoof cannot be disabled from the ini (non-square sizes get replaced by 2048x2048). Needs a mod-side change.

## What was tried

1. Installed the mod with its `install.sh`; wrapped the launch so `BorderlandsGOTY.exe` starts instead of `Launcher.exe`.
2. Replaced the ARM64 `vcruntime140_1.dll` with an x86-64 copy beside the exe, which let the mod DLL load.
3. Wrote `frame_dxgi_proxy` to satisfy the mod's export check against DXVK's five exports, which let the mod hook Direct3D 11.
4. Tried with and without a nested gamescope; the Vulkan surface creation failed the same way.
5. Removed the mod from the game folder, cleared the launch option, set `ResX`/`ResY` back to 1920x1080. The user then uninstalled the game; `~/PCVR/BL1GOTYVR` (archive, extracted mod, `frame_dxgi_proxy`, `bl1vr-launch.sh`, `last-run-logs/`) was removed with it.

## Exact commands

Nothing from this attempt is in the repo as a script; the `frame_dxgi_proxy` source and `bl1vr-launch.sh` were removed with the game folder.

## Check it worked

It did not reach VR. A working run would create the Vulkan surface after the mod's D3D11 hooks install, with no `VK_ERROR_OUT_OF_HOST_MEMORY` in the DXVK log.

## Status and known issues

Parked. What would fix it: a mod build whose square-display spoof and probe window can be switched off, so DXVK gets a normal window to create its surface on.

Retry recipe: rerun the mod's `install.sh`, copy an x86-64 `vcruntime140_1.dll` and `frame_dxgi_proxy/out/dxgi.dll` next to `BorderlandsGOTY.exe`, and launch through a wrapper that swaps `Launcher.exe` for `BorderlandsGOTY.exe`.

## Undo

Already undone: mod removed from the game folder, launch option cleared, `ResX`/`ResY` back to 1920x1080, game uninstalled.

## Credits

- BL1GOTYVR V0.5.7.3 by Mastersellz.
- This repo holds only scripts, no game data or binaries.
