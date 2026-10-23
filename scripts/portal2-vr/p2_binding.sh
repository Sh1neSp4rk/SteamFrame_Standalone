#!/bin/bash
# Portal 2 VR uses the same SteamVR action manifest as L4D2VR: reuse the Frame binding and register it.
P="$HOME/.local/share/Steam/steamapps/common/Portal 2/VR/SteamVRActionManifest"
L="$HOME/.local/share/Steam/steamapps/common/Left 4 Dead 2/VR/SteamVRActionManifest"
python3 -I - "$P" "$L" <<'EOF'
import json, os, sys
p, l = sys.argv[1], sys.argv[2]
pa = json.load(open(os.path.join(p, "action_manifest.json")))
la = json.load(open(os.path.join(l, "action_manifest.json")))
assert [a["name"] for a in pa["actions"]] == [a["name"] for a in la["actions"]], "action sets differ"
b = json.load(open(os.path.join(l, "bindings_frame_controller.json")))
t = json.load(open(os.path.join(p, "bindings_oculus_touch.json")))["bindings"]
for k, v in t.items():           # keep Portal 2's own pose/skeleton/haptics entries
    if k != "/actions/main":
        b["bindings"][k] = v
b["name"] = "Portal 2 VR - Steam Frame"
b["description"] = "Steam Frame layout (shared with L4D2VR): triggers = portals, bumpers jump/use, A crouch, menu pauses, grips unused."
json.dump(b, open(os.path.join(p, "bindings_frame_controller.json"), "w"), indent=2)
pa["default_bindings"] = [d for d in pa["default_bindings"] if d["controller_type"] != "frame_controller"]
pa["default_bindings"].insert(0, {"controller_type": "frame_controller", "binding_url": "bindings_frame_controller.json"})
json.dump(pa, open(os.path.join(p, "action_manifest.json"), "w"), indent=2)
print("Portal 2 frame binding written")
EOF
bash ~/PCVR/bin/kill_app.sh 620 > /dev/null 2>&1; sleep 6
bash ~/PCVR/Portal2VR/p2_go.sh 2>&1 | grep -a -E 'Workshop|portal2.exe' | tail -3 | cut -c1-200
