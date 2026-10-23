#!/bin/bash
# Heretic / Hexen / Hexen: Deathkings in GZDoomVR, using the original DOS WADs that ship in the
# "Heretic + Hexen" (3286930) rerelease's dos/base folder. Same setup as the Doom VR entries.
Z="$HOME/PCVR/GZDoomVR"
B="/run/media/steamos/External-00/steamapps/common/Heretic + Hexen/dos/base"
E="python3 $HOME/PCVR/bin/steam_eval.py"
cp -f "$B/heretic/HERETIC.WAD" "$Z/heretic.wad"
cp -f "$B/hexen/HEXEN.WAD" "$Z/hexen.wad"
cp -f "$B/hexendk/HEXDD.WAD" "$Z/hexdd.wad"
ls -la "$Z"/heretic.wad "$Z"/hexen.wad "$Z"/hexdd.wad
existing=$(python3 ~/PCVR/bin/steam_shortcuts.py list)
add() {  # add NAME "LAUNCH OPTIONS"
  id=$(echo "$existing" | python3 -c 'import json,sys;n=sys.argv[1];print(next((str(a["appid"]) for a in json.load(sys.stdin) if a["name"]==n),""))' "$1")
  [ -n "$id" ] || id=$(python3 ~/PCVR/bin/steam_shortcuts.py add "$1" "$Z/gzdoomvr.exe" "$Z" | tail -1)
  $E "SteamClient.Apps.SpecifyCompatTool($id, \"proton_experimental\")" > /dev/null
  $E "SteamClient.Apps.SetAppLaunchOptions($id, \"$2\")" > /dev/null
  echo "$1  appid $id  ($2)"
}
add "Heretic VR" "-iwad heretic.wad +vr_mode 10"
add "Hexen VR" "-iwad hexen.wad +vr_mode 10"
add "Hexen Deathkings VR" "-iwad hexen.wad -file hexdd.wad +vr_mode 10"
