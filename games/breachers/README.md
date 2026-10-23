# Breachers

**Status:** Dead end — anti-cheat. Two walls, one behind the other: Steam's launch target is a .NET launcher that cannot run under Proton on the Frame, and past it the game's own startup integrity check (part of its Easy Anti-Cheat integration) fails and the game exits ten seconds in, with or without the anti-cheat bootstrapper.

| | |
|---|---|
| Steam app | 1922010, 13.4 GB on disk |
| Engine / VR API | Unity IL2CPP, OpenVR (`-xrloader OpenVR`) |
| Anti-cheat | Easy Anti-Cheat (EOS) with integrity certificates; Valve's Deck test stops at "SteamOS does not support VR" |
| Route | Proton 11.0 (ARM64) + FEX, Steam's default compat tool |
| Diagnosed | 2026-10-09, six test launches |

## What it is

Breachers is a Unity IL2CPP VR game that talks to SteamVR through OpenVR. Steam runs `Breachers.exe -xrloader OpenVR`. That file is a 48 KB .NET Framework 4 application ("BreachersLauncher") which installs Easy Anti-Cheat if needed and then starts `GameLauncher.exe`, the EOS anti-cheat bootstrapper, which in turn starts the real game, `Breachers_Internal.exe`.

## What you see

Press Play; four seconds later the button is back to Play. Every attempt since 29 September looked the same.

## Why it fails on the Frame

### 1. The launcher is a .NET program

- Proton on the Frame ships no .NET runtime and no Wine Mono, so the launcher dies at once:

```
err:mscoree:load_mono Could not load Mono into this process
```

- That is the four-second exit.
- The install script does nothing harmful here (it only registers firewall entries), and the prefix's system DLLs stay Proton's own, unlike Halo MCC.

### 2. The game refuses to start

- A wrapper that skips the launcher and runs `Breachers_Internal.exe -xrloader OpenVR` directly gets the Unity player going: it starts the crash handler, reads `boot.config`, creates `Player.log`, loads `UnityPlayer.dll`, `baselib.dll` and `GameAssembly.dll`.
- `GameAssembly.dll` imports WINTRUST, and 0.2 seconds after it loads the main thread opens `GameAssembly.dll` itself for reading. Ten seconds of reading and hashing later the process raises a system hard-error dialog and exits:

```
fixme:ntdll:NtRaiseHardError 0x50000018 4 0x3 ...: stub
```

- `NtRaiseHardError` is a stub in Wine, so the message never appears. Unity never logged a line, and no crash dump was written.
- Two deliberate single-step exceptions earlier in the same run are the usual fingerprint of anti-tamper code checking for a debugger.
- Starting the game through its EOS bootstrapper instead (`GameLauncher.exe -xrloader OpenVR`) runs the identical sequence to the identical hard error. Proton's anti-cheat runtime never engages, because the Linux side of EAC does not exist for ARM64 Proton.
- The `EasyAntiCheat/Certificates` folder in the install is what EAC's integrity feature uses to validate the game's binaries, and that validation is what fails here.

## What was tried

- Stock launch: four-second .NET failure.
- Wrapper to `Breachers_Internal.exe` directly: ten-second hard error.
- Wrapper to `GameLauncher.exe` (the EAC bootstrapper): same hard error.
- Relay, window, file and wintrust tracing to attribute the exit. No signature-verification API is ever called and no window is created; the exit follows the game reading its own code module.

## What would fix it

- **The publisher only:** enable EAC's Linux support, or build without the startup integrity check for platforms where it cannot pass.
- Nothing on the headset can satisfy a check that compares the running game against what it expects on Windows.

## State left on the headset

Launch options are empty, the compat tool is Steam's default, and the test wrappers were removed. The 13.4 GB install is still on the internal drive; uninstall it from the library if you want the space back.
