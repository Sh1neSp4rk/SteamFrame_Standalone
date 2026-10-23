#!/bin/bash
# Library entries -> flat by default via flatvr-launch.sh; "<Game> VR" shortcuts -> steam -applaunch <id> -frame-vr.
# Also removes the two Quake shortcuts that can't reach VR (files stay).
E="python3 $HOME/PCVR/bin/steam_eval.py"
W="$HOME/PCVR/bin/flatvr-launch.sh"
chmod +x "$W"
declare -A NAME=( [519860]="DUSK HD VR" [550]="Left 4 Dead 2 VR" [620]="Portal 2 VR" [622650]="Bendy VR" )
declare -A KEY=( [519860]=dusk [550]=l4d2 [620]=portal2 [622650]=bendy )
existing=$(python3 ~/PCVR/bin/steam_shortcuts.py list)
for app in 519860 550 620 622650; do
  $E "SteamClient.Apps.SetAppLaunchOptions($app, \"$W ${KEY[$app]} %command%\")" > /dev/null
  n="${NAME[$app]}"
  id=$(echo "$existing" | python3 -c 'import json,sys;n=sys.argv[1];print(next((str(a["appid"]) for a in json.load(sys.stdin) if a["name"]==n),""))' "$n")
  [ -n "$id" ] || id=$(python3 ~/PCVR/bin/steam_shortcuts.py add "$n" /usr/bin/steam "$HOME" | tail -1)
  $E "SteamClient.Apps.SetAppLaunchOptions($id, \"-applaunch $app -frame-vr\")" > /dev/null
  echo "$app -> ${KEY[$app]} flat by default; VR shortcut \"$n\" appid $id"
done
for id in 4126529436 2568474145; do python3 ~/PCVR/bin/steam_shortcuts.py remove $id && echo "removed shortcut $id"; done
python3 ~/PCVR/bin/steam_shortcuts.py list
