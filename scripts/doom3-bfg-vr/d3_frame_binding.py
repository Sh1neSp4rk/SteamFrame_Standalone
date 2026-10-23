"""Writes the Steam Frame controller layout for Doom 3 BFG VR (native, legacy OpenVR input):
  1. ~/PCVR/D3BFGVR-game/d3bfgvr_frame_binding.json - SteamVR legacy binding (physical input -> legacy button),
     derived from SteamVR's own Frame legacy binding with harder grips and a real menu button.
  2. <Fully Possessed>/vr_openvr.cfg - the mod's user cfg (legacy button JOYn -> game action).
  3. Selects the binding for steam.app.3138655638 in steamvr.vrsettings (backup kept).
Run with the game closed, then restart vrserver so it rereads the settings."""
import copy, json, os, shutil

HOME = os.path.expanduser("~")
DEFAULT = "/opt/steamvr/drivers/frame_controller/resources/input/legacy_bindings_frame_controller.json"
OUT = f"{HOME}/PCVR/D3BFGVR-game/d3bfgvr_frame_binding.json"
CFG = f"{HOME}/PCVR/D3BFGVR/vr_assets/Fully Possessed/vr_openvr.cfg"
SETTINGS = f"{HOME}/.config/openvr/config/steamvr.vrsettings"
APP = "steam.app.3138655638"

b = json.load(open(DEFAULT))
b["name"] = "Doom 3 BFG VR - Steam Frame layout"
b["description"] = ("Grips unused. Bumpers drive the legacy grip button (left: jump, right: PDA), "
                    "the left d-pad opens the main menu, right A crouches and B reloads.")
srcs = b["bindings"]["/actions/legacy"]["sources"]
out = []
for s in srcs:
    path = s["path"]
    if path.endswith("/grip"):
        continue  # physical grips unused: holding the controller kept triggering them
    if path.endswith("/bumper"):
        if "touch" not in s["inputs"]:
            continue  # drop the duplicate trigger-value source
        hand = "left" if "/left/" in path else "right"
        s = {"path": path, "mode": "button", "inputs": {"click": {"output": f"/actions/legacy/in/{hand}_grip_press"}}}
    elif path == "/user/hand/left/input/dpad_down":
        s = {"path": path, "mode": "button", "inputs": {"click": {"output": "/actions/legacy/in/left_applicationmenu_press"}}}
    elif path in ("/user/hand/right/input/x", "/user/hand/right/input/y"):
        continue  # duplicated B
    out.append(s)
b["bindings"]["/actions/legacy"]["sources"] = out
json.dump(b, open(OUT, "w"), indent=2)
print("wrote", OUT, f"({len(out)} sources)")

# legacy button -> JOY key (from the mod's sys_public.h enum): L menu JOY32, L grip JOY33, L "A" JOY38,
# L stick click JOY39, L trigger JOY40; R menu JOY50, R grip JOY51, R A JOY56, R stick click JOY57, R trigger JOY58.
cfg = """// Steam Frame controller layout for Doom 3 BFG VR (written by ~/PCVR/bin/d3_frame_binding.py).
// Executed after vr_openvr_default.cfg; only the controller binds are changed.
bind "JOY32" "_impulse40"   // left d-pad: main menu (Escape)
bind "JOY33" "_moveup"      // left bumper (legacy grip): jump
unbind "JOY38"              // legacy left A: no physical button
bind "JOY39" "_speed"       // left stick click: sprint
bind "JOY40" "_impulse16"   // left trigger: flashlight
bind "JOY50" "_impulse13"   // right B: reload
bind "JOY51" "_impulse19"   // right bumper (legacy grip): PDA
bind "JOY56" "_movedown"    // right A: crouch (hold)
bind "JOY57" "_impulse32"   // right stick click: recenter view
bind "JOY58" "_attack"      // right trigger: fire
bind "STEAMVR_LEFT_PAD_UP" "_forward"
bind "STEAMVR_LEFT_PAD_DOWN" "_back"
bind "STEAMVR_LEFT_PAD_LEFT" "_moveLeft"
bind "STEAMVR_LEFT_PAD_RIGHT" "_moveRight"
bind "STEAMVR_RIGHT_PAD_UP" "_impulse14"     // right stick up: next weapon
bind "STEAMVR_RIGHT_PAD_DOWN" "_impulse15"   // right stick down: previous weapon
bind "STEAMVR_RIGHT_PAD_LEFT" "_impulse35"   // right stick left: snap turn left
bind "STEAMVR_RIGHT_PAD_RIGHT" "_impulse34"  // right stick right: snap turn right
"""
open(CFG, "w").write(cfg)
print("wrote", CFG)

shutil.copy(SETTINGS, SETTINGS + ".bak-d3bfgvr")
s = json.load(open(SETTINGS))
app = s.setdefault(APP, {})
for key in ("frame_controller_CurrentURL_legacy", "frame_controller_250820_CurrentURL_legacy"):
    app[key] = "file://" + OUT
json.dump(s, open(SETTINGS, "w"), indent=3)
print("selected for", APP, app)
