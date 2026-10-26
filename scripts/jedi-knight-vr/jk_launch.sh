#!/bin/bash
# Launch a JKXRL game through Steam and report. usage: jk_launch.sh jka|jko [seconds] [keep]
key=${1:-jka}; G=~/PCVR/JKXR/$key; L=~/.local/share/Steam/logs
case $key in jka) id=2265637930; exe=openjk_sp;; jko) id=2719912217; exe=openjo_sp;; esac
pat="${exe}[.]aarch64"
pkill -9 -f "$pat"; sleep 2
gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id); rm -f $G/last.log
t0=$(date '+%H:%M:%S')
(steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
n=${2:-40}; for ((t=10; t<=n; t+=10)); do sleep 10; echo "t=${t}s: $(pgrep -f "$pat" >/dev/null && echo running || echo gone)"; done
echo "=== errors/XR"; grep -a -i -E 'openxr|xr_|vulkan|error|fail|crash|signal|segfault|warning' $G/last.log | grep -v -E 'gameoverlayrenderer' | head -30
echo "=== log tail"; grep -a -v -E 'gameoverlayrenderer|Gamescope WSI|ATTENTION|pApplication|pEngine|ngineVersion|pplicationVersion|apiVersion' $G/last.log | tail -20
echo "=== vrserver"; awk -v t="$t0" '$5 >= t' $L/vrserver.txt | grep -a -i -E "$exe|$id|binding|Loading [0-9]|Unable" | tail -8 | cut -c1-210
[ "$3" = keep ] || pkill -9 -f "$pat"
