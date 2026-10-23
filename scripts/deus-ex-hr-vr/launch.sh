#!/bin/bash
# Launches DXHR:DC through Steam (optionally with Proton/DXVK debug logs) and reports mod state.
# usage: launch.sh [seconds] [debug]
S=~/.local/share/Steam
G="$S/steamapps/common/Deus Ex Human Revolution Director's Cut"
if [ "$2" = debug ]; then
  python3 ~/PCVR/bin/steam_eval.py 'SteamClient.Apps.SetAppLaunchOptions(238010, "PROTON_LOG=1 WINEDEBUG=+loaddll,warn+module,err DXVK_LOG_LEVEL=info DXVK_LOG_PATH=/home/steamos/PCVR/DeusExHRVR/dxvk-logs %command%"), "debug options"'
  rm -rf ~/steam-238010.log ~/PCVR/DeusExHRVR/dxvk-logs; mkdir -p ~/PCVR/DeusExHRVR/dxvk-logs
else
  python3 ~/PCVR/bin/steam_eval.py 'SteamClient.Apps.SetAppLaunchOptions(238010, ""), "plain options"'
fi
sleep 2
DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 steam steam://rungameid/238010 >/dev/null 2>&1 &
sleep ${1:-75}
echo "== processes"; pgrep -a -f -i 'DXHRDC.exe|DeusExHRVRHost.exe' | grep -v -E 'pgrep|bash' | cut -c1-110
echo "== Steam launch state"; grep -a -E '238010.*(Interstitial|Completed|Waiting)' $S/logs/console_log.txt | tail -2 | cut -c1-120
echo "== mod logs"; ls -la "$G" | grep -i -E 'DeusExHRVR.*\.(log|csv|txt)'
for l in "$G"/DeusExHRVR*.log "$G"/DeusExHRVR/*.log; do [ -f "$l" ] && { echo "-- $l"; tail -30 "$l" | cut -c1-200; }; done
true
