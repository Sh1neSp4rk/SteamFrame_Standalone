#!/bin/bash
# Launch "Red Faction VR" through Steam, wait, report. usage: rf_launch.sh [seconds]
D=~/PCVR/RedFactionVR; G=~/.local/share/Steam/steamapps/common/"Red Faction"; L=~/.local/share/Steam/logs
id=$(cat $D/appid.txt); gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id)
mkdir -p ~/.local/share/Steam/steamapps/compatdata/20530
# SteamVR honours the Frame-path custom OpenXR binding only when the app's XR input context holds one interaction
# profile; keep the auto-generated Index (knuckles) default unwritable so SteamVR skips it ("Loading 1 bindings").
K=~/.config/openvr/config/openxr/steam.app.3865968601_knuckles_1_binding.json
[ -f "$K" ] || echo '{}' > "$K"; chmod 444 "$K"
python3 ~/PCVR/bin/steam_shortcuts.py stop $id >/dev/null 2>&1; sleep 2
rm -f $D/logs/*.log
(steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
n=${1:-90}; for ((t=15; t<=n; t+=15)); do sleep 15; echo "t=${t}s: $(pgrep -a -f '[A]lpineFactionVR.exe|[R]F.exe' | cut -c1-90 | head -2 | tr '\n' ';')"; done
echo "--- game logs"; ls -la --time-style=+%T "$G"/logs 2>/dev/null | cut -c25-; f=$(ls -t "$G"/logs/*.log 2>/dev/null | head -1); [ -n "$f" ] && tail -40 "$f" | cut -c1-180
echo "--- proton log (non-fixme err/openxr)"; f=$(ls -t $D/logs/*.log 2>/dev/null | head -1); [ -n "$f" ] && wc -l $f && grep -a -i -E 'openxr|xrCreate|xrclient|err:|unhandled|wineopenxr|Loaded L".*(openxr|d3d11|dxvk|AlpineFaction|RF.exe)' "$f" | grep -v fixme | tail -25 | cut -c1-200
echo "--- vrserver"; grep -a -i -E 'alpine|RF.exe|redfaction' $L/vrserver.txt | tail -5 | cut -c1-180
ls -t $L | grep -i -E 'xrclient|vrclient' | head -3
