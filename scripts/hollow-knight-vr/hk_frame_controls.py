"""Steam Frame control scheme for Hollow Knight VR Enhanced (UnityVR_Bepinex + framepad, as DUSK HD VR).
Chain: Frame input -> SteamVR action (bindings_frame_controller.json) -> the mod's virtual Xbox pad (framepad stands in
for ViGEm; this core maps leftgrip->LB, rightgrip->RB, stick clicks->L3/R3) -> Hollow Knight's own gamepad defaults.
The Frame has every Xbox button, so this is Hollow Knight's official Xbox layout 1:1:

  A jump          B focus / cast       X attack         Y dream nail
  RT dash         LT super dash        RB quick cast    LB quick map
  left stick move, d-pad move/menus, menu = Start (pause), view = Back (inventory)   (FrameVR_HK plugin: Start/Back)
  grips unused; right stick click = R3; left stick click unbound (its action carries the d-pad touch, see dpad())
Run with the game closed; originals are kept as *.orig."""
import json, os, shutil

HOME = os.path.expanduser("~")
GAME = f"{HOME}/.local/share/Steam/steamapps/common/Hollow Knight"
SVR = f"{GAME}/hollow_knight_Data/StreamingAssets/SteamVR"
SETTINGS = f"{HOME}/.config/openvr/config/steamvr.vrsettings"
APP = "steam.app.2289186113"
BINDING = f"{SVR}/bindings_frame_controller.json"


def backup(path):
    if os.path.exists(path) and not os.path.exists(path + ".orig"):
        shutil.copy(path, path + ".orig")


def button(path, action):
    return {"path": path, "mode": "button", "inputs": {"click": {"output": f"/actions/default/in/{action}"}}}


# The Frame driver reports a held d-pad "click" as ~150 ms pulses that stop after ~1 s, and "touch" is one shared
# sensor (any direction fires all four) that does follow the thumb. So: click -> the direction action (the FrameVR_HK
# plugin latches it), touch -> clickleftjoystick, which the plugin reads as "thumb still on the d-pad" to keep the
# latched direction held. Hollow Knight never uses L3, and the stick's own click is left unbound to keep it clean.
def dpad(path, action):
    return {"path": path, "mode": "button",
            "inputs": {"click": {"output": f"/actions/default/in/{action}"},
                       "touch": {"output": "/actions/default/in/clickleftjoystick"}}}


L, R = "/user/hand/left/input", "/user/hand/right/input"
sources = [
    {"path": f"{L}/thumbstick", "mode": "joystick",
     "inputs": {"position": {"output": "/actions/default/in/leftjoystick"}}},
    {"path": f"{R}/thumbstick", "mode": "joystick",
     "inputs": {"position": {"output": "/actions/default/in/rightjoystick"},
                "click": {"output": "/actions/default/in/clickrightjoystick"}}},
    {"path": f"{L}/trigger", "mode": "trigger", "inputs": {"pull": {"output": "/actions/default/in/lefttrigger"}}},
    {"path": f"{R}/trigger", "mode": "trigger", "inputs": {"pull": {"output": "/actions/default/in/righttrigger"}}},
    button(f"{L}/bumper", "leftgrip"),    # -> pad LB (quick map): the mod maps the leftgrip action to LB
    button(f"{R}/bumper", "rightgrip"),   # -> pad RB (quick cast): rightgrip -> RB
    button(f"{R}/a", "buttona"),
    button(f"{R}/b", "buttonb"),
    button(f"{R}/x", "buttonx"),
    button(f"{R}/y", "buttony"),
    dpad(f"{L}/dpad_up", "northdpad"),
    dpad(f"{L}/dpad_down", "southdpad"),
    dpad(f"{L}/dpad_left", "westdpad"),
    dpad(f"{L}/dpad_right", "eastdpad"),
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
    "description": "Steam Frame layout for Hollow Knight VR = its Xbox layout: ABXY, triggers LT/RT, bumpers LB/RB, d-pad, menu Start, view Back.",
    "name": "Hollow Knight VR - Steam Frame",
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

cfg_path = f"{GAME}/BepInEx/config/UnityVR_Bepinex.cfg"
backup(cfg_path)
lines = open(cfg_path).read().split("\n")
lines = ["vrControllersSupport = true" if l.startswith("vrControllersSupport =") else l for l in lines]
open(cfg_path, "w").write("\n".join(lines))
print("vrControllersSupport = true")

backup(SETTINGS)
s = json.load(open(SETTINGS))
app = s.setdefault(APP, {})
for key in ("frame_controller_CurrentURL_steamvrinput", "frame_controller_250820_CurrentURL_steamvrinput"):
    app[key] = "file://" + BINDING.replace(" ", "%20")
json.dump(s, open(SETTINGS, "w"), indent=3)
print("selected binding for", APP)
