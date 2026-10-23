"""Persist per-app SteamVR binding selections in steamvr.vrsettings (vrcmd's --set-settings-string only changes
vrserver's memory, which is not what it reads when an app connects). Restart SteamVR afterwards.
Usage: python3 vrsettings_bind.py <appkey> <legacy|openxr|steamvrinput> <binding json> [...more triples]"""
import json, os, shutil, sys, time

S = os.path.expanduser("~/.config/openvr/config/steamvr.vrsettings")
shutil.copy(S, S + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
s = json.load(open(S))
args = sys.argv[1:]
for i in range(0, len(args), 3):
    app, kind, path = args[i:i + 3]
    sec = s.setdefault(app, {})
    for key in (f"frame_controller_CurrentURL_{kind}", f"frame_controller_250820_CurrentURL_{kind}"):
        sec[key] = "file://" + os.path.abspath(path)
    print(app, kind, path)
json.dump(s, open(S, "w"), indent=3)
