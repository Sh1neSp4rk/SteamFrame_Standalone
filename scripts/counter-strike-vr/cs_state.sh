#!/bin/bash
L=~/.local/share/Steam/logs
G=~/PCVR/CSVR/game
pgrep -a -f '[x]ash3d -game' | cut -c1-60
ps -o pcpu=,rss= -p $(pgrep -f '[x]ash3d -game' | head -1) 2>/dev/null
echo "=== compositor (xash)"; grep -a -i -E 'xash|3307658986|EndFrame|layer|quad' $L/vrcompositor.txt | tail -8 | cut -c1-220
echo "=== vrclient xash log"; ls -t $L/vrclient_xash3d*.txt 2>/dev/null | head -1 | xargs -r tail -12 | cut -c1-200
echo "=== game log tail"; grep -a -v DW_RLE $G/csvr-last.log | tail -8
mkdir -p ~/PCVR/CSVR/shots; gamescopectl screenshot ~/PCVR/CSVR/shots/now.png >/dev/null 2>&1; sleep 2; ls -la ~/PCVR/CSVR/shots/now.png 2>&1 | cut -c25-
