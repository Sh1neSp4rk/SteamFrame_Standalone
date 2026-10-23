#!/bin/bash
# Launch Far Cry VR with the hudbridge; watch memory (kill the game below 700 MB available) and report the bridge.
# usage: fc_bridgetest.sh [seconds] [keep]   keep = leave the game running afterwards
D=~/PCVR/FarCryVR; L=~/.local/share/Steam/steamapps/common/FarCry/ovrshim.log
pkill -f '[F]arCry(Configurator)?\.exe'; pkill -f '[h]udbridge'; sleep 2
rm -f $D/env.test $D/hudbridge.log
id=$(cat $D/appid.txt); gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id)
(steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
avail() { awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo; }
rss() { ps -o rss= -C vrcompositor 2>/dev/null | head -1 | awk '{print int($1/1024)}'; }
n=${1:-90}
for ((t=10; t<=n; t+=10)); do
  sleep 10
  a=$(avail)
  echo "t=${t}s avail ${a} MB, vrcompositor $(rss) MB, game $(pgrep -f '[F]arCry\.exe' >/dev/null && echo up || echo down), bridge $(pgrep -f '[h]udbridge' >/dev/null && echo up || echo down)"
  if [ "$a" -lt 700 ]; then echo "LOW MEMORY: closing the game"; pkill -f '[F]arCry\.exe'; break; fi
done
echo "=== ovrshim"; grep -v -E '^  (dev|queue|image lo|width|height|format) ' "$L" | uniq -c | head -30
echo "=== hudbridge"; tail -25 $D/hudbridge.log 2>/dev/null
ls -la /tmp/farcryvr_bridge_* 2>/dev/null
[ "$2" = keep ] || { pkill -f '[F]arCry\.exe'; sleep 3; echo "bridge after game exit: $(pgrep -f '[h]udbridge' >/dev/null && echo still up || echo gone)"; }
