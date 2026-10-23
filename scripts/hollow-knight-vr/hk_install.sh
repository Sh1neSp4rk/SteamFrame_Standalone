#!/bin/bash
# Install HollowKnight_VREnhanced into the Steam game folder, add the "Hollow Knight VR" shortcut (BepInEx only loads
# through the shortcut's winhttp override, so the library entry stays flat), launch once with logs.
set -e
D=~/PCVR/HollowKnightVR; G=~/.local/share/Steam/steamapps/common/"Hollow Knight"; E="python3 $HOME/PCVR/bin/steam_eval.py"
echo "--- conflicts"; for f in $(cd $D/extracted && find . -type f); do [ -e "$G/$f" ] && echo "exists: $f"; done; echo "(none = nothing overwritten)"
cp -an $D/extracted/. "$G"/
ls "$G" | tr '\n' ' '; echo
cat > $D/hkvr-shortcut.sh <<'EOF'
#!/bin/bash
# "Hollow Knight VR" shortcut wrapper: hollow_knight.exe in Hollow Knight's (367520) Proton prefix with BepInEx's
# winhttp.dll doorstop enabled (the library entry launches without the override = flat game, mod dormant).
# touch ~/PCVR/HollowKnightVR/debug for a Proton log; env.test is sourced if present.
D="$HOME/PCVR/HollowKnightVR"
export STEAM_COMPAT_DATA_PATH="$HOME/.local/share/Steam/steamapps/compatdata/367520"
export WINEDLLOVERRIDES="winhttp=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
[ -f "$D/env.test" ] && source "$D/env.test"
[ -e "$D/debug" ] && export PROTON_LOG=1 PROTON_LOG_DIR="$D/logs" WINEDEBUG="${WINEDEBUG:-+loaddll}"
mkdir -p "$D/logs"; echo "$(date) args: $*" >> "$D/last-launch.txt"
exec "$@"
EOF
chmod +x $D/hkvr-shortcut.sh; touch $D/debug
id=$(python3 ~/PCVR/bin/steam_shortcuts.py list | python3 -c 'import json,sys;print(next((a["appid"] for a in json.load(sys.stdin) if a["name"]=="Hollow Knight VR"),""))')
[ -n "$id" ] || id=$(python3 ~/PCVR/bin/steam_shortcuts.py add "Hollow Knight VR" "$G/hollow_knight.exe" "$G" | tail -1)
echo "shortcut id: $id"; echo $id > $D/appid.txt
$E "SteamClient.Apps.SpecifyCompatTool($id, \"proton-experimental-arm64\"); SteamClient.Apps.SetShortcutLaunchOptions($id, \"$D/hkvr-shortcut.sh %command%\"); 'ok'" | head -1
cat > $D/hk_launch.sh <<'EOF'
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
EOF
chmod +x $D/hk_launch.sh
bash $D/hk_launch.sh 75
