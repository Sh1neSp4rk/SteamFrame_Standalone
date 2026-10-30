"""SteamVR OpenXR binding for KHARVOX (DOOM 2016 VR, steam.app.379720) on the Steam Frame, with frame_doompad.

Goal: VR controls match flat DOOM's gamepad layout. KHARVOX keeps what needs motion awareness (move, turn, fire,
A/B with its menu routing, R3 melee+use, the grips for two-hand support and the shoulder weapon); the frame_doompad
layer's "framepad" set sends every other Xbox button straight to DOOM. KHARVOX's own equipment, pause, mission-info
and weapon-mod actions are left unbound because framepad sends LB, Start, Back and D-pad up 1:1 instead.
KHARVOX keeps its default "Swap jump/crouch" off. Frame A is framepad's plain Xbox A (jump, menu confirm); Frame B
drives KHARVOX's doom_crouch (so its camera follows the crouch) plus framepad's plain Xbox B, and the layer drops the
menu A that KHARVOX derives from crouch, so B goes back in menus.
Usage: python kharvox_binding.py OUT.json"""
import json, sys

K, F = "/actions/kharvox_gameplay/in/", "/actions/framepad/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"
FIRM = {"click_activate_threshold": "0.8", "click_deactivate_threshold": "0.7"}


def btn(path, output, extra=None):
    p = {"haptic_amplitude": 0, "force_input": "click"}
    p.update(extra or {})
    return {"path": path, "mode": "button", "inputs": {"click": {"output": output}}, "parameters": p}


kharvox = [
    # stick clicks live inside the joystick source (a separate button source on the same path is ignored)
    {"path": L + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": K + "doom_move"}}},
    {"path": R + "thumbstick", "mode": "joystick",
     "inputs": {"position": {"output": K + "doom_turn"}, "click": {"output": K + "doom_melee"}}},   # R3
    {"path": R + "trigger", "mode": "trigger", "inputs": {"pull": {"output": K + "doom_fire"}}},      # RT
    btn(R + "b", K + "doom_crouch"),     # B: crouch (KHARVOX camera); the plain Xbox B comes from framepad
    btn(L + "grip", K + "doom_support_grip", FIRM),          # VR: two-hand support, tap = equipment, hold = BFG
    btn(R + "grip", K + "doom_secondary_fire_grip", FIRM),   # VR: weapon mod in front, shoulder weapon behind
]
framepad = [
    {"path": L + "trigger", "mode": "trigger", "inputs": {"pull": {"output": F + "lt"}}},          # LT
    btn(R + "a", F + "a"),               # A: jump / confirm
    btn(R + "b", F + "b"),               # B: crouch / back
    btn(L + "bumper", F + "lb"),
    btn(R + "bumper", F + "rb"),
    btn(R + "x", F + "x"),
    btn(R + "y", F + "y"),
    btn(L + "view", F + "view"),
    btn(R + "menu", F + "menu"),
    btn(L + "dpad_up", F + "dpad_up"),
    btn(L + "dpad_down", F + "dpad_down"),
    btn(L + "dpad_left", F + "dpad_left"),
    btn(L + "dpad_right", F + "dpad_right"),
    {"path": L + "thumbstick", "mode": "joystick", "inputs": {"click": {"output": F + "l3"}}},     # L3
]
binding = {
    "name": "KHARVOX DOOM VR - Steam Frame (matches flat gamepad)",
    "description": "Each Frame button does what the same Xbox button does in flat DOOM: RT fire, LT weapon mod, "
                   "LB equipment, RB change weapon (hold: wheel with the right stick), A jump, B crouch, X chainsaw, "
                   "Y BFG, R3 melee/use, View dossier, Menu pause, D-pad as flat. Right stick turns. Grips: two-hand "
                   "support and shoulder weapon.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {
        "/actions/kharvox_gameplay": {
            "chords": [], "eyetracking": [],
            "haptics": [{"output": f"/actions/kharvox_gameplay/out/{h}_haptic", "path": f"/user/hand/{h}/output/haptic"}
                        for h in ("left", "right")],
            "poses": [{"output": K + f"{h}_{k}_pose", "path": f"/user/hand/{h}/pose/openxr_{k}"}
                      for h in ("right", "left") for k in ("aim", "grip")],
            "sources": kharvox},
        "/actions/framepad": {"chords": [], "eyetracking": [], "haptics": [], "poses": [], "sources": framepad},
    },
}
json.dump(binding, open(sys.argv[1], "w"), indent=2)
print("wrote", sys.argv[1])
