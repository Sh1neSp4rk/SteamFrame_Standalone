# SteamFrame_Standalone

PC VR games and mods running **standalone on the Steam Frame**: no PC, no streaming, the headset doing all the work. This repository is the home for everything learned getting about thirty titles through Proton, FEX and SteamVR on the Frame's ARM64 SteamOS, or rebuilt natively when that chain could not carry them.

- **Guide site:** <https://sh1nesp4rk.github.io/SteamFrame_Standalone/> (the same content as [docs/index.html](docs/index.html))
- **Per-game write-ups:** [games/](games/) (what the game is, what broke, the fix, the exact commands, status)
- **Scripts and patches:** [scripts/](scripts/) (indexed in [scripts/README.md](scripts/README.md))
- **Tools:** [tools/frame-quadfix](tools/frame-quadfix/), an OpenXR API layer for Proton games on the Frame (per-eye quad layers, single interaction profile); [tools/far-cry-ovrshim](tools/far-cry-ovrshim/), a proxy `openvr_api.dll` plus a native overlay helper for 32-bit OpenVR games whose overlays Proton cannot pass; and [scripts/common/vr_audit2.py](scripts/common/vr_audit2.py), which audits which VR shortcuts depend on which Steam game installs
- **For platform and mod developers:** [KNOWN-ISSUES.md](KNOWN-ISSUES.md) (what fails in SteamVR, Proton and the zink driver on the Frame, and why)
- **Controller layout:** [FRAME-LAYOUT.md](FRAME-LAYOUT.md) (one layout for every mod, and each game's deviations)

Nothing here modifies SteamOS. Every fix is a launch option, a script in the home folder, or a file inside a game folder or its Proton prefix. No game data, mod binaries or game binaries are included.

## How the Frame runs PC games

A Frame-native game from the Steam store is an Android APK. Everything else is the Windows x86-64 build, started like this:

```
Steam client (ARM64)
  -> steam-launch-wrapper -> reaper
    -> Steam Linux Runtime (pressure-vessel container)
      -> FEX  (translates x86-64 code to ARM64 on the fly)
        -> Proton 11.0 (ARM64) or Proton Experimental (ARM64)
          -> Wine, with DXVK turning Direct3D into Vulkan on the Adreno 750 (Turnip driver)
            -> the game's Windows .exe
VR:  OpenVR games  -> Proton's vrclient bridge -> SteamVR on the headset
     OpenXR games  -> wineopenxr -> SteamVR's OpenXR runtime
```

What that chain can and cannot carry, as found on the test headset (SteamOS 0.4.5, SteamVR 2.18.2):

| Game type | Standalone on the Frame? | Why |
|---|---|---|
| Direct3D 11/12 or Vulkan game, **OpenVR** | Yes, under Proton | Proton's vrclient bridge is complete for these |
| Direct3D 11/12 or Vulkan game, **OpenXR** | Yes, under Proton | wineopenxr bridges D3D11, D3D12 and Vulkan sessions |
| **OpenGL** game, **OpenVR** | Yes, under Proton | Eye textures submit fine (GZDoom VR). One exception: `IVRCompositor::SetSkyboxOverride` with OpenGL textures asserts inside the ARM64 bridge (Doom 3 BFG VR, Half-Life: VR Mod) |
| **OpenGL** game, **OpenXR** | **No** under Proton | `wine_xrCreateSession Unhandled graphics binding type: 1000023000`. wineopenxr has no OpenGL binding. Build it natively instead |
| Sideloaded x86-64 OpenXR build | **No** | The container only imports SteamVR's ARM64 OpenXR runtime, so VR never attaches |
| Native ARM64 Linux build, OpenXR or OpenVR | Yes | Talks to SteamVR's ARM64 libraries directly; OpenGL goes through zink on Turnip. The toolchain is on the headset (gcc 15, clang 19, cmake, ninja, SDL2, OpenXR headers, OpenVR) |
| Easy Anti-Cheat games | **No** | EAC's Linux module only exists for publishers who enabled it, and it does not run under FEX either way. Offline modes only |
| Unity VR mods using a virtual gamepad driver (ViGEmBus) | Needs a stand-in | Proton cannot load the Windows kernel driver; DUSK HD VR got a shared-memory replacement plus a Linux uinput pad |
| 32-bit games | Mostly | 32-bit OpenXR on D3D11 works through Proton Experimental's i386 wineopenxr (F.E.A.R. VR, Red Faction VR); Proton's i386 vrclient bridge connects (BioShock VR), but that game never presented a frame; Deus Ex HR VR works through a 64-bit helper process |

Failure patterns seen more than once:

- A launcher runs before the game and stops on a dialog nobody can see in VR (Contractors, Halo MCC, FighterZ). Fix: a wrapper script that swaps the executable Steam starts.
- Steam's install script overwrites Proton's ARM64 runtime DLLs with Microsoft x86-64 ones and the prefix cannot boot (Halo MCC). Fix: restore Proton's copies.
- A mod's x86-64 DLL cannot load an ARM64 runtime DLL from the prefix (Borderlands VR, Deus Ex HR VR, Unreal Revived VR). Fix: an x86-64 copy beside the executable.
- A VR mod that patches Direct3D in memory crashes on ARM64 DXVK (Halo MCC VR). Fix: Proton's x86-64 DXVK beside the exe.
- Strict OpenXR: SteamVR on the Frame refuses an instance that enables `XR_FB_foveation` without `XR_FB_swapchain_update_state` (Unity OpenXR 1.14 games). Fix: a 70 KB implicit API layer.
- A game below about 20 fps shows a black world with its menus intact: SteamVR blanks it. Lower the resolution.

## Status

| Game | Route | Status | Notes |
|---|---|---|---|
| [GZDoom VR: Doom, Heretic, Hexen](games/gzdoom-vr/) | Proton, OpenVR | Working | Non-Steam shortcuts; grip threshold fix for Heretic and Hexen |
| [Quake (Team Beef port)](games/quake-team-beef/) | Native, OpenXR | Working | Standard layout confirmed |
| [Quake II VR](games/quake2-vr/) | Native, OpenXR | Working | glFinish for the right eye; MSAA 2 |
| [Quake III VR](games/quake3-vr/) | Native, OpenXR | Working | Port defaults |
| [Quake VR: Unleashed](games/quakevr-unleashed/) | Native, OpenXR | Working, heavy | Three zink fixes; resolution is the only performance lever |
| [Return to Castle Wolfenstein VR](games/rtcw-vr/) | Native, OpenXR | Working | Needs RealRTCW's `realrtcw5.0` branch |
| [Doom 3 BFG VR](games/doom3-bfg-vr/) | Native, OpenVR | Working | Rebuilt natively around one skybox call |
| [Selaco VR](games/selaco-vr/) | Native, OpenVR | Working | Windows build dies under FEX; legacy-input binding |
| [Aliens versus Predator VR](games/avp-vr/) | Native, OpenXR | Working | First native port; keyboard patch |
| [Counter-Strike VR](games/counter-strike-vr/) | Native, OpenXR | Working | Team Beef's Quest port on Xash3D; menu cylinder replaced by a quad; bumper, view and d-pad actions added |
| [Jedi Academy VR and Jedi Outcast VR](games/jedi-knight-vr/) | Native, Vulkan + OpenXR | Working | JKXRL built for ARM64; multi-draw indirect off and per-game tiling mode for Turnip |
| [DUSK HD VR](games/dusk-hd-vr/) | Proton, OpenVR | Working | Virtual pad stand-in, stripped Harmony patches, uinput pad |
| [F.E.A.R. VR](games/fear-vr/) | Proton, OpenXR | Working | Proton verb swap for the launcher handoff |
| [Left 4 Dead 2 VR](games/l4d2-vr/) | Proton, OpenVR | Working | Mod DLL patched for FEX load times |
| [Portal 2 VR](games/portal2-vr/) | Proton, OpenVR | Working, controls unconfirmed | Shares the L4D2 binding |
| [Bendy VR](games/bendy-vr/) | Proton, OpenVR | Working | Needs the `release-1.5` Steam branch |
| [Red Faction VR](games/red-faction-vr/) | Proton, OpenXR (32-bit) | Working | Mod patched and rebuilt for the standard layout; single-profile binding rule |
| [Hollow Knight VR](games/hollow-knight-vr/) | Proton, OpenVR | Working | DUSK recipe plus a plugin for pause and the d-pad |
| [Circuit Superstars VR](games/circuit-superstars-vr/) | Proton, OpenVR | Working | Gamepad-only mod; a plugin drives a virtual pad from the SteamVR actions |
| [Unreal Revived VR](games/unreal-revived-vr/) | Proton, OpenXR (D3D12) | Working | Installed on a PC and copied in; Microsoft d3dcompiler; the frame_quadfix OpenXR layer for the menus |
| [Far Cry VR](games/far-cry-vr/) | Proton, OpenVR (32-bit) | Working | Proxy openvr_api.dll plus a native overlay helper for the HUD and menus |
| [Contractors VR](games/contractors/) | Proton, OpenVR | Working | Skip Unreal's bootstrapper |
| [Halo: MCC (flat + VR mod)](games/halo-mcc/) | Proton | Working | Prefix repair, wrapper, x86-64 DXVK; patched MCCVR (Halo 3 stereo and flicker fixes), Halo layer build of frame_quadfix, 1:1 Frame controls; same build streams from a Windows PC |
| [Metal: Hellsinger VR](games/metal-hellsinger-vr/) | Proton, OpenXR | Working | One missing DLL (`mfc140u.dll`) |
| [Snapshot VR](games/snapshot-vr/) | Proton, OpenXR | Working | Implicit OpenXR API layer |
| [XCOM 2](games/xcom2/) | Proton (flat) | Working | Controller layout only |
| [BioShock Remastered VR](games/bioshock-vr/) | Proton (32-bit) | Parked | OpenVR connects, no frame ever presented |
| [Borderlands GOTY VR](games/borderlands-vr/) | Proton | Parked | Needs a mod-side change (square-display spoof) |
| [Dragon Ball FighterZ](games/dragon-ball-fighterz/) | Proton | Dead end | Easy Anti-Cheat |
| [Breachers](games/breachers/) | Proton | Dead end | .NET launcher, then EAC integrity check |
| [Half-Life: VR Mod](games/half-life-vr-mod/) | Proton | Dead end, for now | Skybox assertion on Proton 11; mod VR shutdown on Experimental |
| [UEVR injector](games/uevr/) | Proton | Dead end, by choice | Worked; result not kept |
| [Resident Evil 4 (2023) VR](games/re4-remake-vr/) | Streamed from a Windows PC, OpenVR | Working (streamed) | RE4VR; a SteamVR binding plus a REFramework Lua script give the Frame the flat Xbox layout 1:1 |
| [Titanfall 2 VR](games/titanfall2-vr/) | Streamed only | Not standalone | Needs the mod's installer window on a PC |
| [Tribes 2 VR](games/tribes2-vr/) | Proton (32-bit) | Dead end | Mod runs; TribesNext login crashes under FEX, 2D shell cannot fuse on the Frame's lenses |
| [Deus Ex: HR VR](games/deus-ex-hr-vr/) | Proton, OpenXR | Removed | Worked at 18 to 36 fps reprojected with eleven inputs; not worth keeping. Lessons recorded |

## Controller layout

Every VR mod ships bindings for Quest or Index controllers and puts jump, crouch and the menu somewhere different. All the games here use one base layout and deviate only where a game must. The full layout and every game's deviations are in [FRAME-LAYOUT.md](FRAME-LAYOUT.md); the short version:

| Input | Action |
|---|---|
| Right trigger | Primary fire |
| Left trigger | Secondary (alt-fire, aim, shove; crouch in the Quake games) |
| Left bumper | Jump |
| Right bumper | Use / interact |
| A | Crouch |
| B | Reload |
| X | Utility (flashlight, melee, grenade) |
| Left stick | Move (head-oriented where possible); click = sprint |
| Right stick | Snap turn; up/down past 75% = weapons; click = recenter |
| Menu | Pause |
| View | Map / scoreboard / inventory |
| Grips | Never core actions; 80% squeeze to press, release below 70% |

Stick deadzones are 10% for move and turn and 75% when a stick direction acts as a button. The left d-pad is for tap actions only: the Frame driver reports a held click as short pulses that stop after about a second (see KNOWN-ISSUES). How a layout is applied depends on how the game talks to SteamVR (OpenXR suggested bindings, legacy OpenVR input, an action manifest, or the mod's own config); the guide's "Controller layout" page covers each case. Two things that cost evenings: `vrcmd --set-settings-string` neither persists nor applies a binding on the Frame (write `steamvr.vrsettings` with [vrsettings_bind.py](scripts/common/vrsettings_bind.py) and restart the VR session), and SteamVR's simulated Oculus Touch profile drops the axis3/axis4 legacy ids.

## Using this repository on a Frame

1. Enable Developer Mode on the headset (Steam Settings > System), set a user password, and `ssh steamos@frame.local` from a PC. The guide's "Toolbox" page has the details.
2. Scripts assume the layout used on the test headset: `~/PCVR/<Port>/` for a port's source and build, `~/PCVR/<Port>-game/` for the playable folder, `~/PCVR/bin/` for the shared helpers. Copy `scripts/common/*` to `~/PCVR/bin/` and a game's scripts to the folder its README names.
3. Read the game's README before running anything. Build scripts clone and compile on the headset; install scripts change files inside a Steam game folder or prefix and say how to undo it.
4. Never `pkill -9 vrserver`. Restart the whole VR session instead with `systemctl --user restart gamescope-session.target`, which drops whoever is wearing the headset.

## Contributing

Issues and pull requests are welcome, especially:

- A game or mod that works on the Frame with a recipe not listed here, or a fix for a parked title. Add `games/<slug>/README.md` using the existing files as the template, and put scripts under `scripts/<slug>/` with a header comment saying what each one does.
- Corrections to the findings in [KNOWN-ISSUES.md](KNOWN-ISSUES.md), with the log lines that show it.
- Controller bindings that follow [FRAME-LAYOUT.md](FRAME-LAYOUT.md), with the game's deviations listed.

Please keep personal data out (no Steam account ids, user names or email addresses in logs or paths), and never commit game data, mod archives or built binaries. Patches to GPL projects stay under that project's license; say which project a patch belongs to.

## License

The documentation, the guide site and the original scripts in this repository are released under the [MIT License](LICENSE).

The ports and mods this repository builds on are separate projects with their own licenses, several of them GPL (GZDoom and SelacoVR, DarkPlaces and the Team Beef Quake ports, Yamagi Quake II, ioquake3, ioRTCW/RealRTCW, RBDoom3BFG, the AvP source, Xash3D FWGS under CSVR, OpenJK under JKXRL). Only patches and build or binding scripts for them are included here, and the patch scripts that carry replacement source fragments are offered under the same license as the code they patch. No game data, mod binaries or built binaries are distributed. Game data must come from your own copies of the games on Steam.

## Credits

- [Team Beef](https://github.com/Team-Beef-Studios) for QuakeQuest, Quake2Quest, RealRTCWXR, CSVR and BendyVR, and GameOrDie007 for the PC VR ports of the Quake games; the Xash3D FWGS, ReGameDLL_CS and YaPB projects under CSVR; Patola for JKXRL (the Linux fork of Team Beef's JKXR) and the OpenJK project under it
- [emawind84/SelacoVR](https://github.com/emawind84/SelacoVR), [hh79/gzdoomvr](https://github.com/hh79/gzdoomvr) and jantyka's gzdoomvr lineage for the Doom-engine VR builds
- [RippeR37/q3vr](https://github.com/RippeR37/q3vr), [vittorioromeo/quakevr](https://github.com/vittorioromeo/quakevr), [NPi2Loup/DOOM-3-BFG-VR](https://github.com/NPi2Loup/DOOM-3-BFG-VR), [Bassquake/Aliens-Versus-Predator-VR](https://github.com/Bassquake/Aliens-Versus-Predator-VR)
- sd805 (l4d2vr), Spencer0187 (portal2vr-roomscale), Astienth (Dusk_HD_VR), thefreemike31 (fear-vr), farmerarmor (DeusExHRVR), moistman42069 (MCCVR), mohamad-balouza (bioshock-vr), Mastersellz (BL1GOTYVR), 7empest (Half-Life: VR Mod), praydog (UEVR), CircuitLord (Titanfall 2 VR), Bruhlitz (Tribes2VRmod), kwstasg (Unreal Revived) and OldUnreal, fholger (farcry_vrmod), Cactus VR Studios (alpinefactionVR, on GooberRF's Alpine Faction), Astienth (Circuit_Superstars_VR, UnityVR_Bepinex), the Hollow Knight VR Enhanced authors, Nefarius (ViGEm client)
- Valve for OpenVR, SteamVR and Proton; the FEX, DXVK, Mesa (zink, Turnip) and OpenXR projects
- saphid's Frame Control, whose Steam shortcut code [steam_shortcuts.py](scripts/common/steam_shortcuts.py) is adapted from (MIT)
