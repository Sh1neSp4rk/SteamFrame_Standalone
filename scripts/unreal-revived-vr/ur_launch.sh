#!/bin/bash
# Point "Unreal Revived VR" at UnrealRevivedVR.exe (first run only), then launch through Steam and report.
# usage: ur_launch.sh [seconds]
D=~/PCVR/UnrealRevivedVR; L=~/.local/share/Steam/logs; id=$(cat $D/appid.txt); gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id)
P=~/.local/share/Steam/steamapps/compatdata/$id/pfx/drive_c; G="$P/Games/Unreal Revived"; S="$G/System64"
if [ ! -f $D/exe.set ]; then
  python3 $HOME/PCVR/bin/steam_eval.py "SteamClient.Apps.SetShortcutExe($id, \"\\\"$S/UnrealRevivedVR.exe\\\"\"); SteamClient.Apps.SetShortcutStartDir($id, \"\\\"$S\\\"\"); 'ok'" | head -1
  touch $D/exe.set
fi
echo "=== VC++ runtime next to the exe"; ls "$S" | grep -i -E '^(vcruntime|msvcp|concrt)' | tr '\n' ' '; echo
for f in vcruntime140.dll vcruntime140_1.dll msvcp140.dll; do
  if [ ! -f "$S/$f" ]; then c=$(find ~/.local/share/Steam/steamapps/compatdata -path '*/system32/*' -iname "$f" 2>/dev/null | while read x; do file -b "$x" | grep -q x86-64 && echo "$x"; done | head -1); [ -n "$c" ] && cp "$c" "$S/$f" && echo "copied x86-64 $f from $c"; fi
done
for f in "$S"/vcruntime140*.dll "$S"/msvcp140.dll; do [ -f "$f" ] && printf '%-22s %s\n' "$(basename "$f")" "$(file -b "$f" | cut -c1-40)"; done
python3 ~/PCVR/bin/steam_shortcuts.py stop $id >/dev/null 2>&1; pkill -f '[U]nrealRevived(VR)?\.exe' 2>/dev/null; sleep 2
rm -f $D/logs/*.log; echo play > $D/mode; t0=$(date +%s)
(steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
n=${1:-90}; for ((t=15; t<=n; t+=15)); do sleep 15; echo "t=${t}s: $(pgrep -a -f '[U]nrealRevived(VR)?\.exe|[U]nreal\.exe' | grep -v -E 'reaper|bwrap|adverb|proton' | cut -c1-90 | head -2 | tr '\n' ';')"; done
mkdir -p $D/shots; gamescopectl screenshot $D/shots/run.png >/dev/null 2>&1
echo "=== game logs written since launch"; find "$G" "$P/users" -newermt "@$t0" -iname '*.log' 2>/dev/null | while read f; do echo "-- $f ($(wc -l < "$f") lines)"; grep -a -i -E 'xr|openxr|vr|d3d12|vkd3d|render|error|critical|warning: failed|exit|crash|controller|profile' "$f" | head -40 | cut -c1-200; done
echo "=== vrserver"; grep -a -E "$id|UnrealRevived" $L/vrserver.txt | tail -5 | cut -c1-200
echo "=== xrclient"; ls -t $L | grep -i -E 'xrclient' | head -2; f=$(ls -t $L/xrclient_*nreal* 2>/dev/null | head -1); [ -n "$f" ] && tail -15 "$f" | cut -c1-200
echo "=== proton log"; f=$(ls -t $D/logs/*.log 2>/dev/null | head -1); [ -n "$f" ] && grep -a -i -E 'wineopenxr|openxr|vkd3d|d3d12|err:|unhandled|exception|Loaded L".*(UnrealRevived|D3D12Drv|openxr|vcruntime|msvcp)' "$f" | grep -v -E 'fixme|winebth|device_notify|hid:' | tail -30 | cut -c1-200
