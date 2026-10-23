#!/bin/bash
# Installs Ermac's Hexen VR 3D weapons (WIP pk3) into GZDoomVR and adds it to both Hexen entries.
Z="$HOME/PCVR/GZDoomVR"
E="python3 $HOME/PCVR/bin/steam_eval.py"
cp -f "$HOME/PCVR/HexenVRWeapons/x/hexen_VR_weapons_Ermac_WIP.pk3" "$Z/"
HEX=2541150700; HDK=2150730901
$E "SteamClient.Apps.SetAppLaunchOptions($HDK, \"-iwad hexen.wad -file hexdd.wad hexen_VR_weapons_Ermac_WIP.pk3 +vr_mode 10\")" > /dev/null
# test run of Hexen VR with a console log, then set its normal options
pgrep -f gzdoomvr.exe > /dev/null && { bash ~/PCVR/bin/kill_app.sh 4268466633; sleep 4; }
$E "SteamClient.Apps.SetAppLaunchOptions($HEX, \"-iwad hexen.wad -file hexen_VR_weapons_Ermac_WIP.pk3 +vr_mode 10 +logfile hexenvr-test.log\")" > /dev/null
g=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $HEX)
rm -f "$Z/hexenvr-test.log"
steam "steam://rungameid/$g" > /dev/null 2>&1 &
sleep 45
$E "SteamClient.Apps.SetAppLaunchOptions($HEX, \"-iwad hexen.wad -file hexen_VR_weapons_Ermac_WIP.pk3 +vr_mode 10\")" > /dev/null
pgrep -a -f 'gzdoomvr.exe' | grep -v -E 'pgrep|bash|proton |reaper|srt-bwrap|pv-adverb' | cut -c1-140
L=$(find "$Z" ~/.local/share/Steam/steamapps/compatdata/$HEX -name 'hexenvr-test.log' 2>/dev/null | head -1)
echo "log: $L"
grep -a -i -E 'error|warning|script|hexen_VR|adding|openvr|vr_mode' "$L" | head -40
