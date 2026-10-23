#!/usr/bin/env python3
"""Write the Steam Frame legacy-input binding for Selaco VR (steam.app.3063768737) and the frame.cfg the launcher execs.

Selaco VR is a legacy OpenVR app: SteamVR maps each Frame input to a legacy button id, the port's joy_mode 1 code
turns ids into gamepad keys (patched so Axis2/3/4 press are distinct keys), and frame.cfg binds the keys.

  Frame input          legacy id            key        action
  R trigger            right_axis1          RTrigger   +attack            L trigger      left_axis1    Shift   +crouch (user: like the Quake games)
  R A                  right_a              Pad_A      +use               L bumper       left_axis4    Joy16   +jump
  R B                  right_appmenu        Pad_B      +reload            L stick click  left_axis0    Space   +speed (sprint)
  R X                  right_axis2          Joy11      Toggle_Flashlight  L grip (80%)   left_grip     -       two-handed weapon hold
  R menu               right_axis3          Joy12      menu_main          L d-pad up     left_axis2    Joy14   useGadget (quick save/load dropped: in the way)
  R bumper             right_axis4          Joy13      +altattack (user: secondary fire above the trigger)   L d-pad down   left_axis3    Joy15   switchGadget
  R stick click        right_axis0          Enter      vr_recenter        L d-pad left   left_a        Pad_X   useMeds
  R stick up/down      (code, 70%)          MWheel     weapprev/next      L view         left_appmenu  Pad_Y   codex (PDA)
  R stick left/right   (code)               -          snap turn 45       L d-pad right  -             -       unbound
  R grip (80%)         right_grip           LTrigger   +usereload (use-or-reload, user request)
  R Y                  -                    -          unbound (no spare legacy id)
"""
import json, os
G = os.path.expanduser('~/PCVR/SelacoVR/game')

def button(path, out, **params):
    src = {'inputs': {'click': {'output': '/actions/legacy/in/' + out}}, 'mode': 'button', 'path': '/user/hand/' + path}
    if params: src['parameters'] = {k: str(v) for k, v in params.items()}
    return src

TRIG = dict(click_activate_threshold=0.55, click_deactivate_threshold=0.5, haptic_amplitude=0)
GRIP = dict(click_activate_threshold=0.8, click_deactivate_threshold=0.7, haptic_amplitude=0)
sources = []
for h in ('left', 'right'):
    sources += [
        button(h + '/input/system', h + '_system_press'),
        {'inputs': {'pull': {'output': '/actions/legacy/in/%s_axis1_value' % h}}, 'mode': 'trigger',
         'parameters': {'haptic_amplitude': '0'}, 'path': '/user/hand/%s/input/trigger' % h},
        button(h + '/input/trigger', h + '_axis1_press', **TRIG),
        {'inputs': {'click': {'output': '/actions/legacy/in/%s_axis0_press' % h},
                    'position': {'output': '/actions/legacy/in/%s_axis0_value' % h},
                    'touch': {'output': '/actions/legacy/in/%s_axis0_touch' % h}},
         'mode': 'joystick', 'path': '/user/hand/%s/input/thumbstick' % h},
        button(h + '/input/bumper', h + '_axis4_press'),
    ]
sources += [
    button('left/input/grip', 'left_grip_press', **GRIP),
    button('left/input/dpad_up', 'left_axis2_press'),
    button('left/input/dpad_down', 'left_axis3_press'),
    button('left/input/dpad_left', 'left_a_press'),
    button('left/input/view', 'left_applicationmenu_press'),
    button('right/input/a', 'right_a_press'),
    button('right/input/b', 'right_applicationmenu_press'),
    button('right/input/x', 'right_axis2_press'),
    button('right/input/menu', 'right_axis3_press'),
    button('right/input/grip', 'right_grip_press', **GRIP),   # user request: right grip (80%) = use/reload
]
binding = {
    'action_manifest_version': 0,
    'alias_info': {},
    'bindings': {'/actions/legacy': {
        'sources': sources,
        'haptics': [{'output': '/actions/legacy/out/%s_haptic' % h, 'path': '/user/hand/%s/output/haptic' % h} for h in ('left', 'right')],
        'poses': [{'output': '/actions/legacy/in/%s_Pose' % h.capitalize(), 'path': '/user/hand/%s/pose/raw' % h} for h in ('left', 'right')],
    }},
    'controller_type': 'frame_controller',
    'description': 'Steam Frame standard layout: triggers fire/alt-fire, left bumper jump, right bumper use, A crouch, B reload, '
                   'X flashlight, menu pauses, d-pad quicksave/quickload/meds, view = PDA, right stick click recenters. Grips 80%.',
    'name': 'Selaco VR - Steam Frame layout',
    # no simulated controller type: SteamVR's Touch simulation drops the axis3/axis4 press ids (menu, bumpers, d-pad down)
    'options': {'mirror_actions': False},
    'simulated_actions': [],
}
p = os.path.join(G, 'selaco_frame_binding.json')
json.dump(binding, open(p, 'w'), indent=1)
print('wrote', p)

CFG = r'''// Selaco VR - Steam Frame settings, exec'd by selacovr-run.sh on every start (edit here, not in the menus).
// SelacoVR's CVARINFO.vrdefaults is not read by the engine, so its defaults are applied here.
vid_vsync false
turbo 80
gl_lens false
movebob 0
gl_bloom false
crosshair 1
crosshairscale 1
m_use_mouse true
use_joystick true
// use by hand aim or view (the mod's hands-only default makes doors miss when the hand is off the panel)
use_mode 2
// menus/title on a head-locked SteamVR overlay (1 = fixed in the raw tracking space, which ends up out of view on the Frame)
vr_overlayscreen 2
hud_momentum 0
g_cameramotion 0
g_overlay_armor false
g_overlay_dash false
g_overlay_dirt false
g_overlay_frozen false
g_overlay_healing false
g_overlay_steam false
g_screenbloodeffects 0
g_slidezooming 0
g_vignetting 0
r_filmgrain 0
hud_scaling 1
snd_subtitlesize 3
g_tos 1
vr_2dweaponOffsetX -3.5
vr_2dweaponOffsetY 0
vr_2dweaponOffsetZ 0.3
vr_2dweaponScale 0.5
vr_hud_fixed_pitch true
vr_hud_fixed_roll false
vr_automap_use_hud true
vid_scalemode 0
gl_max_lights 80000
// Graphics: Selaco's own "Quality (Steam Deck)" preset (GFXPresetDeckHigh), pinned so the first-run prompt can't
// downgrade it. r_thingLOD is the voxel-to-sprite distance (Performance preset uses 700). bloom/lens stay off for VR.
r_rainquality 2
r_shadowQuality 1
gl_texture_filter 6
gl_light_shadowmap 1
gl_shadowmap_quality 512
gl_shadowmap_filter 3
gl_fxaa 0
r_waterquality 1
gl_ssao 2
r_reflections 1
cl_maxdecals 1000
r_thingLOD 1400
smokeeffects 1
r_smokequality 3
r_particleIntensity 3
r_particleLifespan 1
r_BloodQuality 1
lightingquality 2
r_fogeffects 1
r_drawplayersprites 1
r_mirror_recursions 2
g_permanentDestruction 0
g_permanentGore 0
r_muzzleflashShadows 0
r_flashlightshadows 0
r_smokedensity 1
r_drawvoxels true
// Frame layout
vr_joy_mode 1
vr_control_scheme 0
vr_secondary_button_mappings false
vr_two_handed_weapons true
vr_snapTurn 45
vr_crouch_use_button true
vr_teleport false
bind RTrigger "+attack"
bind Shift "+crouch"
bind Pad_A "+use"
bind Pad_B "+reload"
bind Joy11 "Toggle_Flashlight"
bind Joy12 "menu_main"
bind Joy13 "+altattack"
bind Joy16 "+jump"
bind Enter "vr_recenter"
bind Space "+speed"
unbind RThumb
bind LTrigger "+usereload"
bind Joy14 "useGadget"
bind Joy15 "switchGadget"
bind Pad_X "useMeds"
bind Pad_Y "codex"
bind MWheelUp "weapprev"
bind MWheelDown "weapnext"
'''
open(os.path.join(G, 'frame.cfg'), 'w').write(CFG)
print('wrote frame.cfg')
