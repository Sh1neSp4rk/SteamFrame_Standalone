#!/bin/bash
# Launch wrapper for the "Red Faction VR" non-Steam shortcut: run AlpineFactionVR.exe inside Red Faction's (20530)
# Proton prefix so saves/settings are shared with the flat game. touch ~/PCVR/RedFactionVR/debug for a Proton log.
D="$HOME/PCVR/RedFactionVR"
export STEAM_COMPAT_DATA_PATH="$HOME/.local/share/Steam/steamapps/compatdata/20530"
[ -f "$D/env.test" ] && source "$D/env.test"
[ -e "$D/debug" ] && export PROTON_LOG=1 PROTON_LOG_DIR="$D/logs" WINEDEBUG="${WINEDEBUG:-+loaddll}"
mkdir -p "$D/logs"
echo "$(date) args: $*" >> "$D/last-launch.txt"
mode=$(cat "$D/mode" 2>/dev/null || echo play)
if [ "$mode" = cmd ]; then
  # replace the launcher exe and its args with cmd.exe /c <cmd.txt>
  args=(); for a in "$@"; do case "$a" in */AlpineFactionVR.exe) break;; esac; args+=("$a"); done
  exec "${args[@]}" "c:\\windows\\system32\\cmd.exe" /c "$(cat "$D/cmd.txt")"
fi
if [ "$mode" = run ]; then
  # replace the launcher exe and its args with the command in $D/run.txt (one argument per line)
  args=(); for a in "$@"; do case "$a" in */AlpineFactionVR.exe) break;; esac; args+=("$a"); done
  mapfile -t cmd < "$D/run.txt"
  exec "${args[@]}" "${cmd[@]}"
fi
exec "$@"
