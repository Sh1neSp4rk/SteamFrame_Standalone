#!/usr/bin/env python3
"""Add the Deus Ex HR DC case to ~/PCVR/bin/flatvr-launch.sh (flat by default, VR with -frame-vr), set Steam launch
options for 238010 and add the "Deus Ex HR DC VR" shortcut. Idempotent."""
import os, pathlib, shutil, subprocess, sys
B = pathlib.Path.home() / "PCVR/bin"
W = B / "flatvr-launch.sh"
s = W.read_text()
case = r'''  deusex)  # VR: DeusExHRVR (d3d11.dll proxy + atidxx32/atiadlxy stereo shims + 64-bit OpenXR host); flat: the three
           # mod DLLs renamed aside so the game uses Proton's own d3d11 and no stereo driver (Portal 2-style switch)
    G="$HOME/.local/share/Steam/steamapps/common/Deus Ex Human Revolution Director's Cut"
    sw() { [ -e "$G/$1" ] && mv -f "$G/$1" "$G/$2"; }
    if [ $vr = 1 ]; then
      for f in d3d11 atidxx32 atiadlxy; do sw ".$f.dll-vr" "$f.dll"; done
      [ -e "$HOME/PCVR/DeusExHRVR/debug" ] && export PROTON_LOG=1 PROTON_LOG_DIR="$HOME/PCVR/DeusExHRVR/logs"
      exec "${args[@]}"
    fi
    for f in d3d11 atidxx32 atiadlxy; do sw "$f.dll" ".$f.dll-vr"; done
    exec "${args[@]}" ;;
'''
if "  deusex)" not in s:
    marker = "  bendy)"
    assert s.count(marker) == 1, "bendy case not found"
    shutil.copy(W, str(W) + ".bak-deusex")
    s = s.replace(marker, case + marker)
    W.write_text(s)
    print("flatvr-launch.sh: deusex case added")
r = subprocess.run(["bash", "-n", str(W)], capture_output=True, text=True)
print(r.stderr or "syntax ok")
sys.path.insert(0, str(B))
import steam_shortcuts as sc
opts = f"{W} deusex %command%"
print("launch options:", sc.evaluate(f'SteamClient.Apps.SetAppLaunchOptions(238010, "{opts}")'))
import json
NAME = "Deus Ex HR DC VR"
apps = json.loads(subprocess.run(["python3", str(B / "steam_shortcuts.py"), "list"], capture_output=True, text=True).stdout)
sid = next((a["appid"] for a in apps if a["name"] == NAME), None)
if sid is None:
    sid = int(subprocess.run(["python3", str(B / "steam_shortcuts.py"), "add", NAME, "/usr/bin/steam",
                              str(pathlib.Path.home())], capture_output=True, text=True).stdout.strip().splitlines()[-1])
print("shortcut options:", sc.evaluate(f'SteamClient.Apps.SetAppLaunchOptions({sid}, "-applaunch 238010 -frame-vr")'))
print(NAME, sid)
