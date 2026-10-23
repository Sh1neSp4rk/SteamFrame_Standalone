#!/bin/bash
# Launch "Counter-Strike VR" through Steam and report. usage: cs_launch.sh [seconds] [keep]
G=~/PCVR/CSVR/game
# -9: a blocking engine warning box ignores SIGTERM (this is the game, never vrserver)
pkill -9 -f '[x]ash3d -game cstrike'; sleep 2
id=3307658986; gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id)
rm -f $G/csvr-last.log $G/cstrike/engine.log
(steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
n=${1:-40}; for ((t=10; t<=n; t+=10)); do sleep 10; echo "t=${t}s: $(pgrep -f '[x]ash3d -game' >/dev/null && echo running || echo gone)"; done
echo "=== OpenXR / errors (wrapper log)"; grep -a -i -E 'openxr|xr_|error|fail|segfault|abort|cylinder|glx|session' $G/csvr-last.log | head -30
echo "=== wrapper log tail"; tail -15 $G/csvr-last.log
echo "=== engine.log tail"; tail -25 $G/cstrike/engine.log 2>/dev/null
echo "=== vrserver"; grep -a -i -E 'xash|csvr|openxr.*(app|session)' ~/.local/share/Steam/logs/vrserver.txt | tail -6 | cut -c1-200
[ "$2" = keep ] || pkill -9 -f '[x]ash3d -game cstrike'
