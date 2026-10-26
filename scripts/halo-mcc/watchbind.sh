#!/bin/bash
# Waits for SteamVR to write Halo MCC's new Touch default binding, then replaces it with the Frame layout (read-only).
X=~/.config/openvr/config/openxr
for i in $(seq 1 600); do
  f=$(ls $X/steam.app.976730_oculus_touch_*_binding.json 2>/dev/null | head -1)
  if [ -n "$f" ]; then
    sleep 2
    python3 ~/PCVR/HaloMCCVR/mcc_binding.py ~/PCVR/HaloMCCVR/mcc_frame_binding.json >/dev/null
    cp ~/PCVR/HaloMCCVR/mcc_frame_binding.json "$f" && chmod 444 "$f"
    echo "$(date +%T) replaced $f"; exit 0
  fi
  sleep 1
done
echo "timed out"
