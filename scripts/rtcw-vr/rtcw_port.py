# License note: the replacement source fragments in this file derive from Team-Beef-Studios/RealRTCWXR (ioRTCW / RealRTCW), GPL-3.0,
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Port RealRTCWXR (Team Beef's OpenXR build of RealRTCW 5.0, Windows-only) to Linux for a native linux-arm64 build on
the Steam Frame: the OpenXR layer compiled into the Makefile client, the Win32 graphics binding swapped for Xlib/GLX,
and the Windows timer replaced. Idempotent. Usage: python3 -I rtcw_port.py <repo dir>"""
import os, sys

root = sys.argv[1]

def patch(rel, pairs):
    path = os.path.join(root, rel)
    s = open(path).read()
    for old, new in pairs:
        if new in s:
            continue
        assert s.count(old) == 1, (rel, old[:70], s.count(old))
        s = s.replace(old, new)
    open(path, "w").write(s)
    print("patched", rel)

V = "code/RealRTCWXR/RealRTCWXR/"

# The desktop OpenXR layer serves Linux too (there is no android/ in this repo).
patch(V + "VrCommon.h", [
    ('#ifdef _WIN32\n#include "windows/TBXR_Common.h"\n#else\n#include "android/TBXR_Common.h"\n#endif\n',
     '#include "windows/TBXR_Common.h" // Steam Frame: the desktop layer serves Linux too\n'),
])

patch(V + "windows/TBXR_Common.h", [
    ("#if defined(_WIN32)\n\n// OpenXR Header\n#include <Unknwn.h>\n#include <openxr.h>\n",
     "#if defined(_WIN32) || defined(__linux__)\n\n// OpenXR Header\n#if defined(_WIN32)\n#include <Unknwn.h>\n"
     "#else\n#include <X11/Xlib.h> // Steam Frame: the Xlib/GLX graphics binding (XR_USE_PLATFORM_XLIB)\n#include <GL/glx.h>\n#endif\n"
     "#include <openxr.h>\n"),
    ("#include <GL/glext.h>\n#include <GL/wglext.h>\n",
     "#include <GL/glext.h>\n#if defined(_WIN32)\n#include <GL/wglext.h>\n#endif\n"),
])

patch(V + "windows/TBXR_Common.c", [
    ("\t// Create the OpenXR Session.\n"
     "\tXrGraphicsBindingOpenGLWin32KHR graphicsBindingOpenGLWin32KHR = {0};\n"
     "\tgraphicsBindingOpenGLWin32KHR.type = XR_TYPE_GRAPHICS_BINDING_OPENGL_WIN32_KHR;\n"
     "\tgraphicsBindingOpenGLWin32KHR.next = NULL;\n"
     "\tgraphicsBindingOpenGLWin32KHR.hDC = wglGetCurrentDC();\n"
     "\tgraphicsBindingOpenGLWin32KHR.hGLRC = wglGetCurrentContext();\n",
     "\t// Create the OpenXR Session.\n"
     "#if defined(_WIN32)\n"
     "\tXrGraphicsBindingOpenGLWin32KHR graphicsBindingOpenGLWin32KHR = {0};\n"
     "\tgraphicsBindingOpenGLWin32KHR.type = XR_TYPE_GRAPHICS_BINDING_OPENGL_WIN32_KHR;\n"
     "\tgraphicsBindingOpenGLWin32KHR.next = NULL;\n"
     "\tgraphicsBindingOpenGLWin32KHR.hDC = wglGetCurrentDC();\n"
     "\tgraphicsBindingOpenGLWin32KHR.hGLRC = wglGetCurrentContext();\n"
     "#else\n"
     "\t// Steam Frame: SDL's X11 window and GLX context, current on this thread (SDL_VIDEODRIVER=x11)\n"
     "\tXrGraphicsBindingOpenGLXlibKHR graphicsBindingOpenGLWin32KHR = {0};\n"
     "\tgraphicsBindingOpenGLWin32KHR.type = XR_TYPE_GRAPHICS_BINDING_OPENGL_XLIB_KHR;\n"
     "\tgraphicsBindingOpenGLWin32KHR.next = NULL;\n"
     "\tgraphicsBindingOpenGLWin32KHR.xDisplay = glXGetCurrentDisplay();\n"
     "\tgraphicsBindingOpenGLWin32KHR.glxDrawable = glXGetCurrentDrawable();\n"
     "\tgraphicsBindingOpenGLWin32KHR.glxContext = glXGetCurrentContext();\n"
     "#endif\n"),
    ("\treturn GetTickCount64();\n",
     "#if defined(_WIN32)\n\treturn GetTickCount64();\n#else\n"
     "\tstruct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);\n"
     "\treturn ts.tv_sec * 1000.0 + ts.tv_nsec / 1000000.0;\n#endif\n"),
])

# The "not Windows" branches are Android's: Linux takes the desktop side.
patch(V + "VrInputDefault.c", [
    ("#ifndef _WIN32\n#include <android/keycodes.h>\n",
     "#if !defined(_WIN32) && !defined(__linux__)\n#include <android/keycodes.h>\n"),
])
patch(V + "VrInputCommon.c", [
    ("#ifndef _WIN32\nvoid PortableMouseAbs(float x,float y);\n#else\n",
     "#if !defined(_WIN32) && !defined(__linux__)\nvoid PortableMouseAbs(float x,float y);\n#else\n"),
    ("    static ox = 0, oy = 0;\n", "    static int ox = 0, oy = 0;\n"),
])

# Input debugging (RTCWXR_DEBUG_INPUT=1 in the environment): every key the VR layer sends, and each change of a
# hand's button mask with the trigger value, in the console log.
patch(V + "VrInputCommon.c", [
    ("    if ((trackedRemoteState->Buttons & button) != (prevTrackedRemoteState->Buttons & button))\n    {\n"
     "        CL_KeyEvent( key, (trackedRemoteState->Buttons & button) != 0, Sys_Milliseconds() );\n",
     "    if ((trackedRemoteState->Buttons & button) != (prevTrackedRemoteState->Buttons & button))\n    {\n"
     "        if (getenv(\"RTCWXR_DEBUG_INPUT\")) Com_Printf(\"vrdebug: key %d %s (button 0x%x, catcher %d)\\n\", key,\n"
     "            (trackedRemoteState->Buttons & button) ? \"down\" : \"up\", button, Key_GetCatcher());\n"
     "        CL_KeyEvent( key, (trackedRemoteState->Buttons & button) != 0, Sys_Milliseconds() );\n"),
])
patch(V + "OpenXrInput.c", [
    ("    if (rightTrackedRemoteState_new.IndexTrigger > 0.5f) rightTrackedRemoteState_new.Buttons |= xrButton_Trigger;\n",
     "    if (rightTrackedRemoteState_new.IndexTrigger > 0.5f) rightTrackedRemoteState_new.Buttons |= xrButton_Trigger;\n"
     "    {\n        static uint32_t dbgL, dbgR;\n"
     "        if (getenv(\"RTCWXR_DEBUG_INPUT\") && (dbgL != leftTrackedRemoteState_new.Buttons || dbgR != rightTrackedRemoteState_new.Buttons)) {\n"
     "            dbgL = leftTrackedRemoteState_new.Buttons; dbgR = rightTrackedRemoteState_new.Buttons;\n"
     "            Com_Printf(\"vrdebug: buttons L=0x%x R=0x%x trigL=%.2f trigR=%.2f gripR=%.2f\\n\", dbgL, dbgR,\n"
     "                leftTrackedRemoteState_new.IndexTrigger, rightTrackedRemoteState_new.IndexTrigger, rightTrackedRemoteState_new.GripTrigger);\n"
     "        }\n    }\n"),
])

# UI-side input debugging (same RTCWXR_DEBUG_INPUT): where the UI cursor is and what has focus when a key arrives.
patch("code/ui/ui_main.c", [
    ("void _UI_KeyEvent( int key, qboolean down ) {\n\n\tif ( Menu_Count() > 0 ) {\n\t\tmenuDef_t *menu = Menu_GetFocused();\n",
     "void _UI_KeyEvent( int key, qboolean down ) {\n\n\tif ( Menu_Count() > 0 ) {\n\t\tmenuDef_t *menu = Menu_GetFocused();\n"
     "\t\tif ( getenv( \"RTCWXR_DEBUG_INPUT\" ) ) {\n"
     "\t\t\tCom_Printf( \"uidebug: key %d down %d cursor %.0f,%.0f scale %.2f bias %.0f,%.0f glconfig %dx%d sizeof(glconfig_t) %d sizeof(vmCvar_t) %d aspect %.3f menus %d itemCount %d\\n\",\n"
     "\t\t\t\tkey, down, uiInfo.uiDC.cursorx, uiInfo.uiDC.cursory, uiInfo.uiDC.xscale, uiInfo.uiDC.xBias, uiInfo.uiDC.yBias,\n"
     "\t\t\t\tuiInfo.uiDC.glconfig.vidWidth, uiInfo.uiDC.glconfig.vidHeight, (int)sizeof(glconfig_t), (int)sizeof(vmCvar_t), ui_vrMenuAspect.value,\n"
     "\t\t\t\tMenu_Count(), menu ? menu->itemCount : -1 );\n"
     "\t\t}\n"),
])
patch("code/client/cl_ui.c", [
    ("\tVM_Call( uivm, UI_INIT, ( clc.state >= CA_AUTHORIZING && clc.state < CA_ACTIVE ), (intptr_t)&vr);\n",
     "\tif ( getenv( \"RTCWXR_DEBUG_INPUT\" ) ) Com_Printf( \"cldebug: glconfig %dx%d sizeof(glconfig_t) %d sizeof(vmCvar_t) %d\\n\",\n"
     "\t\tcls.glconfig.vidWidth, cls.glconfig.vidHeight, (int)sizeof(glconfig_t), (int)sizeof(vmCvar_t) );\n"
     "\tVM_Call( uivm, UI_INIT, ( clc.state >= CA_AUTHORIZING && clc.state < CA_ACTIVE ), (intptr_t)&vr);\n"),
])

# The renderer only starts and stops the VR layer on Windows; Linux is a desktop too.
patch("code/sdl/sdl_glimp.c", [
    ("#if defined(_WIN32)\n\n\tri.VR_Shutdown();\n", "#if defined(_WIN32) || defined(__linux__)\n\n\tri.VR_Shutdown();\n"),
    ("#if defined(_WIN32)\n\n\tri.VR_Init();\n", "#if defined(_WIN32) || defined(__linux__)\n\n\tri.VR_Init();\n"),
])

# C99 "inline" without extern emits no external definition (MSVC does): qagame.sp.so had G_GameSkillIntToStr undefined.
patch("code/game/g_main.c", [
    ("inline const char* G_GameSkillIntToStr( int skill ) {", "/* not inline: C99 would emit no definition */ const char* G_GameSkillIntToStr( int skill ) {"),
])

# A stale generated prototype (GCC 15 treats the mismatch as an error; bg_public.h and the definition say int).
patch("code/game/g_func_decs.h", [
    ("extern qboolean BG_AkimboFireSequence ( int weapon , int akimboClip , int coltClip, qboolean triggerState ) ;",
     "extern qboolean BG_AkimboFireSequence ( int weapon , int akimboClip , int coltClip, int triggerState ) ;"),
])

# The game modules (cgame, game, ui) include VrClientInfo.h too: give their compile rules the include path.
p = os.path.join(root, "Makefile")
s = open(p).read()
tag = "$(BASEGAME_CFLAGS) -I$(MOUNT_DIR)/RealRTCWXR/RealRTCWXR "
if tag not in s:
    s = s.replace("$(BASEGAME_CFLAGS) ", tag)
    open(p, "w").write(s)
    print("patched Makefile (game module include path)")

# Makefile: the OpenXR layer's objects in the client, their compile rules, and the Linux flags and libraries.
patch("Makefile", [
    ("  $(B)/client/con_log.o \\\n  $(B)/client/sys_main.o\n\nifdef MINGW\n",
     "  $(B)/client/con_log.o \\\n  $(B)/client/sys_main.o \\\n  \\\n"
     "  $(B)/client/cl_patrons.o \\\n"
     "  $(B)/client/OpenXrInput.o \\\n  $(B)/client/VrInputCommon.o \\\n  $(B)/client/VrInputDefault.o \\\n"
     "  $(B)/client/VrInputWeaponAlign.o \\\n  $(B)/client/RTCWXR_SurfaceView.o \\\n  $(B)/client/TBXR_Common.o\n\nifdef MINGW\n"),
    ("define DO_CC\n$(echo_cmd) \"CC $<\"\n$(Q)$(CC) $(NOTSHLIBCFLAGS) $(CFLAGS) $(CLIENT_CFLAGS) $(OPTIMIZE) -o $@ -c $<\nendef\n",
     "define DO_CC\n$(echo_cmd) \"CC $<\"\n$(Q)$(CC) $(NOTSHLIBCFLAGS) $(CFLAGS) $(CLIENT_CFLAGS) $(XRCLIENT_CFLAGS) $(OPTIMIZE) -o $@ -c $<\nendef\n"),
    ("$(B)/client/%.o: $(CMDIR)/%.c\n\t$(DO_CC)\n",
     "$(B)/client/%.o: $(CMDIR)/%.c\n\t$(DO_CC)\n\n"
     "$(B)/client/%.o: $(MOUNT_DIR)/RealRTCWXR/RealRTCWXR/%.c\n\t$(DO_CC)\n\n"
     "$(B)/client/%.o: $(MOUNT_DIR)/RealRTCWXR/RealRTCWXR/windows/%.c\n\t$(DO_CC)\n"),
    # the XR fork only maintains rend2 (the legacy renderer no longer compiles: tr_cmds.c 'eye' undeclared)
    ("    TARGETS += $(B)/$(CLIENTBIN)$(FULLBINEXT) $(B)/renderer_sp_opengl1_$(SHLIBNAME)\n",
     "    TARGETS += $(B)/$(CLIENTBIN)$(FULLBINEXT) # Steam Frame: no renderer_sp_opengl1 (unmaintained in the XR fork)\n"),
    ("  ifeq ($(USE_MUMBLE),1)\n    CLIENT_LIBS += -lrt\n  endif\n\nelse # ifeq Linux\n",
     "  ifeq ($(USE_MUMBLE),1)\n    CLIENT_LIBS += -lrt\n  endif\n\n"
     "  # Steam Frame: the RealRTCWXR OpenXR layer built into the client (the Windows build keeps it in a VS project).\n"
     "  # RTCWXR_CLIENT (vr as a struct, not the renderer's pointer) goes to the client objects only: XRCLIENT_CFLAGS in DO_CC.\n"
     "  XRCLIENT_CFLAGS = -DRTCWXR_CLIENT\n"
     "  CLIENT_CFLAGS += -DXR_USE_PLATFORM_XLIB -DXR_USE_GRAPHICS_API_OPENGL -DXR_NO_STDINT_H \\\n"
     "    -I$(MOUNT_DIR)/openxr/include -I$(MOUNT_DIR)/RealRTCWXR/RealRTCWXR\n"
     "  CLIENT_LIBS += /opt/steamvr/bin/linuxarm64/libopenxr_loader.so -Wl,-rpath,/opt/steamvr/bin/linuxarm64 -lGL -lX11\n"
     "\nelse # ifeq Linux\n"),
])
