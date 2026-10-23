#!/usr/bin/env python3
"""Standard Frame layout for Counter-Strike VR (native CSVR build, steam.app.3307658986).

Two parts:
 1. A frame_controller binding for the app's OpenXR actions (running_action_set; the engine port adds bumper_left,
    bumper_right and view_button). SteamVR only offers its auto-generated Touch default for this app, so the Frame
    binding is written OVER that file and made read-only: SteamVR logs "Unable to write" and loads ours on the next
    app start, no SteamVR restart needed (same trick as Unreal Revived).
 2. cstrike/frame_controls.cfg: what each button does (the engine maps buttons to console commands through vr_button_*
    variables). csvr-run.sh execs it at every launch, so menu changes to those variables don't stick.

Layout (user rules: L bumper jump, L trigger crouch, R trigger fire, R bumper secondary, menu pause, grips at 80%):
  Right: trigger fire, bumper secondary fire (scope / silencer / burst), A use (defuse, hostages), B reload, X buy menu,
         Y drop weapon, stick left/right snap turn, up/down weapons, stick click flashlight, menu = menu.
         Grip (80%) last weapon.
  Left:  trigger crouch, bumper jump, stick move, stick click night vision, view = scoreboard, grip (80%) walk (hold),
         d-pad up/down primary/secondary ammo, left spray, right team menu (tap: the Frame d-pad repeats when held).
SteamVR must already know every action named here (it learns them from the game's suggested bindings): after an engine
change that adds actions, delete the default file, start the game once so SteamVR regenerates it, then run this again.
"""
import json, os, shutil, stat

APP = "steam.app.3307658986"
CFG_DIR = os.path.expanduser("~/.config/openvr/config/openxr")
TARGET = os.path.join(CFG_DIR, APP + "_oculus_touch_0_binding.json")
GAME = os.path.expanduser("~/PCVR/CSVR/game")
A = "/actions/running_action_set/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"

def btn(path, action):
    return {"path": path, "mode": "button", "inputs": {"click": {"output": A + action}},
            "parameters": {"force_input": "click", "haptic_amplitude": 0}}

def pull(path, action):
    return {"path": path, "mode": "trigger", "inputs": {"pull": {"output": A + action}}}

sources = [
    {"path": L + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "move_on_left_joy"}}},
    {"path": R + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "move_on_right_joy"}}},
    btn(L + "thumbstick", "thumbstick_left"),
    btn(R + "thumbstick", "thumbstick_right"),
    btn(R + "trigger", "index_right"),     # fire; also the menu pointer's click
    btn(L + "trigger", "index_left"),      # crouch
    btn(L + "bumper", "bumper_left"),      # jump
    btn(R + "bumper", "bumper_right"),     # secondary fire
    btn(R + "a", "button_a"),              # use
    btn(R + "b", "button_b"),              # reload
    btn(R + "x", "button_x"),              # buy menu
    btn(R + "y", "button_y"),              # drop
    btn(R + "menu", "menu_action"),        # menu / pause (Escape)
    btn(L + "view", "view_button"),        # scoreboard
    btn(L + "dpad_up", "dpad_up"),         # primary ammo
    btn(L + "dpad_down", "dpad_down"),     # secondary ammo
    btn(L + "dpad_left", "dpad_left"),     # spray
    btn(L + "dpad_right", "dpad_right"),   # team menu
    pull(L + "grip", "grip_left"),         # walk (engine counts 80% as pressed)
    pull(R + "grip", "grip_right"),        # last weapon
]
binding = {
    "name": "Counter-Strike VR - Steam Frame layout",
    "description": "R: trigger fire, bumper secondary, A use, B reload, X buy, Y drop, grip last weapon, stick turn/weapons, "
                   "click flashlight, menu. L: trigger crouch, bumper jump, grip walk, stick move, click night vision, "
                   "view scoreboard, d-pad ammo/ammo/spray/team.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {"/actions/running_action_set": {
        "chords": [], "eyetracking": [],
        "haptics": [{"output": "/actions/running_action_set/out/vibrate_left_feedback", "path": "/user/hand/left/output/haptic"},
                    {"output": "/actions/running_action_set/out/vibrate_right_feedback", "path": "/user/hand/right/output/haptic"}],
        "poses": [{"output": A + "hand_pose_left", "path": "/user/hand/left/pose/openxr_aim"},
                  {"output": A + "hand_pose_right", "path": "/user/hand/right/pose/openxr_aim"}],
        "sources": sources}},
}

os.makedirs(CFG_DIR, exist_ok=True)
if os.path.exists(TARGET):
    if not os.path.exists(TARGET + ".orig"):
        shutil.copy(TARGET, TARGET + ".orig")
    os.chmod(TARGET, 0o644)
json.dump(binding, open(TARGET, "w"), indent=2)
os.chmod(TARGET, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)      # read-only: SteamVR can't replace it
json.dump(binding, open(os.path.join(GAME, "csvr_frame_binding.json"), "w"), indent=2)
print("binding:", TARGET, "(read-only)")

cfg = """// Steam Frame standard layout for Counter-Strike VR. Exec'd by csvr-run.sh at every launch (edit here, not in the menu).
vr_button_alt ""
vr_button_trigger_right "+attack"
vr_button_bumper_right "+attack2"
vr_button_a "+use"
vr_button_b "+reload"
vr_button_x "buy"
vr_button_y "drop"
vr_button_thumbstick_press_right "impulse 100"
vr_button_thumbstick_dleft_right "+vr_left"
vr_button_thumbstick_dright_right "+vr_right"
vr_button_thumbstick_dup_right "+vr_weapon_prev"
vr_button_thumbstick_ddown_right "+vr_weapon_next"
vr_button_trigger_left "+duck"
vr_button_bumper_left "+jump"
vr_button_thumbstick_press_left "nightvision"
vr_button_view "+vr_scoreboard"
vr_button_grip_left "+speed"
vr_button_grip_right "lastinv"
vr_button_dpad_up "buyammo1"
vr_button_dpad_down "buyammo2"
vr_button_dpad_left "impulse 201"
vr_button_dpad_right "chooseteam"
"""
open(os.path.join(GAME, "cstrike/frame_controls.cfg"), "w").write(cfg)
print("config:", os.path.join(GAME, "cstrike/frame_controls.cfg"))
