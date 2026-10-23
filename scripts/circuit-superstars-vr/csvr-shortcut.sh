#!/bin/bash
# "Circuit Superstars VR" shortcut wrapper: circuit-superstars.exe in the game's (1097130) Proton prefix with BepInEx's
# winhttp.dll doorstop enabled (the library entry launches without the override = flat game, mod dormant).
# touch ~/PCVR/CircuitSuperstarsVR/debug for a Proton log; env.test is sourced if present.
D="$HOME/PCVR/CircuitSuperstarsVR"
export STEAM_COMPAT_DATA_PATH="$HOME/.local/share/Steam/steamapps/compatdata/1097130"
export WINEDLLOVERRIDES="winhttp=n,b;xinput1_3=n,b;xinput1_4=n,b;xinput9_1_0=n,b;xinput1_2=n,b;xinput1_1=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
# framepad: the plugin's virtual Xbox pad -> shared memory -> an idle Linux uinput pad the game can see (exits with the launch)
SHM="$STEAM_COMPAT_DATA_PATH/pfx/drive_c/users/steamuser/framepad.shm"
UP="$HOME/PCVR/DuskHDVR/framepad/out/uinput_pad"
[ -x "$UP" ] && setsid "$UP" $$ "$SHM" > "$D/uinput_pad.log" 2>&1 < /dev/null &

[ -f "$D/env.test" ] && source "$D/env.test"
[ -e "$D/debug" ] && export PROTON_LOG=1 PROTON_LOG_DIR="$D/logs" WINEDEBUG="${WINEDEBUG:-+loaddll}"
mkdir -p "$D/logs"; echo "$(date) args: $*" >> "$D/last-launch.txt"
exec "$@"
