#!/bin/bash
# Install the Frame-patched AlpineFaction.dll (original kept as .orig), write the Frame binding, relaunch, check the log.
D=~/PCVR/RedFactionVR; G=~/.local/share/Steam/steamapps/common/"Red Faction"
dll=$(find $D/src/build -iname 'AlpineFaction.dll' | head -1); [ -n "$dll" ] || { echo "no built DLL"; exit 1; }
[ -f "$G/AlpineFaction.dll.orig" ] || cp -f "$G/AlpineFaction.dll" "$G/AlpineFaction.dll.orig"
cp -f "$dll" "$G/AlpineFaction.dll"; ls -la --time-style=+%T "$G"/AlpineFaction.dll* | cut -c25-
python3 $D/rf_binding.py
bash $D/rf_launch.sh 60 | grep -E '^t=60' | cut -c1-40
echo "--- mod log"; grep -a -E 'AFVR\] (Runtime|Enabled|Session state|profile|OpenXR session|Error)|ERROR' "$G/logs/AlpineFaction.log" | tail -8 | cut -c1-160
grep -a -E 'Loading [0-9] bindings|Successfully loaded binding file .*rf_frame' ~/.local/share/Steam/logs/vrserver.txt | tail -2 | cut -c1-140
