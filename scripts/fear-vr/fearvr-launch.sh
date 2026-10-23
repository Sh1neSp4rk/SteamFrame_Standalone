#!/bin/bash
# Steam launch wrapper for F.E.A.R. VR on the Frame (launch option: <this> %command%).
# ~/PCVR/FEARVR/mode selects what runs in place of FEAR.exe:
#   play     - "F.E.A.R. VR.exe" (default). Its Steam handoff relaunch (-fearvrhandoff=...) runs FEAR.exe.
#   diagnose - "F.E.A.R. VR.exe" --diagnose (read-only launcher preflight)
#   setup    - the mod's Setup, silent install into C:\FEAR (a hard-link mirror; Setup rejects Z:/S: as links)
#   flat     - the original command, untouched
# OpenXR: the registered C:\openxr\wineopenxr64.json also serves 32-bit (system32 -> syswow64 redirect);
# do not set XR_RUNTIME_JSON (Proton's native OpenXR setup reads it too). touch ~/PCVR/FEARVR/debug for a Proton log in ~/steam-21090.log.
D="$HOME/PCVR/FEARVR"
G="$HOME/.local/share/Steam/steamapps/common/FEAR Ultimate Shooter Edition"
C="$HOME/.local/share/Steam/steamapps/compatdata/21090/pfx/drive_c"
mode=$(cat "$D/mode" 2>/dev/null || echo play)
[ -e "$D/debug" ] && export PROTON_LOG=1 WINEDEBUG="${WINEDEBUG:-+loaddll}"
echo "$(date) mode=$mode args: $*" >> "$D/last-launch.txt"

args=("$@")
idx=-1
for i in "${!args[@]}"; do
  case "${args[$i]}" in */FEAR.exe|*/FEAR.EXE) idx=$i; break ;; esac
done
case " $* " in
  *-fearvrhandoff*)
    # The launcher's handoff relaunch (from the "F.E.A.R. VR" shortcut) must join the launcher's running
    # wineserver; Proton's waitforexitandrun would wait for that server to exit, deadlocking both.
    args=("${args[@]/#--verb=waitforexitandrun/--verb=run}")
    args=("${args[@]/#waitforexitandrun/run}")
    echo "handoff: ${args[*]}" >> "$D/last-launch.txt"
    exec "${args[@]}" ;;
esac
if [ "$mode" = flat ] || [ $idx -lt 0 ]; then exec "$@"; fi

pre=("${args[@]:0:$idx}")
case "$mode" in
  setup)    cmd=("$C/FEARVR-Setup/F.E.A.R. VR Setup.exe" --action install --game "C:\\FEAR"
                 --silent --result "C:\\FEARVR-Setup\\setup-result.json") ;;
  diagnose) cmd=("$G/F.E.A.R. VR.exe" --diagnose) ;;
  *)        cmd=("$G/F.E.A.R. VR.exe") ;;
esac
echo "running: ${cmd[*]}" >> "$D/last-launch.txt"
cd "$G"
exec "${pre[@]}" "${cmd[@]}"
