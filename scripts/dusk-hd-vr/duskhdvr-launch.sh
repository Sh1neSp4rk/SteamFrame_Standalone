#!/bin/bash
# Steam launch wrapper for Dusk_HD_VR on the Frame: starts DLC/DUSK HD/Dusk.exe instead of classic DUSK,
# loads BepInEx (winhttp) and framepad's xinput1_3 (the virtual pad the mod feeds). Log: last-launch.txt
# It also starts uinput_pad, an idle virtual Xbox 360 controller on the Linux side: without some real game
# controller device Unity never creates a joystick, so DUSK ignored the pad framepad serves. It exits
# with this launch (the wrapper's PID stays the game's launcher after exec).
# Debug run: touch ~/PCVR/DuskHDVR/debug for ~/steam-519860.log (PROTON_LOG). With ~/PCVR/DuskHDVR/rawlist
# present, also runs rawlist.exe in the prefix (writes C:\users\steamuser\rawlist.txt after 40 s).
D="$HOME/PCVR/DuskHDVR"
export WINEDLLOVERRIDES="winhttp=n,b;xinput1_3=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
if [ -e "$D/debug" ]; then
  export PROTON_LOG=1 WINEDEBUG="+loaddll"
fi
if [ -e "$D/rawlist" ]; then
  # Proton shlex-splits this and needs an absolute first word.
  export PROTON_REMOTE_DEBUG_CMD="$D/framepad/out/rawlist.exe"
fi
SHM="$HOME/.local/share/Steam/steamapps/compatdata/519860/pfx/drive_c/users/steamuser/framepad.shm"
[ -x "$D/framepad/out/uinput_pad" ] && setsid "$D/framepad/out/uinput_pad" $$ "$SHM" > "$D/uinput_pad.log" 2>&1 < /dev/null &
args=("${@/common\/Dusk\/Dusk.exe/common/Dusk/DLC/DUSK HD/Dusk.exe}")
echo "$(date) ${args[*]}" > "$D/last-launch.txt"
exec "${args[@]}"
