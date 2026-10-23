#!/bin/bash
# GZDoomVR (Heretic/Hexen) on the Frame: SteamVR's stock Frame legacy binding presses the grip at 10% squeeze,
# which blocks attacking just from holding the controller. Copy it with the grip press raised to 80% (release
# below 70%) and select it for the Heretic/Hexen shortcuts via vrcmd (no SteamVR restart).
OUT="$HOME/PCVR/GZDoomVR/gzdoomvr_frame_binding.json"
python3 -I - "$OUT" <<'EOF'
import json, sys
src = '/opt/steamvr/drivers/frame_controller/resources/input/legacy_bindings_frame_controller.json'
b = json.load(open(src))
b['name'] = 'GZDoomVR - Steam Frame (firm grip)'
b['description'] = 'Stock Frame legacy layout, but the grip press needs an 80% squeeze (releases below 70%).'
for s in b['bindings']['/actions/legacy']['sources']:
    if s['path'].endswith('/grip') and s.get('mode') == 'button':
        s['parameters']['click_activate_threshold'] = '0.8'
        s['parameters']['click_deactivate_threshold'] = '0.7'
        print('grip', s['path'], s['parameters'])
json.dump(b, open(sys.argv[1], 'w'), indent=2)
EOF
V=/opt/steamvr/bin/linuxarm64/vrcmd
for app in 4268466633 2541150700 2150730901; do
  for key in frame_controller_CurrentURL_legacy frame_controller_250820_CurrentURL_legacy; do
    $V --set-settings-string "steam.app.$app" "$key" "file://$OUT" > /dev/null 2>&1
  done
  echo "steam.app.$app -> $($V --settings-string "steam.app.$app" frame_controller_CurrentURL_legacy 2>&1 | tail -1)"
done
