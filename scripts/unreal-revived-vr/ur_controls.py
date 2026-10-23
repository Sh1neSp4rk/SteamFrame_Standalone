"""Steam Frame layout for Unreal Revived VR (standard layout, user rules: left bumper jump, left trigger crouch,
right trigger fire, right bumper alt-fire, menu pause, right stick click recenter; aim with the right controller).

Chain: Frame input -> game OpenXR action (/actions/revived_motion, per hand) -> Xbox bit (D3D12Drv OPENXRINPUT:
right primary A, right secondary B, left primary X, left secondary Y, squeeze>0.5 LB/RB, stick clicks LS/RS,
menu (either hand) Start, view (either hand) Back, triggers LT/RT) -> Unreal key Joy1..Joy12 -> User.ini bind.

  Frame               action                 pad    Joy    Unreal
  R trigger           right trigger          RT     Joy11  Fire
  R bumper            right squeeze_click    RB     Joy6   AltFire
  L trigger           left trigger           LT     Joy12  Duck
  L bumper            left squeeze_click     LB     Joy5   Jump
  R A                 right primary          A      Joy1   InventoryActivate
  R B                 right secondary        B      Joy2   InventoryNext
  R X, L view         right/left view        Back   Joy7   ActivateTranslator
  R menu              right menu             Start  Joy8   (menu / pause, built in)
  L d-pad up          left secondary         Y      Joy4   NextWeapon
  L d-pad down        left primary           X      Joy3   PrevWeapon
  L stick click,      left stick_click       LS     Joy9   InventoryPrevious
    L d-pad left
  R stick click       right stick_click      RS     Joy10  RecenterVR
  sticks              stick                  sticks        move / turn (the mod's VR turning)
  R Y, L d-pad right, grips: unbound (no pad button left; grips stay free per the standard)

Writes ur_frame_binding.json, installs it as the app's Touch default (read-only, so SteamVR can't regenerate it) and
blocks the other generated defaults (Index, Vive, generic) so the context holds one profile; also selects it in
steamvr.vrsettings for later SteamVR starts. Edits User.ini binds and VRAimMode=1. Run with the game closed."""
import json, os, re, shutil, stat, subprocess

HOME = os.path.expanduser('~'); D = f'{HOME}/PCVR/UnrealRevivedVR'
APPID = open(f'{D}/appid.txt').read().strip(); APP = f'steam.app.{APPID}'
S = f'{HOME}/.local/share/Steam/steamapps/compatdata/{APPID}/pfx/drive_c/Games/Unreal Revived/System64'
XR = f'{HOME}/.config/openvr/config/openxr'
A = '/actions/revived_motion/in/'
L, R = '/user/hand/left/input', '/user/hand/right/input'

def btn(path, action, inp='click'):
    return {'path': path, 'mode': 'button', 'inputs': {inp: {'output': A + action}},
            'parameters': {'force_input': 'click', 'haptic_amplitude': 0}}

sources = [
    {'path': f'{L}/thumbstick', 'mode': 'joystick', 'inputs': {'position': {'output': A + 'stick'}}},
    {'path': f'{R}/thumbstick', 'mode': 'joystick', 'inputs': {'position': {'output': A + 'stick'}}},
    btn(f'{L}/thumbstick', 'stick_click'), btn(f'{R}/thumbstick', 'stick_click'),
    {'path': f'{L}/trigger', 'mode': 'trigger', 'inputs': {'pull': {'output': A + 'trigger'}}},
    {'path': f'{R}/trigger', 'mode': 'trigger', 'inputs': {'pull': {'output': A + 'trigger'}}},
    btn(f'{L}/bumper', 'squeeze_click'), btn(f'{R}/bumper', 'squeeze_click'),
    btn(f'{R}/a', 'primary'), btn(f'{R}/b', 'secondary'), btn(f'{R}/x', 'view'), btn(f'{R}/menu', 'menu'),
    btn(f'{L}/view', 'view'),
    btn(f'{L}/dpad_up', 'secondary'), btn(f'{L}/dpad_down', 'primary'), btn(f'{L}/dpad_left', 'stick_click'),
]
poses = [{'output': A + p, 'path': f'/user/hand/{h}/pose/openxr_{p}'} for h in ('left', 'right') for p in ('aim', 'grip')]
binding = {
    'name': 'Unreal Revived VR - Steam Frame layout',
    'description': 'R: trigger fire, bumper alt-fire, A use item, B next item, X translator, menu pause, stick click recenter. '
                   'L: trigger crouch, bumper jump, stick click / d-pad left previous item, d-pad up/down weapons, view translator.',
    'controller_type': 'frame_controller', 'category': 'openxr',
    'interaction_profile': '/interaction_profiles/oculus/touch_controller', 'options': {'mirror_actions': False},
    'bindings': {'/actions/revived_motion': {'chords': [], 'eyetracking': [], 'haptics': [], 'poses': poses, 'sources': sources}},
}
out = f'{D}/ur_frame_binding.json'
json.dump(binding, open(out, 'w'), indent=3); print('wrote', out)

# SteamVR side: our file in the Touch default's place (read-only), other generated defaults blocked
for f in os.listdir(XR):
    if not f.startswith(APP + '_'): continue
    p = f'{XR}/{f}'; os.chmod(p, 0o644)
    if '_oculus_touch_' in f:
        if not os.path.exists(p + '.orig'): shutil.copy(p, p + '.orig')
        shutil.copy(out, p)
    else:
        open(p, 'w').write('{}')
    os.chmod(p, 0o444); print('locked', f, '(frame layout)' if '_oculus_touch_' in f else '(blocked)')
subprocess.run(['python3', f'{HOME}/PCVR/bin/vrsettings_bind.py', APP, 'openxr', out], check=False)

# Unreal side: pad binds + controller aiming
binds = {'Joy1': 'InventoryActivate', 'Joy2': 'InventoryNext', 'Joy3': 'PrevWeapon', 'Joy4': 'NextWeapon',
         'Joy5': 'Jump', 'Joy6': 'AltFire', 'Joy7': 'ActivateTranslator', 'Joy9': 'InventoryPrevious',
         'Joy10': 'RecenterVR', 'Joy11': 'Fire', 'Joy12': 'Duck'}
u = f'{S}/User.ini'
if not os.path.exists(u + '.orig'): shutil.copy(u, u + '.orig')
t = open(u, encoding='latin-1').read()
for k, v in binds.items(): t = re.sub(rf'(?m)^{k}=.*$', f'{k}={v}', t)
open(u, 'w', encoding='latin-1').write(t); print('User.ini binds set')
v = f'{S}/UnrealVR.ini'
if not os.path.exists(v + '.orig'): shutil.copy(v, v + '.orig')
t = open(v, encoding='latin-1').read(); t = re.sub(r'(?m)^VRAimMode=.*$', 'VRAimMode=1', t)
open(v, 'w', encoding='latin-1').write(t); print('UnrealVR.ini VRAimMode=1')
