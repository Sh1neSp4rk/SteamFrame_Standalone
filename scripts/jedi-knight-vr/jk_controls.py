#!/usr/bin/env python3
"""Frame bindings for Jedi Academy VR (steam.app.2265637930) and Jedi Outcast VR (steam.app.2719912217), native JKXRL.

Every Frame input goes to its own OpenXR action (the engine port adds frame_bumper, frame_dpad_*, frame_view,
frame_x, frame_y); the client then rebuilds JKXR's Touch-style controls from them (cl_main.cpp CL_FrameLayoutTranslate,
vr_frame_layout 1). Written OVER SteamVR's read-only auto-generated Touch default, so SteamVR loads it on the next app
start without a SteamVR restart. SteamVR must already know every action named here: after engine changes that add
actions, run jk_rebind.sh (delete default, start once, then this)."""
import json, os, shutil, stat, sys

APPS = {"jka": "steam.app.2265637930", "jko": "steam.app.2719912217"}
CFG = os.path.expanduser("~/.config/openvr/config/openxr")
SET = "/actions/jkxr_gameplay"
A = SET + "/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"

def btn(path, action):
    return {"path": path, "mode": "button", "inputs": {"click": {"output": A + action}},
            "parameters": {"force_input": "click", "haptic_amplitude": 0}}

sources = []
for H in (L, R):
    sources += [
        {"path": H + "trigger", "mode": "trigger",
         # no trigger_click: only the (dropped) simple profile suggests it, and SteamVR rejects unknown actions;
         # the engine counts a pull above 0.5 as a click anyway
         "inputs": {"pull": {"output": A + "trigger"}, "touch": {"output": A + "trigger_touch"}}},
        {"path": H + "grip", "mode": "trigger", "inputs": {"pull": {"output": A + "squeeze"}}},
        {"path": H + "thumbstick", "mode": "joystick",
         "inputs": {"position": {"output": A + "thumbstick"}, "click": {"output": A + "thumbstick_click"},
                    "touch": {"output": A + "thumbstick_touch"}}},
        btn(H + "bumper", "frame_bumper"),
    ]
sources += [
    btn(R + "a", "primary_button"), btn(R + "b", "secondary_button"),
    btn(R + "x", "frame_x"), btn(R + "y", "frame_y"), btn(R + "menu", "menu"),
    btn(L + "dpad_up", "frame_dpad_up"), btn(L + "dpad_down", "frame_dpad_down"),
    btn(L + "dpad_left", "frame_dpad_left"), btn(L + "dpad_right", "frame_dpad_right"),
    btn(L + "view", "frame_view"),
]
binding = {
    "name": "JKXR (Jedi Knight) - Steam Frame layout",
    "description": "R: trigger fire/saber, bumper alt-fire, grip weapon wheel, A use, B Force wheel, X saber style, "
                   "Y console, stick turn, click next item, menu. L: trigger crouch, bumper jump, grip use Force, "
                   "stick move, click use item, view datapad, d-pad quick save/load, Force prev/next.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {SET: {
        "chords": [], "eyetracking": [],
        "haptics": [{"output": SET + "/out/haptic", "path": f"/user/hand/{h}/output/haptic"} for h in ("left", "right")],
        "poses": [{"output": A + "aim_pose", "path": f"/user/hand/{h}/pose/openxr_aim"} for h in ("left", "right")]
               + [{"output": A + "grip_pose", "path": f"/user/hand/{h}/pose/openxr_grip"} for h in ("left", "right")],
        "sources": sources}},
}

for key in (sys.argv[1:] or APPS):
    app = APPS[key]
    target = os.path.join(CFG, app + "_oculus_touch_0_binding.json")
    if os.path.exists(target):
        if not os.path.exists(target + ".orig"):
            shutil.copy(target, target + ".orig")
        known = json.load(open(target))
        names = {v["output"].rsplit("/", 1)[1] for b in known["bindings"].values()
                 for s in b.get("sources", []) for v in s["inputs"].values()}
        mine = {v["output"].rsplit("/", 1)[1] for s in sources for v in s["inputs"].values()}
        missing = sorted(mine - names)
        if missing and known.get("controller_type") != "frame_controller":
            print(f"{key}: SteamVR's default lacks {missing}; run jk_rebind.sh"); continue
        os.chmod(target, 0o644)
    json.dump(binding, open(target, "w"), indent=2)
    os.chmod(target, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    json.dump(binding, open(os.path.expanduser(f"~/PCVR/JKXR/{key}/jkxr_frame_binding.json"), "w"), indent=2)
    print(f"{key}: {target} (read-only)")
