# License note: the replacement source fragments in this file derive from GameOrDie007/Quake-PCVR (DarkPlaces, Team Beef QuakeQuest), GPL-2.0,
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Port Quake-PCVR's OpenXR seam (Team Beef's QuakeQuest on DarkPlaces, PC port by GameOrDie007) to Linux:
the XR_KHR_opengl_enable Xlib/GLX graphics binding in place of the Win32 one, for a native linux-arm64 build on
the Steam Frame (as q2_port.py did for Quake-II-PCVR), plus two Frame fixes in vr_input.c: haptic timing in double
(float milliseconds since the epoch never advance, so a quick-save buzz never stopped), and the left hand's A action
(the Frame layout's left bumper) read as the right A, so it jumps and selects. Idempotent.
Usage: python3 -I q1pc_port.py <repo dir>"""
import os, sys

root = sys.argv[1]

def patch(rel, pairs):
    path = os.path.join(root, rel)
    s = open(path).read()
    for old, new in pairs:
        if new in s:
            continue
        assert s.count(old) == 1, (rel, old[:60], s.count(old))
        s = s.replace(old, new)
    open(path, "w").write(s)
    print("patched", rel)

patch("vr_tbxr.h", [
    ("#define XR_USE_PLATFORM_WIN32 1\n#define XR_USE_GRAPHICS_API_OPENGL 1\n",
     "#ifdef WIN32\n#define XR_USE_PLATFORM_WIN32 1\n#else\n#define XR_USE_PLATFORM_XLIB 1 // Steam Frame: native linux-arm64, GLX\n#endif\n"
     "#define XR_USE_GRAPHICS_API_OPENGL 1\n"),
    ("#include <windows.h>\n\n#include <openxr/openxr.h>\n",
     "#ifdef WIN32\n#include <windows.h>\n#else\n#include <X11/Xlib.h>\n#include <GL/glx.h> // the GLXContext and GLXDrawable the Xlib binding carries\n#endif\n\n#include <openxr/openxr.h>\n"),
])

patch("vr_xr.c", [
    ("\tXrGraphicsBindingOpenGLWin32KHR graphicsBinding = {};\n",
     "#ifdef WIN32\n\tXrGraphicsBindingOpenGLWin32KHR graphicsBinding = {};\n#else\n\tXrGraphicsBindingOpenGLXlibKHR graphicsBinding = {};\n#endif\n"),
    ("\tgraphicsBinding.type = XR_TYPE_GRAPHICS_BINDING_OPENGL_WIN32_KHR;\n\tgraphicsBinding.next = NULL;\n"
     "\tgraphicsBinding.hDC = wglGetCurrentDC();\n\tgraphicsBinding.hGLRC = wglGetCurrentContext();\n\n"
     "\tif (!graphicsBinding.hDC || !graphicsBinding.hGLRC)\n",
     "#ifdef WIN32\n"
     "\tgraphicsBinding.type = XR_TYPE_GRAPHICS_BINDING_OPENGL_WIN32_KHR;\n\tgraphicsBinding.next = NULL;\n"
     "\tgraphicsBinding.hDC = wglGetCurrentDC();\n\tgraphicsBinding.hGLRC = wglGetCurrentContext();\n\n"
     "\tif (!graphicsBinding.hDC || !graphicsBinding.hGLRC)\n"
     "#else\n"
     "\t// Steam Frame: SDL's X11 window and GLX context, current on this thread (SDL_VIDEODRIVER=x11)\n"
     "\tgraphicsBinding.type = XR_TYPE_GRAPHICS_BINDING_OPENGL_XLIB_KHR;\n\tgraphicsBinding.next = NULL;\n"
     "\tgraphicsBinding.xDisplay = glXGetCurrentDisplay();\n"
     "\tgraphicsBinding.glxDrawable = glXGetCurrentDrawable();\n"
     "\tgraphicsBinding.glxContext = glXGetCurrentContext();\n\n"
     "\tif (!graphicsBinding.xDisplay || !graphicsBinding.glxContext)\n"
     "#endif\n"),
])

patch("vr_input.c", [
    # Haptics: Sys_DirtyTime() * 1000 is milliseconds since the epoch on Linux; as a float that only changes every
    # 131 s, so frametime was 0 and a 500 ms buzz ran forever. Keep the clock in double.
    ("    static float lastFrameTime = 0.0f;\n    float timestamp = (float)(TBXR_GetTimeInMilliSeconds( ));\n"
     "    float frametime = timestamp - lastFrameTime;\n",
     "    static double lastFrameTime = 0.0; // Steam Frame: double, or ms since the epoch never advance in float\n"
     "    double timestamp = TBXR_GetTimeInMilliSeconds( );\n"
     "    float frametime = (float)(timestamp - lastFrameTime);\n"),
    # The Frame layout binds the left bumper to akey: the game only reads the right hand's A (jump; Enter in menus).
    ("    if (GetActionStateBoolean(AAction, SIDE_RIGHT).currentState) rightTrackedRemoteState_new.Buttons |= xrButton_A;\n",
     "    if (GetActionStateBoolean(AAction, SIDE_RIGHT).currentState) rightTrackedRemoteState_new.Buttons |= xrButton_A;\n"
     "    if (GetActionStateBoolean(AAction, SIDE_LEFT).currentState) rightTrackedRemoteState_new.Buttons |= xrButton_A; // Steam Frame: the left bumper as A\n"),
])
