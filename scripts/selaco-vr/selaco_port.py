#!/usr/bin/env python3
# License note: the replacement source fragments in this file derive from emawind84/SelacoVR (GZDoom / QuestZDoom), GPL-3.0,
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Linux/ARM64 patches for emawind84/SelacoVR (native OpenVR build on the Steam Frame). Idempotent."""
import os, sys
SRC = os.path.expanduser('~/PCVR/SelacoVR/src/src')

def patch(rel, old, new, must=True):
    p = os.path.join(SRC, rel)
    s = open(p).read()
    if new in s and (old not in s or old in new):
        print('  already:', rel); return
    if old not in s:
        if must: sys.exit('PATCH FAILED: %s: %r' % (rel, old[:60]))
        print('  skipped:', rel); return
    open(p, 'w').write(s.replace(old, new, 1)); print('  patched:', rel)

# --- GCC 15: ZWidget uses uint32_t without <cstdint>
patch('../libraries/ZWidget/include/zwidget/window/window.h', '#pragma once\n', '#pragma once\n#include <cstdint>\n')

# --- GCC 15 defaults to C23: the lemon/re2c build tools are K&R-era C
for tool in ('lemon', 're2c'):
    p = os.path.join(SRC, '../tools/%s/CMakeLists.txt' % tool)
    if os.path.exists(p):
        s = open(p).read()
        if 'std=gnu89' not in s:
            s += '\nif( NOT MSVC )\n\ttarget_compile_options( %s PRIVATE -std=gnu89 -Wno-error -Wno-implicit-function-declaration -Wno-incompatible-pointer-types )\nendif()\n' % tool
            open(p, 'w').write(s); print('  patched: tools/%s/CMakeLists.txt' % tool)
        else:
            print('  already: tools/%s' % tool)

# --- CMake: OpenVR input device on the SDL side too; linuxarm64 SDK dir
patch('CMakeLists.txt',
      "\tcommon/platform/posix/sdl/st_start.cpp )\n",
      "\tcommon/platform/posix/sdl/st_start.cpp )\nif( ENABLE_OPENVR AND NOT WIN32 )\n\tlist( APPEND PLAT_SDL_SOURCES win32/i_openVR.cpp )\nendif()\n")
# ...and it must not stay in the Win32 list, or OTHER_SYSTEM_SOURCES marks it HEADER_FILE_ONLY
patch('CMakeLists.txt',
      "\tlist( APPEND PLAT_SDL_SOURCES win32/i_openVR.cpp )\nendif()\n",
      "\tlist( APPEND PLAT_SDL_SOURCES win32/i_openVR.cpp )\n\tlist( REMOVE_ITEM PLAT_WIN32_SOURCES win32/i_openVR.cpp )\nendif()\n")
patch('CMakeLists.txt',
      "\t\tif(X64)\n\t\t\tset(OPENVR_PLAT ${OPENVR_PLAT}64)\n\t\telse()\n\t\t\tset(OPENVR_PLAT ${OPENVR_PLAT}32)\n\t\tendif()",
      "\t\tif(CMAKE_SYSTEM_PROCESSOR MATCHES \"aarch64|arm64\")\n\t\t\tset(OPENVR_PLAT ${OPENVR_PLAT}arm64)\n\t\telseif(X64)\n\t\t\tset(OPENVR_PLAT ${OPENVR_PLAT}64)\n\t\telse()\n\t\t\tset(OPENVR_PLAT ${OPENVR_PLAT}32)\n\t\tendif()")

# --- GCC 15 / C23: sqrt() used without <math.h>
patch('common/thirdparty/math/sqrt.c', '#include', '#include <math.h>\n#include')

# --- i_openVR.cpp: no Windows headers / JoyDevices table on POSIX (always re-applied from the pristine file)
import subprocess
subprocess.run(['git', '-C', SRC, 'checkout', '--', 'win32/i_openVR.cpp'], check=True)
p = os.path.join(SRC, 'win32/i_openVR.cpp'); s = open(p).read()
s = s.replace('JoyDevices[INPUT_OpenVR]', 'JoyDevices_OpenVR'); open(p, 'w').write(s)
patch('win32/i_openVR.cpp',
      '#include <Windows.h>\n#include "d_event.h"\n#include "i_input.h"\n',
      '''#ifdef _WIN32
#include <Windows.h>
#include "d_event.h"
#include "i_input.h"
#define JoyDevices_OpenVR JoyDevices[INPUT_OpenVR]
#else
// POSIX: no JoyDevices[] table; the SDL joystick code (posix/sdl/i_joystick.cpp) polls us through I_OpenVRGetDevices/I_OpenVRAddAxes.
#include "d_event.h"
#include "m_joy.h"
#include "tarray.h"
class FJoystickCollection
{
public:
	virtual ~FJoystickCollection() {}
	virtual bool GetDevice() = 0;
	virtual void ProcessInput() = 0;
	virtual void AddAxes(float axes[NUM_JOYAXIS]) = 0;
	virtual void GetDevices(TArray<IJoystickConfig *> &sticks) = 0;
	virtual IJoystickConfig *Rescan() = 0;
};
static FJoystickCollection *OpenVRJoyDevice = nullptr;
#define JoyDevices_OpenVR OpenVRJoyDevice
#endif
''')
s = open(p).read()
if True:
    s += '''
#ifndef _WIN32
void I_OpenVRGetDevices(TArray<IJoystickConfig *> &sticks)
{
	if (OpenVRJoyDevice != NULL) OpenVRJoyDevice->GetDevices(sticks);
}
void I_OpenVRAddAxes(float axes[NUM_JOYAXIS])
{
	if (OpenVRJoyDevice != NULL) OpenVRJoyDevice->AddAxes(axes);
}
#endif
'''
    open(p, 'w').write(s); print('  patched: i_openVR.cpp POSIX hooks')

# --- posix SDL joystick: expose the OpenVR device alongside SDL sticks
patch('common/platform/posix/sdl/i_joystick.cpp',
      'void PostDeviceChangeEvent() {',
      '#ifdef USE_OPENVR\nvoid I_OpenVRGetDevices(TArray<IJoystickConfig *> &sticks);\nvoid I_OpenVRAddAxes(float axes[NUM_JOYAXIS]);\n#endif\n\nvoid PostDeviceChangeEvent() {')
patch('common/platform/posix/sdl/i_joystick.cpp',
      '\tif (JoystickManager)\n\t\tJoystickManager->GetDevices(sticks);\n}',
      '\tif (JoystickManager)\n\t\tJoystickManager->GetDevices(sticks);\n#ifdef USE_OPENVR\n\tI_OpenVRGetDevices(sticks);\n#endif\n}')
patch('common/platform/posix/sdl/i_joystick.cpp',
      '\tif (use_joystick && JoystickManager)\n\t{\n\t\tJoystickManager->AddAxes(axes);\n\t}\n}',
      '\tif (use_joystick && JoystickManager)\n\t{\n\t\tJoystickManager->AddAxes(axes);\n\t}\n#ifdef USE_OPENVR\n\tif (use_joystick) I_OpenVRAddAxes(axes);\n#endif\n}')
# --- gl_openvr.cpp: SetupOverlay re-ran VR_Init as an Overlay app on top of the Scene init; the Linux runtime
#     shuts the client down on the double init and the next vrclient call segfaults. One init per process.
subprocess.run(['git', '-C', SRC, 'checkout', '--', 'rendering/gl/stereo3d/gl_openvr.cpp'], check=True)  # re-apply all below from pristine
patch('rendering/gl/stereo3d/gl_openvr.cpp',
      '\t\tvr::VR_Init(&eError, vr::EVRApplicationType::VRApplication_Overlay);;\n\t\tif (eError != EVRInitError_VRInitError_None) {\n\t\t\tstd::string errMsg = vr::VR_GetVRInitErrorAsEnglishDescription(eError);\n\t\t\treturn;\n\t\t}\n',
      '\t\t// Frame/Linux: no second VR_Init (Overlay) here - the overlay interface is reachable from the Scene init.\n\t\teError = vr::VRInitError_None;\n')
# --- OpenVR C API header: VRControllerState_t / VREvent_t are 4-byte packed on Linux in the C++ header and in
#     the runtime, but openvr_capi.h leaves them at default packing -> buttons/axes read from wrong offsets.
for st in ('VRControllerState_t',):
    patch('../../openvr/headers/openvr_capi.h',
          'typedef struct %s\n{' % st,
          '#if defined(__linux__) || defined(__APPLE__)\n#pragma pack( push, 4 )\n#endif\ntypedef struct %s\n{' % st)
    patch('../../openvr/headers/openvr_capi.h',
          '} %s;\n' % st,
          '} %s;\n#if defined(__linux__) || defined(__APPLE__)\n#pragma pack( pop )\n#endif\n' % st)
# --- Frame layout: expose the spare legacy buttons (Axis2/3/4 press) as distinct keys in joy_mode 1, and add a
#     vr_recenter console command (the code had a TODO for it). The Frame legacy binding maps X/menu/bumper and
#     the d-pad onto those ids; frame.cfg binds the keys.
GL = os.path.join(SRC, 'rendering/gl/stereo3d/gl_openvr.cpp')
s = open(GL).read()
if '//Frame: bumper' not in s:
    lines = s.split('\n')
    def uncomment_block(marker, newkey):
        # the commented block is the 4 lines ending with "//\t1, KEY_Fx);"
        i = next(k for k, l in enumerate(lines) if l.strip() == '// \t1, %s);' % marker)
        for k in range(i - 3, i + 1):
            lines[k] = lines[k].replace('// ', '', 1)
        lines[i] = lines[i].replace(marker, newkey)
        return i
    def add_axis4(after, newkey):
        blk = [l.replace('k_EButton_Axis3', 'k_EButton_Axis4') for l in lines[after - 3:after + 1]]
        blk[-1] = blk[-1][:blk[-1].rindex('1, ')] + '1, ' + newkey + ');'
        lines[after + 1:after + 1] = ['', '\t\t\t\t//Frame: bumper'] + blk
    J = lambda n: '(KEY_FIRSTJOYBUTTON + %d)' % (n - 1)   # "JoyN" in bind commands
    uncomment_block('KEY_F1', J(11))               # dominant X        -> Joy11
    i = uncomment_block('KEY_F5', J(12))           # dominant menu     -> Joy12
    add_axis4(i, J(13))                            # dominant bumper   -> Joy13
    uncomment_block('KEY_F2', J(14))               # off d-pad up      -> Joy14
    i = uncomment_block('KEY_F7', J(15))           # off d-pad down    -> Joy15
    add_axis4(i, J(16))                            # off bumper        -> Joy16
    s = '\n'.join(lines)
    open(GL, 'w').write(s); print('  patched: gl_openvr.cpp spare buttons')
else:
    print('  already: gl_openvr.cpp spare buttons')
patch('rendering/gl/stereo3d/gl_openvr.cpp', 'namespace openvr {\n#include "openvr.h"\n}',
      'bool vr_recenterRequested = false;\n\nnamespace openvr {\n#include "openvr.h"\n}')
patch('rendering/gl/stereo3d/gl_openvr.cpp',
      '\t\t\tif (!is_initial_origin_set) {\n\t\t\t\t// initialize origin to first noted HMD location\n\t\t\t\t// TODO: implement recentering based on a CCMD\n\t\t\t\topenvr_origin = openvr_HmdPos;\n\t\t\t\tis_initial_origin_set = true;\n\t\t\t}',
      '\t\t\tif (!is_initial_origin_set || vr_recenterRequested) {\n\t\t\t\t// initialize origin to first noted HMD location (or re-center on vr_recenter)\n\t\t\t\topenvr_origin = openvr_HmdPos;\n\t\t\t\tis_initial_origin_set = true;\n\t\t\t\tvr_recenterRequested = false;\n\t\t\t}')
# --- debugging aid: vr_debug_buttons 1 prints the raw legacy button masks whenever they change
patch('rendering/gl/stereo3d/gl_openvr.cpp', 'bool vr_recenterRequested = false;\n',
      'bool vr_recenterRequested = false;\nCVAR(Bool, vr_debug_buttons, false, 0)\n')
patch('rendering/gl/stereo3d/gl_openvr.cpp',
      '\t\t//Dominant Grip works like a shift key\n',
      '\t\t{\n\t\t\tstatic uint64_t dbgL = 0, dbgR = 0;\n\t\t\tif (vr_debug_buttons && (leftTrackedRemoteState_new.ulButtonPressed != dbgL || rightTrackedRemoteState_new.ulButtonPressed != dbgR))\n'
      '\t\t\t{\n\t\t\t\tdbgL = leftTrackedRemoteState_new.ulButtonPressed; dbgR = rightTrackedRemoteState_new.ulButtonPressed;\n'
      '\t\t\t\tPrintf("VRBTN L=%016llx R=%016llx\\n", (unsigned long long)dbgL, (unsigned long long)dbgR);\n\t\t\t}\n\t\t}\n'
      '\t\t//Dominant Grip works like a shift key\n')
# --- Frame controller (unsimulated legacy binding): the driver reports no Prop_AxisNType, so fall back to axis 0 = stick
patch('rendering/gl/stereo3d/gl_openvr.cpp',
      '\t\t\t\t\t\t\t\tif (axisTrigger == -1) axisTrigger = a;\n\t\t\t\t\t\t\t\tbreak;\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n',
      '\t\t\t\t\t\t\t\tif (axisTrigger == -1) axisTrigger = a;\n\t\t\t\t\t\t\t\tbreak;\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n'
      '\t\t\t\t\t\tif (axisJoystick == -1 && axisTrackpad == -1) axisJoystick = 0; // Frame: no axis types reported, stick is axis 0\n\t\t\t\t\t}\n')
# --- menu overlay: feed it one eye's image, not left/right alternately (the per-eye scene behind the menu made it judder)
patch('rendering/gl/stereo3d/gl_openvr.cpp',
      '\t\t\tvrOverlay->SetOverlayTexture(overlayHandle, eyeTexture);\n\t\t\tvrOverlay->SetOverlayTextureBounds(overlayHandle, &tBounds);\n\t\t\tvrOverlay->SetOverlayWidthInMeters(overlayHandle, 1 + vr_overlayscreen_size);\n\t\t\tvrOverlay->ShowOverlay(overlayHandle);\n',
      '\t\t\tif (eye == 0)\n\t\t\t{\n\t\t\t\tvrOverlay->SetOverlayTexture(overlayHandle, eyeTexture);\n\t\t\t\tvrOverlay->SetOverlayTextureBounds(overlayHandle, &tBounds);\n\t\t\t\tvrOverlay->SetOverlayWidthInMeters(overlayHandle, 1 + vr_overlayscreen_size);\n\t\t\t\tvrOverlay->ShowOverlay(overlayHandle);\n\t\t\t}\n')
# --- poses/controllers were not polled on the title map (Selaco's main menu lives there), so menus were dead until in-game
patch('rendering/gl/stereo3d/gl_openvr.cpp',
      '\t\tif (gamestate != GS_TITLELEVEL) {\n\t\t\t// TODO: Draw a more interesting background behind the 2D screen\n',
      '\t\tif (true) { // Frame: poll poses and controllers on the title map too, or the main menu cannot be driven\n\t\t\t// TODO: Draw a more interesting background behind the 2D screen\n')
patch('rendering/gl/stereo3d/gl_openvr.cpp', 'CCMD (cinemamode)\n{',
      'CCMD (vr_recenter)\n{\n\tvr_recenterRequested = true;\n}\n\nCCMD (cinemamode)\n{')
print('done')
