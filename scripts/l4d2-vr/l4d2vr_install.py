"""Installs L4D2VR v0.6.2 (sd805/l4d2vr) into Left 4 Dead 2 on the Steam Frame, with a Frame controller binding.

Frame layout (grips unused, like DUSK/Doom 3 on the Frame):
  right trigger  shoot                    left trigger   shove (secondary attack)
  left bumper    jump                     right bumper   use
  right A        crouch / menu select     right B        reload / menu back
  right X        flashlight               right Y        jump
  left stick     move; click = recenter   right stick    turn; push up/down = prev/next item; click = show HUD
  left d-pad     menu up/down/left/right; left/right also prev/next item
  menu (right)   pause                    view (left)    scoreboard
Run with the game closed. Usage: python3 l4d2vr_install.py <game dir>"""
import json, os, shutil, sys

SRC = os.path.expanduser("~/PCVR/L4D2VR/x")
GAME = sys.argv[1]
AM = os.path.join(GAME, "VR", "SteamVRActionManifest")

for f in ("d3d9.dll", "openvr_api.dll"):
    dst = os.path.join(GAME, f)
    if os.path.exists(dst) and not os.path.exists(dst + ".orig-l4d2vr"):
        shutil.copy(dst, dst + ".orig-l4d2vr")
    shutil.copy(os.path.join(SRC, f), dst)
if os.path.isdir(os.path.join(GAME, "VR")):
    keep = os.path.join(GAME, "VR", "config.txt")
    cfg = open(keep).read() if os.path.exists(keep) else None
    shutil.copytree(os.path.join(SRC, "VR"), os.path.join(GAME, "VR"), dirs_exist_ok=True)
    if cfg is not None:
        open(keep, "w").write(cfg)   # keep the user's tweaks
else:
    shutil.copytree(os.path.join(SRC, "VR"), os.path.join(GAME, "VR"))
print("installed d3d9.dll, openvr_api.dll, VR/")

L, R = "/user/hand/left/input", "/user/hand/right/input"
def act(*names):
    return [f"/actions/main/in/{n}" for n in names]
def button(path, *outs):
    return [{"path": path, "mode": "button", "inputs": {"click": {"output": o}}} for o in act(*outs)]

sources = [
    {"path": f"{L}/thumbstick", "mode": "joystick", "parameters": {"deadzone_pct": "10"},
     "inputs": {"position": {"output": act("Walk")[0]}, "click": {"output": act("ResetPosition")[0]}}},
    {"path": f"{R}/thumbstick", "mode": "joystick", "parameters": {"deadzone_pct": "10"},
     "inputs": {"position": {"output": act("Turn")[0]}, "click": {"output": act("ShowHUD")[0]}}},
    {"path": f"{R}/thumbstick", "mode": "dpad",
     "parameters": {"sub_mode": "touch", "deadzone_pct": "75", "overlap_pct": "0"},
     "inputs": {"north": {"output": act("PrevItem")[0]}, "south": {"output": act("NextItem")[0]}}},
    # (no menu d-pad on the left stick: it is the walk stick; the left d-pad buttons navigate menus)
    *button(f"{R}/trigger", "PrimaryAttack"),
    *button(f"{L}/trigger", "SecondaryAttack"),
    *button(f"{L}/bumper", "Jump"),
    *button(f"{R}/bumper", "Use"),
    *button(f"{R}/a", "Crouch", "ActivateVR", "MenuSelect"),
    *button(f"{R}/b", "Reload", "MenuBack"),
    *button(f"{R}/x", "Flashlight"),
    *button(f"{R}/y", "Jump"),
    *button(f"{L}/dpad_up", "MenuUp"),
    *button(f"{L}/dpad_down", "MenuDown"),
    *button(f"{L}/dpad_left", "MenuLeft", "PrevItem"),
    *button(f"{L}/dpad_right", "MenuRight", "NextItem"),
    *button(f"{R}/menu", "Pause"),
    *button(f"{L}/view", "Scoreboard"),
]

touch = json.load(open(os.path.join(AM, "bindings_oculus_touch.json")))
binding = {
    "action_manifest_version": 0,
    "alias_info": {},
    "bindings": {k: dict(v) for k, v in touch["bindings"].items()},
    "category": "steamvr_input",
    "controller_type": "frame_controller",
    "description": "Steam Frame layout for L4D2VR: bumpers jump/use, A crouch, B reload, X flashlight, menu pauses, grips unused.",
    "name": "L4D2VR - Steam Frame",
    "options": {},
    "simulated_actions": [],
}
binding["bindings"]["/actions/main"]["sources"] = sources   # poses/skeleton/haptics stay as in the Touch file
json.dump(binding, open(os.path.join(AM, "bindings_frame_controller.json"), "w"), indent=2)

mpath = os.path.join(AM, "action_manifest.json")
m = json.load(open(mpath))
m["default_bindings"] = [d for d in m["default_bindings"] if d["controller_type"] != "frame_controller"]
m["default_bindings"].insert(0, {"controller_type": "frame_controller", "binding_url": "bindings_frame_controller.json"})
json.dump(m, open(mpath, "w"), indent=2)
print("frame_controller binding added")
