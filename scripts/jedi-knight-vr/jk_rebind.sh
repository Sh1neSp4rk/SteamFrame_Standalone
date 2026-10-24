#!/bin/bash
# After engine changes that add OpenXR actions: rebuild, let SteamVR regenerate both games' defaults (so it knows every
# action), lock the Frame bindings over them, then start Jedi Academy for play.
L=~/.local/share/Steam/logs/vrserver.txt
pkill -9 -f 'open(jk|jo)_sp[.]aarch64'; sleep 2
bash ~/PCVR/JKXR/jk_build.sh > /tmp/jk_build.out 2>&1 || { tail -30 /tmp/jk_build.out; exit 1; }
grep -E 'patched|FAILED' /tmp/jk_build.out
bash ~/PCVR/JKXR/jk_setup.sh > /dev/null || exit 1
for k in jka jko; do
  case $k in jka) app=steam.app.2265637930;; jko) app=steam.app.2719912217;; esac
  F=~/.config/openvr/config/openxr/${app}_oculus_touch_0_binding.json
  chmod 644 $F 2>/dev/null; rm -f $F ~/.config/openvr/config/openxr/${app}_khr_simple_controller_*_binding.json
  bash ~/PCVR/JKXR/jk_launch.sh $k 25 > /dev/null 2>&1
  python3 - "$F" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
acts = sorted({v["output"].rsplit("/", 1)[1] for b in d["bindings"].values() for s in b.get("sources", []) for v in s["inputs"].values()})
print(sys.argv[1].split("/")[-1].split("_")[0], len(acts), "actions:", " ".join(acts))
EOF
done
python3 ~/PCVR/JKXR/jk_controls.py
bash ~/PCVR/JKXR/jk_launch.sh jka 25 keep > /dev/null 2>&1
grep -a -E 'Unable to write|Loading [0-9]+ bindings|attempting to load default|Successfully loaded binding' $L | tail -4 | cut -c1-200
pgrep -f 'openjk_sp[.]aarch64' > /dev/null && echo "Jedi Academy running"
