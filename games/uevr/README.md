# UEVR, the Unreal Engine VR injector

**Status:** Dead end by choice — it worked on the Frame, but the result was not good enough to keep, so everything was removed.

| | |
|---|---|
| Engine / VR API | Unreal Engine games, Direct3D 11 hooked by the injector |
| Route | Proton 11.0 (ARM64) + FEX |
| Diagnosed | 2026-10-06 |

## What it is

UEVR is a generic VR injector for Unreal Engine games. On the Frame it was used with community profiles to run Boltgun, SPRAWL, Phantom Fury and System Shock in VR. The injector's UI is WPF, so each game prefix needs the .NET Desktop Runtime.

## What you see

The games ran in VR. Boltgun under Proton 11.0 (ARM64) hooked Direct3D 11 after a run of "Failed to initialize Framework on DirectX 12" retries. The injector's WPF window crashed later, cosmetically. The games were playable, but the mods were "not quite good enough".

## Why it fails on the Frame

It does not fail. This is a dead end by choice: the VR results were playable but not good enough to keep.

## What was tried

The recipe that worked (2026-10-06, since removed):

1. UEVR nightly (01143 at the time) unpacked to `~/PCVR/UEVR`; profiles from uevr-profiles.com.
2. Per game prefix: .NET Desktop Runtime 6.0.36 x64 installed, because the injector's UI is WPF.
3. A wrapper, `~/PCVR/UEVR/uevr-launch.sh %command%`, that installs .NET if missing and then sets the launch environment so Proton starts the injector alongside the game:

```
PROTON_REMOTE_DEBUG_CMD="<path>/UEVRInjector.exe --attach=<Game>-Win64-Shipping.exe" %command%
```

   It has to be a script because Steam strips backslashes from launch options.

4. Boltgun under Proton 11.0 (ARM64) hooked Direct3D 11 after a run of "Failed to initialize Framework on DirectX 12" retries.

## What would fix it

Nothing is broken. If wanted again: UEVR nightly, .NET 6 Desktop x64 in the game prefix, the `PROTON_REMOTE_DEBUG_CMD` launch option set from a wrapper script, and profiles from uevr-profiles.com.

## State left on the headset

Nothing. `uninstall.sh` cleared the launch options, removed the added pak files, the per-prefix UEVR data and .NET, and deleted `~/PCVR/UEVR`.

## Credits

- UEVR (the Unreal Engine VR injector) and the community profiles from uevr-profiles.com.
