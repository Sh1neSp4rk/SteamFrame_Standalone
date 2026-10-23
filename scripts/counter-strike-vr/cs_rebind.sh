#!/bin/bash
# After engine changes that add OpenXR actions: let SteamVR regenerate the app's default binding (so it knows every
# action), then lock the Frame binding over it and start the game for play.
F=~/.config/openvr/config/openxr/steam.app.3307658986_oculus_touch_0_binding.json
L=~/.local/share/Steam/logs/vrserver.txt
pkill -9 -f '[x]ash3d -game cstrike'; sleep 2
bash ~/PCVR/CSVR/cs_build_engine.sh > /tmp/cs_eng.out 2>&1 || { tail -20 /tmp/cs_eng.out; exit 1; }
grep -E 'patched|FAILED' /tmp/cs_eng.out
chmod 644 "$F" 2>/dev/null; rm -f "$F"
echo "== pass 1: SteamVR writes its default"
bash ~/PCVR/CSVR/cs_launch.sh 20 > /dev/null 2>&1
python3 - "$F" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
acts = sorted({v["output"].rsplit("/", 1)[1] for b in d["bindings"].values() for s in b.get("sources", []) for v in s["inputs"].values()})
print("default lists", len(acts), "actions:", " ".join(acts))
EOF
python3 ~/PCVR/CSVR/cs_controls.py
echo "== pass 2: Frame binding"
t0=$(date '+%H:%M:%S')
bash ~/PCVR/CSVR/cs_launch.sh 20 keep > /dev/null 2>&1
grep -a -E 'Unable to write|Loading [0-9]+ bindings|attempting to load default|Successfully loaded binding' $L | tail -4 | cut -c1-200
grep -a -E 'Sh1ne|frame_controls|frame_name' ~/PCVR/CSVR/game/csvr-last.log | head -3
pgrep -f '[x]ash3d -game' >/dev/null && echo "game running"
