"""SteamVR OpenXR binding for Halo MCC VR (MCCVR mod, app 976730) on the Steam Frame.

Goal: VR controls match flat. Flat MCC sees the Frame as an Xbox pad (Steam Input, 1:1), and each Halo title applies
its own MCC button layout. The mod turns its OpenXR actions into that same virtual Xbox pad (btn_a -> A, trigger_l ->
LT, grip_l -> LB, grip_r -> RB, click_l -> L3, menu -> Start), so binding each Frame input to the action that produces
the same Xbox button makes every title follow its flat layout. The right stick turns instead of looking (VR).
The mod has no d-pad or Back action; the framexr layer (framexr/) adds a "framepad" action set for them, which the
layer turns into real XInput Back / D-pad bits, so View and the d-pad also match flat.
Grips also drive LB/RB, as they do in the mod's own layout (support grip = two-hand aim + LB).
"""
import json, os, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/PCVR/HaloMCCVR/mcc_frame_binding.json")
A = "/actions/gameplay/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"
FIRM = {"click_activate_threshold": "0.8", "click_deactivate_threshold": "0.7", "haptic_amplitude": 0}

def btn(path, action, extra=None):
    p = {"haptic_amplitude": 0, "force_input": "click"}
    p.update(extra or {})
    return {"path": path, "mode": "button", "inputs": {"click": {"output": A + action}}, "parameters": p}

def pull(path, action):
    return {"path": path, "mode": "trigger", "inputs": {"pull": {"output": A + action}}}

sources = [
    # Stick clicks live inside the joystick source (a separate button source on the same path never reached
    # the mod: L3+R3 for the mod menu did nothing).
    {"path": L + "thumbstick", "mode": "joystick",
     "inputs": {"position": {"output": A + "move"}, "click": {"output": A + "click_l"}}},   # L3
    {"path": R + "thumbstick", "mode": "joystick",
     "inputs": {"position": {"output": A + "turn"}, "click": {"output": A + "click_r"}}},   # R3
    pull(L + "trigger", "trigger_l"),          # LT
    pull(R + "trigger", "trigger_r"),          # RT
    btn(L + "bumper", "grip_l"),               # LB
    btn(R + "bumper", "grip_r"),               # RB
    btn(L + "grip", "grip_l", FIRM),           # VR support grip (also LB in the mod), 80%
    btn(R + "grip", "grip_r", FIRM),           # VR weapon grip (also RB in the mod), 80%
    btn(R + "a", "btn_a"),
    btn(R + "b", "btn_b"),
    btn(R + "x", "btn_x"),
    btn(R + "y", "btn_y"),
    btn(R + "menu", "menu"),                   # Start
]
binding = {
    "name": "Halo MCC VR - Steam Frame (matches flat)",
    "description": "Each Frame button sends the same Xbox button as in flat play: triggers LT/RT, bumpers LB/RB, A/B/X/Y, "
                   "stick clicks L3/R3, menu Start, View Back, d-pad d-pad. Right stick turns.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {"/actions/gameplay": {
        "chords": [], "eyetracking": [],
        "haptics": [{"output": "/actions/gameplay/out/game_haptics", "path": f"/user/hand/{h}/output/haptic"} for h in ("left", "right")],
        "poses": [{"output": A + f"{h}_aim_pose", "path": f"/user/hand/{h}/pose/openxr_aim"} for h in ("left", "right")]
               + [{"output": A + "two_hand_grip_pose", "path": f"/user/hand/{h}/pose/openxr_grip"} for h in ("left", "right")],  # 0.7.0+
        "sources": sources},
        "/actions/framepad": {"chords": [], "eyetracking": [], "haptics": [], "poses": [], "sources": [
            {"path": L + "view", "mode": "button", "inputs": {"click": {"output": "/actions/framepad/in/view"}},
             "parameters": {"haptic_amplitude": 0, "force_input": "click"}}] + [
            {"path": L + "dpad_" + d, "mode": "button", "inputs": {"click": {"output": "/actions/framepad/in/dpad_" + d}},
             "parameters": {"haptic_amplitude": 0, "force_input": "click"}} for d in ("up", "down", "left", "right")]}},
}
json.dump(binding, open(OUT, "w"), indent=2)
print("wrote", OUT)
