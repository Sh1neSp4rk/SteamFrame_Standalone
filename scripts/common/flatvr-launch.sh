#!/bin/bash
# Flat-by-default / VR-on-request Steam launch wrapper for modded games on the Steam Frame.
# Launch options (library entry):  /home/steamos/PCVR/bin/flatvr-launch.sh <game> %command%
# The "<Game> VR" non-Steam shortcut runs:  steam -applaunch <appid> -frame-vr
# Steam appends -frame-vr to the command line; without it the game launches FLAT (mod off).
# Log: ~/PCVR/modes/<game>.log
game="$1"; shift
mkdir -p "$HOME/PCVR/modes"
LOG="$HOME/PCVR/modes/$game.log"
vr=0; args=()
for a in "$@"; do [ "$a" = -frame-vr ] && vr=1 || args+=("$a"); done
echo "$(date '+%F %T') game=$game vr=$vr" > "$LOG"

case "$game" in
  dusk)   # VR: DUSK HD + Dusk_HD_VR via its own wrapper; flat: classic DUSK, no BepInEx
    [ $vr = 1 ] && exec "$HOME/PCVR/DuskHDVR/duskhdvr-launch.sh" "${args[@]}"
    exec "${args[@]}" ;;
  l4d2)   # VR: the mod's d3d9.dll on the DX9 renderer; flat: the game's own Vulkan renderer never loads it
    if [ $vr = 1 ]; then
      export WINEDLLOVERRIDES="d3d9=n,b"
      exec "${args[@]}" -insecure -dx9 -window -w 1280 -h 720 +mat_motion_blur_percent_of_screen_max 0 +crosshair 0 \
           +mat_queue_mode 0 +mat_vsync 0 +mat_antialias 0 +mat_grain_scale_override 0
    fi
    exec "${args[@]}" ;;
  portal2)  # same switch as the mod's Enable-Disable_vr_mod_SWITCHER.cmd (renames two files)
    G="$HOME/.local/share/Steam/steamapps/common/Portal 2"
    sw() { [ -e "$G/$1" ] && mv -f "$G/$1" "$G/$2"; }
    if [ $vr = 1 ]; then
      sw "bin/.openvr_api.dll" "bin/openvr_api.dll"; sw "portal2_dlc3/.pak01_dir.vpk" "portal2_dlc3/pak01_dir.vpk"
      export WINEDLLOVERRIDES="d3d9=n,b"
      exec "${args[@]}" -insecure -dx9 -window -novid +mat_motion_blur_percent_of_screen_max 0 +mat_queue_mode 0 \
           +mat_vsync 0 +mat_antialias 0 +mat_grain_scale_override 0 +snd_surround_speakers 5
    fi
    sw "bin/openvr_api.dll" "bin/.openvr_api.dll"; sw "portal2_dlc3/pak01_dir.vpk" "portal2_dlc3/.pak01_dir.vpk"
    exec "${args[@]}" -insecure -novid ;;   # the mod's engine binaries stay in place: keep VAC off
  bendy)  # VR: BepInEx (winhttp proxy) loads BendyVR; flat: Wine's builtin winhttp, no BepInEx
    [ $vr = 1 ] && export WINEDLLOVERRIDES="winhttp=n,b"
    exec "${args[@]}" ;;
  farcry)  # VR: what the mod's FarCryVR.exe does (Bin32\FarCry.exe -MOD:CryVR + DXVK env) with its own d3d9.dll (DXVK
           # fork that starts OpenVR) and dsound.dll (DSOAL) forced native; flat: Proton's builtin d3d9/dsound, no mod
    if [ $vr = 1 ]; then
      export DXVK_LOG_LEVEL=none DXVK_ASYNC=0 DXVK_GPLASYNCCACHE=0 DXVK_STARTOPENVR=1 WINEDLLOVERRIDES="d3d9=n,b;dsound=n,b;msvcp140=n,b;vcruntime140=n,b;concrt140=n,b"
      [ -f "$HOME/PCVR/FarCryVR/env.test" ] && source "$HOME/PCVR/FarCryVR/env.test"
      [ -e "$HOME/PCVR/FarCryVR/debug" ] && export PROTON_LOG=1 PROTON_LOG_DIR="$HOME/PCVR/FarCryVR/logs" WINEDEBUG="${WINEDEBUG:-+loaddll}"
      # HUD/menu overlays: ovrshim hands frames to this native helper (Proton's 32-bit OpenVR bridge can't)
    rm -f /tmp/farcryvr_bridge_*.shm /tmp/farcryvr_hud_*.bmp
    "$HOME/PCVR/FarCryVR/ovrshim/hudbridge" $$ > "$HOME/PCVR/FarCryVR/hudbridge.log" 2>&1 &
    exec "${args[@]}" -MOD:CryVR
    fi
    exec "${args[@]}" ;;
  *) echo "unknown game $game" >> "$LOG"; exec "${args[@]}" ;;
esac
