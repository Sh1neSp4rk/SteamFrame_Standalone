#!/bin/bash
# "Unreal Revived VR" shortcut wrapper: own Proton prefix (compatdata/<shortcut id>); Unreal Revived installed inside it.
# touch ~/PCVR/UnrealRevivedVR/debug for a Proton log; env.test is sourced if present.
# mode file: play (default) | run (replace the exe+args with $D/run.txt, one argument per line) | cmd (cmd.exe /c $D/cmd.txt)
D="$HOME/PCVR/UnrealRevivedVR"
export STEAM_COMPAT_DATA_PATH="$HOME/.local/share/Steam/steamapps/compatdata/$(cat "$D/appid.txt")"
# Microsoft d3dcompiler_47 (next to the exe): Wine's builtin can't compile the renderer's SV_ClipDistance shaders
export WINEDLLOVERRIDES="d3dcompiler_47=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
[ -f "$D/env.test" ] && source "$D/env.test"
[ -e "$D/debug" ] && export PROTON_LOG=1 PROTON_LOG_DIR="$D/logs" WINEDEBUG="${WINEDEBUG:-+loaddll}"
mkdir -p "$D/logs"; echo "$(date) args: $*" >> "$D/last-launch.txt"
mode=$(cat "$D/mode" 2>/dev/null || echo play)
if [ "$mode" != play ]; then
  args=(); for a in "$@"; do case "$a" in *.exe|*.EXE) break;; esac; args+=("$a"); done
  if [ "$mode" = cmd ]; then exec "${args[@]}" "c:\\windows\\system32\\cmd.exe" /c "$(cat "$D/cmd.txt")"; fi
  mapfile -t cmd < "$D/run.txt"; exec "${args[@]}" "${cmd[@]}"
fi
# a crash leaves Running.ini behind and the next start opens a recovery dialog
rm -f "$STEAM_COMPAT_DATA_PATH/pfx/drive_c/Games/Unreal Revived/System64/Running.ini"
exec "$@"
