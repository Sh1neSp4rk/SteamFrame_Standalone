#!/usr/bin/env python3
"""Standard Frame layout for Deus Ex HR DC VR (DeusExHRVR 0.3.0 under Proton, steam.app.238010).

DeusExHRVR's OpenXR actions (set /actions/motion_controller) are NOT hand-scoped, so any Frame input can drive any of
them; DeusExHRVR.ini [Buttons]/[ScreenButtons] then pick the Xbox button each one sends (the game's prompts show Xbox
glyphs). The game suggests Touch + simple profiles; SteamVR only honours a custom Frame binding with ONE profile in
play, so the simple default is locked as '{}' and the Frame binding is written over the read-only Touch default.

Gameplay (Xbox action in brackets):
  R trigger fire (RT)   R bumper interact/reload (X)   B takedown (B)   Y holster / hold: quick inventory (Y)
  R grip 80% grenade (RB)   R stick aim, click iron sight/scope (RS; hold + left stick = augment d-pad)
  L trigger crouch (LS)  L bumper jump (A)   L grip cover (LT)   L stick move, click sprint (LB)
  Menu: tap = in-game menu (Back), hold 1.5 s = pause (Start)   [the mod's own menu-button logic]
Menus: R trigger select (A), B back, Y/X as labelled, L bumper also A.
Frame A, X, view and the d-pad have no DeusExHRVR action left (it reads eleven Touch inputs).
"""
import json, os, re, shutil, stat

APP = "steam.app.238010"
CFG = os.path.expanduser("~/.config/openvr/config/openxr")
SET = "/actions/motion_controller"
A = SET + "/in/"
L, R = "/user/hand/left/input/", "/user/hand/right/input/"

def btn(path, action):
    return {"path": path, "mode": "button", "inputs": {"click": {"output": A + action}},
            "parameters": {"force_input": "click", "haptic_amplitude": 0}}

def pull(path, action):
    return {"path": path, "mode": "trigger", "inputs": {"pull": {"output": A + action}}}

sources = [
    {"path": L + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "left_stick"}}},
    {"path": R + "thumbstick", "mode": "joystick", "inputs": {"position": {"output": A + "right_stick"}}},
    pull(R + "trigger", "right_trigger"),   # RT fire
    pull(L + "trigger", "left_trigger"),    # -> LS crouch (ini)
    pull(L + "grip", "left_grip"),          # -> LT cover (ini)
    pull(R + "grip", "right_grip"),         # RB grenade
    btn(L + "bumper", "button_a"),          # A jump
    btn(R + "bumper", "button_x"),          # X interact / reload
    btn(R + "b", "button_b"),               # B takedown
    btn(R + "y", "button_y"),               # Y holster / quick inventory
    btn(L + "thumbstick", "left_click"),    # -> LB sprint (ini)
    btn(R + "thumbstick", "right_click"),   # RS iron sight / scope; chord modifier for augment d-pad
    btn(R + "menu", "menu"),                # tap Back (in-game menu), hold Start (pause)
]
binding = {
    "name": "Deus Ex HR DC VR - Steam Frame layout",
    "description": "R: trigger fire, bumper interact/reload, B takedown, Y holster/inventory, grip grenade, stick click "
                   "scope, menu (tap in-game menu, hold pause). L: trigger crouch, bumper jump, grip cover, stick click sprint.",
    "controller_type": "frame_controller", "category": "openxr",
    "interaction_profile": "/interaction_profiles/oculus/touch_controller",
    "options": {"mirror_actions": False},
    "bindings": {SET: {"chords": [], "eyetracking": [], "haptics": [],
                       "poses": [{"output": A + "right_weapon_aim", "path": "/user/hand/right/pose/openxr_aim"}],
                       "sources": sources}},
}

touch = os.path.join(CFG, APP + "_oculus_touch_0_binding.json")
simple = os.path.join(CFG, APP + "_khr_simple_controller_1_binding.json")
for p in (touch, simple):
    if os.path.exists(p):
        if not os.path.exists(p + ".orig"):
            shutil.copy(p, p + ".orig")
        os.chmod(p, 0o644)
json.dump(binding, open(touch, "w"), indent=2)
open(simple, "w").write("{}")
for p in (touch, simple):
    os.chmod(p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
print("binding:", touch, "(read-only); simple profile locked empty")

# DeusExHRVR.ini: gameplay and screen button maps
G = [d for d in os.listdir(os.path.expanduser("~/.local/share/Steam/steamapps/common")) if d.startswith("Deus Ex Human")][0]
ini = os.path.expanduser(f"~/.local/share/Steam/steamapps/common/{G}/DeusExHRVR.ini")
if not os.path.exists(ini + ".bak-frame"):
    shutil.copy(ini, ini + ".bak-frame")
text = open(ini).read()
buttons = ("[Buttons]\n; Steam Frame layout (dx_controls.py); Frame input in brackets\n"
           "RightA=A\n; [L bumper] jump\nRightB=B\n; [B] takedown\nLeftX=X\n; [R bumper] interact / reload\n"
           "LeftY=Y\n; [Y] holster / quick inventory\nLeftGrip=LT\n; [L grip] cover\nRightGrip=RB\n; [R grip] grenade\n"
           "LeftStickClick=LB\n; [L stick click] sprint\nRightStickClick=RS\n; [R stick click] iron sight / scope\n"
           "LeftTrigger=LS\n; [L trigger] crouch\nRightTrigger=RT\n; [R trigger] fire\n\n")
screen = ("[ScreenButtons]\n; menus, terminals, readers: R trigger selects, B backs out\n"
          "RightTrigger=A\nRightB=B\nRightA=A\nLeftX=X\nLeftY=Y\nLeftTrigger=LT\n\n")
text = re.sub(r"\[Buttons\].*?(?=\n\[ScreenButtons\])", buttons.rstrip("\n"), text, count=1, flags=re.S)
text = re.sub(r"\[ScreenButtons\].*?(?=\n\[Luma\])", screen.rstrip("\n"), text, count=1, flags=re.S)
open(ini, "w").write(text)
print(re.search(r"\[Buttons\].*?\[Luma\]", text, re.S).group(0))
