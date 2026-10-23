"""SteamVR OpenXR binding for Red Faction VR (Alpine Faction VR, shortcut steam.app.3865968601) on the Steam Frame.

Needs the Frame-patched AlpineFaction.dll (rf_patch.py: jump/crouch/reload/flashlight/menu/alt-fire actions accept either
hand; the menu action pauses on SteamVR). SteamVR only honours a Frame-path custom file for this Proton/wineopenxr app
when its XR input context holds a single interaction profile, so rf_launch.sh keeps the app's Index default unwritable.

Layout (Frame standard):
  Right - trigger fire, bumper alt-fire, A laser sight, B reload, X flashlight, menu pause (Esc),
          stick turn + weapon cycle, stick click recenter, grip (80%) = mod's alt-fire modifier. Y free.
  Left  - trigger crouch, bumper jump, grip (80%) use / two-hand grab, stick move, stick click holster.
          View and d-pad free (the mod has no further actions).
"""
import json, os

OUT = os.path.expanduser("~/PCVR/RedFactionVR/rf_frame_binding.json")
A = "/actions/gameplay/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"
FIRM = {"click_activate_threshold": "0.8", "click_deactivate_threshold": "0.7", "haptic_amplitude": 0}

def btn(path, action, extra=None):
    p = {"haptic_amplitude": 0, "force_input": "click"}
    p.update(extra or {})
    return {"path": path, "mode": "button", "inputs": {"click": {"output": A + action}}, "parameters": p}

sources = [
    {"path": L + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "left_thumbstick"}}},
    btn(L + "thumbstick", "left_thumbstick_click"),            # holster (mod)
    {"path": R + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "right_thumbstick"}}},
    btn(R + "thumbstick", "recenter"),                         # Frame: recenter (patched-in action)
    {"path": L + "trigger", "mode": "trigger", "inputs": {"click": {"output": A + "crouch"}},
     "parameters": {"haptic_amplitude": 0}},                   # Frame: crouch on the left trigger
    btn(L + "bumper", "jump"),                                 # Frame: jump on the left bumper
    btn(L + "grip", "grip", FIRM),                             # use / two-hand grab, 80% squeeze
    {"path": R + "trigger", "mode": "trigger", "inputs": {"pull": {"output": A + "right_trigger"}}},   # fire
    btn(R + "bumper", "left_trigger"),                         # alt-fire (the mod's Index-layout action)
    btn(R + "grip", "grip", FIRM),                             # right grip + trigger = alt-fire (mod), 80%
    btn(R + "a", "right_thumbstick_click"),                    # laser sight toggle (the mod's stick-click function)
    btn(R + "b", "reload"),
    btn(R + "x", "flashlight"),
    btn(R + "menu", "menu"),                                   # pause (Esc); Y, view and the d-pad stay free
]
binding = {
    "name": "Red Faction VR - Steam Frame layout",
    "description": "Right: trigger fire, bumper alt-fire, A crouch, B reload, X flashlight, Y jump, menu pause, stick turn/weapons, "
                   "click laser, grip alt-fire modifier. Left: trigger crouch, bumper jump, grip use/two-hand, d-pad up flashlight, view pause.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {"/actions/gameplay": {
        "chords": [], "eyetracking": [], "haptics": [],
        "poses": [{"output": A + "grip_pose", "path": f"/user/hand/{h}/pose/openxr_grip"} for h in ("left", "right")]
               + [{"output": A + "aim_pose", "path": f"/user/hand/{h}/pose/openxr_aim"} for h in ("left", "right")],
        "sources": sources}},
}
json.dump(binding, open(OUT, "w"), indent=2)
print("wrote", OUT)
