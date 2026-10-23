"""SteamVR OpenXR binding for Quake II VR (native, steam.app.3173477041) on the Steam Frame, then select it.
Left hand carries all movement:  stick move, grip run, trigger crouch, bumper jump, d-pad left/right = help /
inventory (X/Y), view = menu.  Right hand: trigger fire, A crouch, B jump, stick turn/weapons, grip = the game's
dominant-grip functions, menu = menu.  Grips need an 80% squeeze (standard Frame layout)."""
import json, os, subprocess

OUT = os.path.expanduser("~/PCVR/Quake2VR-game/q2vr_frame_binding.json")
APP = "steam.app.3173477041"
A = "/actions/gameplay/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"
FIRM = {"click_activate_threshold": "0.8", "click_deactivate_threshold": "0.7", "haptic_amplitude": 0}

def btn(path, action, extra=None):
    p = {"haptic_amplitude": 0, "force_input": "click"}
    p.update(extra or {})
    return {"path": path, "mode": "button", "inputs": {"click": {"output": A + action}}, "parameters": p}

sources = []
for H in (L, R):
    sources += [
        {"path": H + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "thumbstick"}}},
        btn(H + "thumbstick", "thumbstick_click"),
        {"path": H + "thumbstick", "mode": "button", "inputs": {"touch": {"output": A + "thumbstick_touch"}},
         "parameters": {"haptic_amplitude": 0}},
    ]
sources += [
    # left hand: movement
    {"path": L + "grip", "mode": "button", "inputs": {"click": {"output": A + "trigger"}}, "parameters": FIRM},  # run
    {"path": L + "trigger", "mode": "trigger", "inputs": {"pull": {"output": A + "squeeze"}}},                  # crouch
    btn(L + "bumper", "b_click"),                                                                               # jump
    btn(L + "dpad_left", "x_click"),     # help computer
    btn(L + "dpad_right", "y_click"),    # inventory mode (hold)
    btn(L + "view", "menu_click"),
    # right hand
    {"path": R + "trigger", "mode": "button", "inputs": {"click": {"output": A + "trigger"}}, "parameters": {"haptic_amplitude": 0}},
    {"path": R + "grip", "mode": "trigger", "inputs": {"pull": {"output": A + "squeeze"}}},
    btn(R + "a", "a_click"),
    btn(R + "b", "b_click"),
    btn(R + "menu", "menu_click"),
]
binding = {
    "name": "Quake II VR - Steam Frame layout",
    "description": "Left hand: stick move, grip run, trigger crouch, bumper jump, d-pad left/right help/inventory, view menu. "
                   "Right: trigger fire, A crouch, B jump, stick turn + weapons, menu.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {"/actions/gameplay": {
        "chords": [], "eyetracking": [],
        "haptics": [{"output": "/actions/gameplay/out/haptic", "path": f"/user/hand/{h}/output/haptic"} for h in ("left", "right")],
        "poses": [{"output": f"/actions/gameplay/in/{p}", "path": f"/user/hand/{h}/pose/openxr_aim"}
                  for p in ("grip_pose", "aim_pose") for h in ("left", "right")],
        "sources": sources}},
}
json.dump(binding, open(OUT, "w"), indent=2)
print("wrote", OUT)
for key in ("frame_controller_CurrentURL_openxr", "frame_controller_250820_CurrentURL_openxr"):
    r = subprocess.run(["/opt/steamvr/bin/linuxarm64/vrcmd", "--set-settings-string", f"{APP}/{key}", "file://" + OUT],
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip())
