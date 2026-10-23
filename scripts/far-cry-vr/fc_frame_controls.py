"""Steam Frame layout for Far Cry VR (fholger CryVR, SteamVR Input). The mod ships only Touch/Index bindings; SteamVR's
Touch->Frame auto-remap passes the right-stick d-pad zones but none of the buttons. Standard layout + user rules:

  on foot / weapons                                   vehicles (mod defaults, moved to Frame buttons)
  R trigger   fire                                    R trigger  vehicle weapon
  R bumper    use (doors, vehicles, mounted guns)     L trigger  leave vehicle
  L trigger   crouch          L bumper  jump          L stick    steer / throttle, click = change view
  A  grenades (hold = throw)  B  reload               A  reload            B  change seat
  X  binoculars               menu = pause menu       X  lights
  L stick move, click sprint
  R stick left/right snap/smooth turn (mod option), up = next weapon + binocular zoom in, down = zoom out
  grips (80% squeeze) = the mod's grip action (two-handed weapon hold)
Writes bindings_frame_controller.json next to the mod's actions.json, adds it as the frame_controller default and selects
it for steam.app.13520 in steamvr.vrsettings. Originals kept as *.orig."""
import json, os, shutil

HOME = os.path.expanduser('~')
S = f'{HOME}/.local/share/Steam/steamapps/common/FarCry/Mods/CryVR/steamvr'
SETTINGS = f'{HOME}/.config/openvr/config/steamvr.vrsettings'
APP = 'steam.app.13520'
OUT = f'{S}/bindings_frame_controller.json'
L, R = '/user/hand/left/input', '/user/hand/right/input'

def btn(path, out, extra=None):
    s = {'path': path, 'mode': 'button', 'inputs': {'click': {'output': out}}}
    if extra: s['parameters'] = extra
    return s
GRIP = {'click_activate_threshold': '0.8', 'click_deactivate_threshold': '0.7'}

touch = json.load(open(f'{S}/bindings_touch.json'))['bindings']
default = {
    'poses': touch['/actions/default'].get('poses', []), 'haptics': touch['/actions/default'].get('haptics', []),
    'sources': [
        btn(f'{R}/menu', '/actions/default/in/menu'),
        btn(f'{R}/bumper', '/actions/default/in/use'),
        btn(f'{R}/x', '/actions/default/in/binoculars'),
        btn(f'{L}/grip', '/actions/default/in/grip', GRIP),
        btn(f'{R}/grip', '/actions/default/in/grip', GRIP),
        {'path': f'{R}/thumbstick', 'mode': 'dpad', 'parameters': {'deadzone_pct': '75', 'overlap_pct': '0', 'sub_mode': 'touch', 'sticky': 'true'},
         'inputs': {'north': {'output': '/actions/default/in/zoomin'}, 'south': {'output': '/actions/default/in/zoomout'}}},
    ],
}
move = {'sources': [
    {'path': f'{L}/thumbstick', 'mode': 'joystick', 'inputs': {'position': {'output': '/actions/move/in/move'}}, 'parameters': {'exponent': '2', 'deadzone_pct': '10'}},
    {'path': f'{L}/thumbstick', 'mode': 'button', 'inputs': {'click': {'output': '/actions/move/in/sprint'}}},
    {'path': f'{R}/thumbstick', 'mode': 'dpad', 'parameters': {'deadzone_pct': '75', 'overlap_pct': '0', 'sub_mode': 'touch', 'sticky': 'true'},
     'inputs': {'east': {'output': '/actions/move/in/turnright'}, 'west': {'output': '/actions/move/in/turnleft'}}},
    {'path': f'{R}/thumbstick', 'mode': 'joystick', 'inputs': {'position': {'output': '/actions/move/in/continuousturn'}}, 'parameters': {'deadzone_pct': '10', 'exponent': '2'}},
    btn(f'{L}/bumper', '/actions/move/in/jump'),
    btn(f'{L}/trigger', '/actions/move/in/crouch'),
]}
weapons = {'sources': [
    btn(f'{R}/trigger', '/actions/weapons/in/fire'),
    btn(f'{R}/b', '/actions/weapons/in/reload'),
    btn(f'{R}/a', '/actions/weapons/in/grenades'),
    {'path': f'{R}/thumbstick', 'mode': 'dpad', 'parameters': {'deadzone_pct': '75', 'overlap_pct': '0', 'sub_mode': 'touch', 'sticky': 'true'},
     'inputs': {'north': {'output': '/actions/weapons/in/next'}}},
]}
vehicles = {'sources': [
    {'path': f'{L}/thumbstick', 'mode': 'joystick', 'inputs': {'position': {'output': '/actions/vehicles/in/steer'}}, 'parameters': {'exponent': '2'}},
    {'path': f'{L}/thumbstick', 'mode': 'button', 'inputs': {'click': {'output': '/actions/vehicles/in/changeview'}}},
    btn(f'{R}/trigger', '/actions/vehicles/in/attack'),
    btn(f'{L}/trigger', '/actions/vehicles/in/leave'),
    btn(f'{R}/a', '/actions/vehicles/in/reload'),
    btn(f'{R}/b', '/actions/vehicles/in/changeseat'),
    btn(f'{R}/x', '/actions/vehicles/in/lights'),
]}
binding = {'action_manifest_version': 0, 'alias_info': {}, 'category': 'steamvr_input', 'controller_type': 'frame_controller',
           'name': 'Far Cry VR - Steam Frame', 'description': 'Standard Frame layout: L bumper jump, L trigger crouch, R trigger fire, R bumper use, A grenades, B reload, X binoculars, menu pause.',
           'options': {}, 'simulated_actions': [],
           'bindings': {'/actions/default': default, '/actions/move': move, '/actions/weapons': weapons, '/actions/vehicles': vehicles}}
json.dump(binding, open(OUT, 'w'), indent=2); print('wrote', OUT)

ap = f'{S}/actions.json'
if not os.path.exists(ap + '.orig'): shutil.copy(ap, ap + '.orig')
a = json.load(open(ap))
a['default_bindings'] = [{'controller_type': 'frame_controller', 'binding_url': 'bindings_frame_controller.json'}] + \
    [d for d in a['default_bindings'] if d['controller_type'] != 'frame_controller']
json.dump(a, open(ap, 'w'), indent=2); print('actions.json: frame_controller default added')

if not os.path.exists(SETTINGS + '.orig-farcry'): shutil.copy(SETTINGS, SETTINGS + '.orig-farcry')
s = json.load(open(SETTINGS)); sec = s.setdefault(APP, {})
for k in ('frame_controller_CurrentURL_steamvrinput', 'frame_controller_250820_CurrentURL_steamvrinput'):
    sec[k] = 'file://' + OUT.replace(' ', '%20')
json.dump(s, open(SETTINGS, 'w'), indent=3); print('selected for', APP)
