#!/usr/bin/env python3
# License note: the replacement source fragments in this file derive from CactusVRStudios/alpinefactionVR (MPL-2.0)
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Frame patches for alpinefactionVR (game_patch/vr): jump/crouch/reload/flashlight/menu/alt-fire actions accept either
hand, and the menu action pauses even on SteamVR (the reload+crouch chord keeps working). Idempotent."""
import os, re, sys
SRC = os.path.expanduser('~/PCVR/RedFactionVR/src/game_patch/vr')

def patch(rel, old, new, count=1):
    p = os.path.join(SRC, rel); s = open(p).read()
    if new in s and old not in s: print('  already:', rel, repr(new[:40])); return
    if old not in s: sys.exit('PATCH FAILED %s: %r' % (rel, old[:70]))
    open(p, 'w').write(s.replace(old, new, count)); print('  patched:', rel, repr(new[:40]))

X = 'openxr_context.cpp'
# actions usable from either hand
for name, old in (('reload', 'left_hand'), ('jump', 'right_hand'), ('crouch', 'right_hand'), ('flashlight', 'left_hand')):
    patch(X, '"%s", ' % name, '"%s", ' % name)  # anchor sanity
s = open(os.path.join(SRC, X)).read()
s = re.sub(r'("reload", "Reload", )left_hand\)', r'\1both_hands)', s)
s = re.sub(r'("jump", "Jump", )right_hand\)', r'\1both_hands)', s)
s = re.sub(r'("crouch", "Crouch", )right_hand\)', r'\1both_hands)', s)
s = re.sub(r'("flashlight", "Toggle Flashlight or Headlight", )left_hand\)', r'\1both_hands)', s)
s = re.sub(r'("left_trigger", "Index Alternate Fire", )left_hand\)', r'\1both_hands)', s)
s = s.replace('create_action(menu_action_, XR_ACTION_TYPE_BOOLEAN_INPUT, "menu", "Menu", left_hand);',
              'create_action(menu_action_, XR_ACTION_TYPE_BOOLEAN_INPUT, "menu", "Menu", both_hands);')
# read them combined across hands (XR_NULL_PATH = any subaction)
for act, hand in (('reload', 0), ('jump', 1), ('crouch', 1), ('flashlight', 0), ('menu', 0)):
    s = s.replace('get_boolean(%s_action_, hand_paths_[%d])' % (act, hand), 'get_boolean(%s_action_, XR_NULL_PATH)' % act)
s = s.replace('input_state_.left_trigger = get_float(left_trigger_action_, hand_paths_[0]);',
              'input_state_.left_trigger = get_float(left_trigger_action_, XR_NULL_PATH); // Frame: either hand (right bumper)')
open(os.path.join(SRC, X), 'w').write(s)
print('  openxr_context.cpp: both_hands x6, XR_NULL_PATH reads x6 ->',
      s.count('both_hands)'), 'both_hands uses,', s.count('XR_NULL_PATH)'), 'null-path reads')

# --- a "recenter" action (Frame: right stick click), driving the mod's existing recenter_tracking()
H = 'openxr_context.h'
patch(H, '        bool menu = false;\n    };', '        bool menu = false;\n        bool recenter = false; // Frame\n    };')
patch(H, '        XrAction menu_action_ = XR_NULL_HANDLE;', '        XrAction menu_action_ = XR_NULL_HANDLE;\n        XrAction recenter_action_ = XR_NULL_HANDLE; // Frame')
patch(X, 'create_action(menu_action_, XR_ACTION_TYPE_BOOLEAN_INPUT, "menu", "Menu", both_hands);',
         'create_action(menu_action_, XR_ACTION_TYPE_BOOLEAN_INPUT, "menu", "Menu", both_hands);\n'
         '        create_action(recenter_action_, XR_ACTION_TYPE_BOOLEAN_INPUT, "recenter", "Recenter View", both_hands);')
patch(X, 'input_state_.menu = get_boolean(menu_action_, XR_NULL_PATH);',
         'input_state_.menu = get_boolean(menu_action_, XR_NULL_PATH);\n'
         '            input_state_.recenter = get_boolean(recenter_action_, XR_NULL_PATH);')
patch(X, '        menu_action_ = XR_NULL_HANDLE;\n', '        menu_action_ = XR_NULL_HANDLE;\n        recenter_action_ = XR_NULL_HANDLE;\n')

V = 'vr.cpp'
patch(V, '            g_previous_laser_toggle_pressed = laser_toggle_pressed;\n',
         '            g_previous_laser_toggle_pressed = laser_toggle_pressed;\n'
         '            {   // Frame: recenter action (right stick click)\n'
         '                static bool previous_recenter_pressed = false;\n'
         '                const bool recenter_pressed = g_openxr->is_session_running() && input.recenter;\n'
         '                if (recenter_pressed && !previous_recenter_pressed) {\n'
         '                    recenter_tracking();\n'
         '                    xlog::info("[AFVR] Recenter requested (controller)");\n'
         '                }\n'
         '                previous_recenter_pressed = recenter_pressed;\n'
         '            }\n')
patch(V, '(g_openxr->is_steamvr_runtime()\n                    ? steamvr_menu_chord_held : input.menu);',
         '(input.menu || steamvr_menu_chord_held); // Frame: a real menu button on SteamVR too')
print('done')
