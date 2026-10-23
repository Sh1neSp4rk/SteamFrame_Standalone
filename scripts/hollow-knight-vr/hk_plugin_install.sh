#!/bin/bash
# Install the freshly uploaded FrameVR_HK.dll, relaunch Hollow Knight VR (with FRAMEVR_DEBUG=1 when "debug" is given).
D=~/PCVR/HollowKnightVR; G=~/.local/share/Steam/steamapps/common/"Hollow Knight"
pkill -f '[h]ollow_knight.exe' 2>/dev/null; sleep 3
cp -f "$D/FrameVR_HK.dll" "$G/BepInEx/plugins/"
if [ "$1" = "debug" ]; then echo 'export FRAMEVR_DEBUG=1' > "$D/env.test"; else rm -f "$D/env.test"; fi
bash "$D/hk_launch.sh" 60 2>&1 | grep -E '^t=60'
grep -a -E 'FrameVR|patch .* failed' "$G/BepInEx/LogOutput.log" | head -4 | cut -c1-160
