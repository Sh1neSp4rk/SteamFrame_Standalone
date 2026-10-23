#!/bin/bash
# Launch "Circuit Superstars VR" through Steam, wait, report. usage: cs_launch.sh [seconds]
D=~/PCVR/CircuitSuperstarsVR; G=~/.local/share/Steam/steamapps/common/"Circuit Superstars"; L=~/.local/share/Steam/logs
id=$(cat $D/appid.txt); gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id)
python3 ~/PCVR/bin/steam_shortcuts.py stop $id >/dev/null 2>&1; pkill -f '[c]ircuit-superstars.exe' 2>/dev/null; sleep 2
rm -f $D/logs/*.log "$G/BepInEx/LogOutput.log"
(steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
n=${1:-90}; for ((t=15; t<=n; t+=15)); do sleep 15; echo "t=${t}s: $(pgrep -f -c '[c]ircuit-superstars.exe') proc(s)"; done
echo "--- BepInEx log"; grep -v -E '^\s*$' "$G/BepInEx/LogOutput.log" 2>/dev/null | grep -i -E 'Error|Warn|UnityVR|OpenXR|OpenVR|SteamVR|XR|loaded|Plugin|Exception|camera' | head -40 | cut -c1-180
echo "--- player log"; P=~/.local/share/Steam/steamapps/compatdata/1097130/pfx/drive_c/users/steamuser/AppData/LocalLow; f=$(find $P -iname 'Player.log' 2>/dev/null | head -1); [ -n "$f" ] && grep -i -E 'XR|OpenVR|OpenXR|SteamVR|error|exception|rewired|controller|joystick' "$f" | head -20 | cut -c1-180
echo "--- vrserver"; grep -a -i -E 'circuit' $L/vrserver.txt | tail -4 | cut -c1-180
echo "--- proton log err"; f=$(ls -t $D/logs/*.log 2>/dev/null | head -1); [ -n "$f" ] && grep -a -i -E 'winhttp|wineopenxr|vrclient|err:|unhandled' "$f" | grep -v -E 'fixme|steamclient|winebth' | tail -12 | cut -c1-200
