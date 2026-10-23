#!/bin/bash
# Launches Bendy through Steam and reports BepInEx/Unity logs.
S=~/.local/share/Steam
G="$S/steamapps/common/Bendy and the Ink Machine"
DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 steam steam://rungameid/622650 >/dev/null 2>&1 &
sleep ${1:-60}
echo "== processes"; pgrep -a -f 'Bendy and the Ink Machine.exe' | cut -c1-120 || echo "not running"
echo "== BepInEx log"; tail -40 "$G/BepInEx/LogOutput.log" 2>/dev/null || echo "no BepInEx log"
P=$(find "$S/steamapps/compatdata/622650/pfx/drive_c/users/steamuser/AppData/LocalLow" -name Player.log 2>/dev/null | head -1)
echo "== Player.log ($P)"
[ -n "$P" ] && grep -i -E 'vr|openvr|steamvr|xr|error|exception|fail' "$P" | grep -v -i 'shader' | head -40
