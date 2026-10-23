"""Steam Frame control scheme for Circuit Superstars VR (UnityVR_Bepinex mod + FrameVR_CS plugin + framepad).
Chain: Frame input -> SteamVR action (bindings_frame_controller.json) -> FrameVR_CS drives a virtual Xbox pad
(framepad stands in for ViGEm) -> Circuit Superstars' own gamepad defaults. The Frame has every Xbox button, so this is
the game's Xbox layout 1:1:

  A / B / X / Y as on the pad     RT accelerate   LT brake/reverse     bumpers = LB / RB (via the grip actions)
  left stick steer, right stick as on the pad, stick clicks L3 / R3, d-pad = d-pad (taps; the Frame d-pad pulses)
  menu = Start (pause; the mod: double-tap = first-person view, hold = recenter), view = Back
  grips unused
Run with the game closed; originals are kept as *.orig."""
import json, os, shutil

HOME = os.path.expanduser("~")
GAME = f"{HOME}/.local/share/Steam/steamapps/common/Circuit Superstars"
SVR = f"{GAME}/circuit-superstars_Data/StreamingAssets/SteamVR"
SETTINGS = f"{HOME}/.config/openvr/config/steamvr.vrsettings"
APPS = ("steam.app.1097130", "steam.app.3624666961")   # the app connects as 1097130 (steam_appid.txt); shortcut id too
BINDING = f"{SVR}/bindings_frame_controller.json"


def backup(path):
    if os.path.exists(path) and not os.path.exists(path + ".orig"):
        shutil.copy(path, path + ".orig")


def button(path, action):
    return {"path": path, "mode": "button", "inputs": {"click": {"output": f"/actions/default/in/{action}"}}}


L, R = "/user/hand/left/input", "/user/hand/right/input"
sources = [
    {"path": f"{L}/thumbstick", "mode": "joystick",
     "inputs": {"position": {"output": "/actions/default/in/leftjoystick"},
                "click": {"output": "/actions/default/in/clickleftjoystick"}}},
    {"path": f"{R}/thumbstick", "mode": "joystick",
     "inputs": {"position": {"output": "/actions/default/in/rightjoystick"},
                "click": {"output": "/actions/default/in/clickrightjoystick"}}},
    {"path": f"{L}/trigger", "mode": "trigger", "inputs": {"pull": {"output": "/actions/default/in/lefttrigger"}}},
    {"path": f"{R}/trigger", "mode": "trigger", "inputs": {"pull": {"output": "/actions/default/in/righttrigger"}}},
    button(f"{L}/bumper", "leftgrip"),    # -> pad LB (FrameVR_CS maps the grip actions to the bumpers)
    button(f"{R}/bumper", "rightgrip"),   # -> pad RB
    button(f"{R}/a", "buttona"),
    button(f"{R}/b", "buttonb"),
    button(f"{R}/x", "buttonx"),
    button(f"{R}/y", "buttony"),
    button(f"{L}/dpad_up", "northdpad"),
    button(f"{L}/dpad_down", "southdpad"),
    button(f"{L}/dpad_left", "westdpad"),
    button(f"{L}/dpad_right", "eastdpad"),
    button(f"{R}/menu", "start"),
    button(f"{L}/view", "back"),
]
touch = json.load(open(f"{SVR}/bindings_oculus_touch.json"))["bindings"]["/actions/default"]
binding = {
    "action_manifest_version": 0,
    "alias_info": {},
    "bindings": {"/actions/default": {
        "chords": [],
        "haptics": touch.get("haptics", []),
        "poses": touch.get("poses", []),
        "skeleton": touch.get("skeleton", []),
        "sources": sources,
    }},
    "category": "steamvr_input",
    "controller_type": "frame_controller",
    "description": "Steam Frame layout for Circuit Superstars VR = its Xbox layout: ABXY, triggers, bumpers LB/RB, sticks, d-pad, menu Start, view Back.",
    "name": "Circuit Superstars VR - Steam Frame",
    "options": {},
    "simulated_actions": [],
}
json.dump(binding, open(BINDING, "w"), indent=2)
print("wrote", BINDING)

actions_path = f"{SVR}/actions.json"
backup(actions_path)
actions = json.load(open(actions_path))
defaults = [d for d in actions["default_bindings"] if d["controller_type"] != "frame_controller"]
defaults.insert(0, {"controller_type": "frame_controller", "binding_url": "bindings_frame_controller.json"})
actions["default_bindings"] = defaults
json.dump(actions, open(actions_path, "w"), indent=2)
print("added frame_controller default binding to", actions_path)

backup(SETTINGS)
s = json.load(open(SETTINGS))
for app in APPS:
    sec = s.setdefault(app, {})
    for key in ("frame_controller_CurrentURL_steamvrinput", "frame_controller_250820_CurrentURL_steamvrinput"):
        sec[key] = "file://" + BINDING.replace(" ", "%20")
json.dump(s, open(SETTINGS, "w"), indent=3)
print("selected binding for", APPS)
