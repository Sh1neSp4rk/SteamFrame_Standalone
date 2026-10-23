"""SteamVR OpenXR binding for Quake VR (Team Beef) (native Quake-PCVR, steam.app.2316100907) on the Steam Frame:
the standard Frame layout (~/PCVR/FRAME-LAYOUT.md) mapped onto Team Beef's Touch-controller semantics. The action
names are the app's own (as SteamVR's auto default ~/.config/openvr/config/openxr/steam.app.2316100907_oculus_touch_0_
binding.json lists them): joystick, touchpad (stick click), rockertouch, trigger, gripvalue, akey/bkey/xkey/ykey, backkey.
Left hand: stick move, trigger = run (dash; Quake has no crouch for the trigger slot), grip (80%) = two-hand weapon
hold, bumper = jump, d-pad up/down = quick save/load (their X/Y), view = menu.
Right hand: trigger fire, grip (80%) = weapon wheel (hold, point, release), A = jump, Y = jump, B = menu back,
stick = snap turn (and weapon prev/next when the wheel is off), stick click = laser sight cycle, menu = menu.
Writes the JSON; vrsettings_bind.py persists the selection in steamvr.vrsettings."""
import json, os

OUT = os.path.expanduser("~/PCVR/QuakePCVR-game/q1pc_frame_binding.json")
A = "/actions/gameplay/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"
FIRM = {"click_activate_threshold": "0.8", "click_deactivate_threshold": "0.7", "haptic_amplitude": 0}

def btn(path, action, extra=None):
    p = {"haptic_amplitude": 0, "force_input": "click"}
    p.update(extra or {})
    return {"path": path, "mode": "button", "inputs": {"click": {"output": A + action}}, "parameters": p}

def pull(path, action):
    return {"path": path, "mode": "trigger", "inputs": {"pull": {"output": A + action}}}

def firm(path, action):  # a grip as a button at an 80% squeeze (trigger mode honours the click thresholds)
    return {"path": path, "mode": "trigger", "inputs": {"click": {"output": A + action}}, "parameters": FIRM}

sources = []
for H in (L, R):
    sources += [
        {"path": H + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "joystick"}},
         "parameters": {"deadzone_pct": "10"}},
        btn(H + "thumbstick", "touchpad"),                                                        # stick click
        {"path": H + "thumbstick", "mode": "button", "inputs": {"touch": {"output": A + "rockertouch"}},
         "parameters": {"haptic_amplitude": 0}},
    ]
sources += [
    # left hand: movement
    pull(L + "trigger", "trigger"),                                                                               # run (their off-hand trigger)
    firm(L + "grip", "gripvalue"),                                                                                # two-hand weapon hold (their off-hand grip)
    btn(L + "bumper", "akey"),           # jump (their A)
    btn(L + "dpad_up", "xkey"),          # quick save (their X)
    btn(L + "dpad_down", "ykey"),        # quick load (their Y)
    btn(L + "view", "backkey"),          # menu (their menu button)
    # right hand: aim, fire, turn
    pull(R + "trigger", "trigger"),                                                                               # fire
    firm(R + "grip", "gripvalue"),                                                                                # weapon wheel (their dominant grip)
    btn(R + "a", "akey"),                # jump (no crouch in Quake)
    btn(R + "b", "bkey"),                # menu back
    btn(R + "y", "akey"),                # jump (duplicate)
    btn(R + "menu", "backkey"),          # menu
]
binding = {
    "name": "Quake VR (Team Beef) - Steam Frame layout",
    "description": "Left: stick move, trigger run, grip two-hand hold, bumper jump, d-pad up/down quick save/load, view menu. "
                   "Right: trigger fire, grip weapon wheel, A/Y jump, B back, stick snap turn, stick click laser sight, menu.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {"/actions/gameplay": {
        "chords": [], "eyetracking": [],
        "haptics": [{"output": "/actions/gameplay/out/vibrate_hand", "path": f"/user/hand/{h}/output/haptic"} for h in ("left", "right")],
        "poses": [{"output": A + "hand_pose", "path": f"/user/hand/{h}/pose/openxr_grip"} for h in ("left", "right")]
               + [{"output": A + "aim_pose", "path": f"/user/hand/{h}/pose/openxr_aim"} for h in ("left", "right")],
        "sources": sources}},
}
json.dump(binding, open(OUT, "w"), indent=2)
print("wrote", OUT)
