"""Steam Frame control scheme for DUSK HD VR (Dusk_HD_VR + ~/PCVR/DuskHDVR/FrameVR_DuskHD.dll).
Chain: Frame button -> SteamVR action (bindings_frame_controller.json) -> virtual Xbox pad (the mod, which
swaps LB->RB, R3->LB, RB->R3) -> DUSK action (mappings/default.ini, preset 0).

  right trigger  fire                 left trigger   alt fire (zoom)
  left bumper    jump                 right bumper   use
  right A        crouch               right B        quick melee
  right X        flashlight           right Y        jump
  left grip      tap: last weapon, hold + right stick: weapon wheel (the mod frees right stick up/down
                 only while the left grip action is held)
  left stick     move (head-oriented) right stick    turn
  left click     walk                 right click    (both sticks together: recenter)
  left d-pad     up quick load, down quick save, left/right prev/next weapon
  menu (right)   pause menu           view (left)    stats / back
The right grip is unused. Run with the game closed; originals are kept as *.orig.
Also sets the VR rig scale (VRCamScale) so DUSK's oversized world reads closer to real size."""
import json, os, shutil

HOME = os.path.expanduser("~")
GAME = f"{HOME}/.local/share/Steam/steamapps/common/Dusk/DLC/DUSK HD"
SETTINGS = f"{HOME}/.config/openvr/config/steamvr.vrsettings"
APP = "steam.app.519860"
BINDING = f"{GAME}/bindings_frame_controller.json"


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
    # -> pad RB -> last used weapon / weapon wheel; needs a firm 80% squeeze so holding the controller doesn't fire it
    {"path": f"{L}/grip", "mode": "trigger",
     "parameters": {"click_activate_threshold": "0.8", "click_deactivate_threshold": "0.7"},
     "inputs": {"click": {"output": "/actions/default/in/leftgrip"}}},
    button(f"{L}/bumper", "buttony"),     # -> pad Y -> jump
    button(f"{R}/bumper", "rightgrip"),   # -> pad R3 -> use
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

# Keep the hand pose / skeleton / haptic setup SteamVR has been using (converted from the Touch binding).
touch = json.load(open(f"{GAME}/bindings_oculus_touch.json"))["bindings"]["/actions/default"]
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
    "description": "Steam Frame layout for DUSK HD VR: bumpers jump/use, ABXY crouch/melee/flashlight/last weapon, menu pauses, grips unused.",
    "name": "DUSK HD VR - Steam Frame",
    "options": {},
    "simulated_actions": [],
}
json.dump(binding, open(BINDING, "w"), indent=2)
print("wrote", BINDING)

actions_path = f"{GAME}/actions.json"
backup(actions_path)
actions = json.load(open(actions_path))
defaults = [d for d in actions["default_bindings"] if d["controller_type"] != "frame_controller"]
defaults.insert(0, {"controller_type": "frame_controller", "binding_url": "bindings_frame_controller.json"})
actions["default_bindings"] = defaults
json.dump(actions, open(actions_path, "w"), indent=2)
print("added frame_controller default binding to", actions_path)

mapping = f"{GAME}/mappings/default.ini"
backup(mapping)
open(mapping, "w").write("""[SETTINGS]
; ds4 or xbox360
controllermode = xbox360

; Steam Frame VR layout (written by ~/PCVR/DuskHDVR/dusk_frame_controls.py; original in default.ini.orig).
; The VR mod swaps pad buttons: Frame left grip arrives as rightShoulder, right bumper as rightStickButton,
; right stick click as leftShoulder; left bumper and right Y both send buttonNorth.
[BINDINGS]
rightTrigger = fire
leftTrigger = zoom
rightShoulder = last_used_weapon
rightStickButton = use
buttonSouth = crouch
buttonEast = quick_melee
buttonWest = flashlight
buttonNorth = jump
leftStickButton = walk
selectButton = toggle_stats
dpadUp = quick_load
dpadDown = quick_save
dpadLeft = prev_weapon
dpadRight = next_weapon
""")
print("wrote", mapping)

# DUSK's player is 2 units tall (eyes ~1.9) but its levels are built oversized, so at 1:1 the world looks
# too big and stereo depth too shallow. Scaling the VR rig widens the eye separation to match.
VRCAM_SCALE = "1.35"
cfg_path = f"{GAME}/BepInEx/config/UnityVR_Bepinex.cfg"
backup(cfg_path)
lines = open(cfg_path).read().split("\n")
lines = [f"VRCamScale = {VRCAM_SCALE},{VRCAM_SCALE},{VRCAM_SCALE}" if l.startswith("VRCamScale =") else l for l in lines]
open(cfg_path, "w").write("\n".join(lines))
print("VRCamScale =", VRCAM_SCALE)

backup(SETTINGS)
s = json.load(open(SETTINGS))
app = s.setdefault(APP, {})
for key in ("frame_controller_CurrentURL_steamvrinput", "frame_controller_250820_CurrentURL_steamvrinput"):
    app[key] = "file://" + BINDING.replace(" ", "%20")
json.dump(s, open(SETTINGS, "w"), indent=3)
print("selected binding for", APP)
