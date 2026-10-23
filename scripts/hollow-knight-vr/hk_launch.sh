#!/bin/bash
# Launch "Hollow Knight VR" through Steam, wait, report. usage: hk_launch.sh [seconds]
D=~/PCVR/HollowKnightVR; G=~/.local/share/Steam/steamapps/common/"Hollow Knight"; L=~/.local/share/Steam/logs
id=$(cat $D/appid.txt); gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id)
python3 ~/PCVR/bin/steam_shortcuts.py stop $id >/dev/null 2>&1; sleep 2
rm -f $D/logs/*.log "$G/BepInEx/LogOutput.log"
(steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
n=${1:-90}; for ((t=15; t<=n; t+=15)); do sleep 15; echo "t=${t}s: $(pgrep -f -c '[h]ollow_knight.exe') proc(s)"; done
echo "--- BepInEx log"; grep -v -E '^\s*$' "$G/BepInEx/LogOutput.log" 2>/dev/null | grep -i -E 'Error|Warn|UnityVR|OpenXR|OpenVR|SteamVR|XR|loaded|Plugin|Exception' | head -40 | cut -c1-180
echo "--- player log"; P=~/.local/share/Steam/steamapps/compatdata/367520/pfx/drive_c/users/steamuser/AppData/LocalLow; f=$(find $P -iname 'Player.log' 2>/dev/null | head -1); [ -n "$f" ] && grep -i -E 'XR|OpenVR|OpenXR|SteamVR|error|exception' "$f" | head -20 | cut -c1-180
echo "--- vrserver"; grep -a -i -E 'hollow' $L/vrserver.txt | tail -4 | cut -c1-180
echo "--- proton log err"; f=$(ls -t $D/logs/*.log 2>/dev/null | head -1); [ -n "$f" ] && grep -a -i -E 'winhttp|wineopenxr|vrclient|err:|unhandled' "$f" | grep -v -E 'fixme|steamclient|winebth' | tail -12 | cut -c1-200
