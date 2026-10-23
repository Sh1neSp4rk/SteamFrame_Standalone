# License note: the replacement source fragments in this file derive from GameOrDie007/Quake-II-PCVR (Yamagi Quake II, Team Beef Quake2Quest), GPL-2.0,
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Port Quake-II-PCVR's OpenXR surface to Linux (GLX / XR_KHR_opengl_enable Xlib binding) for a native
linux-arm64 build on the Steam Frame. Idempotent. Usage: python3 -I q2_port.py <repo dir>"""
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

patch("src/vr/vr_surface.c", [
    ("#include <windows.h>\n#include <GL/gl.h>\n",
     "#ifdef _WIN32\n#include <windows.h>\n#include <GL/gl.h>\n#else\n#include <GL/gl.h>\n#include <GL/glx.h>\n#endif\n"),
    ("#define XR_USE_PLATFORM_WIN32\n#define XR_USE_GRAPHICS_API_OPENGL\n",
     "#ifdef _WIN32\n#define XR_USE_PLATFORM_WIN32\n#else\n#define XR_USE_PLATFORM_XLIB  /* Steam Frame: native linux-arm64, GLX */\n#endif\n"
     "#define XR_USE_GRAPHICS_API_OPENGL\n"),
    ("static qboolean\nq2xr_LoadGL(void)\n{",
     "#ifdef _WIN32\n#define Q2XR_GETPROC(name) wglGetProcAddress(name)\n"
     "typedef XrGraphicsBindingOpenGLWin32KHR q2xr_graphics_binding_t;\n#else\n"
     "#define Q2XR_GETPROC(name) glXGetProcAddressARB((const GLubyte *)(name))\n"
     "typedef XrGraphicsBindingOpenGLXlibKHR q2xr_graphics_binding_t;\n#endif\n\n"
     "static qboolean\nq2xr_LoadGL(void)\n{"),
    ("static qboolean\nq2xr_GetGraphicsBinding(XrGraphicsBindingOpenGLWin32KHR *binding)\n{\n\tHGLRC context",
     "static qboolean\nq2xr_GetGraphicsBinding(q2xr_graphics_binding_t *binding)\n{\n#ifndef _WIN32\n"
     "\tSDL_Window *window = SDL_GL_GetCurrentWindow();\n\tSDL_SysWMinfo wminfo;\n"
     "\tGLXContext glxContext = glXGetCurrentContext();\n\tGLXDrawable drawable = glXGetCurrentDrawable();\n\n"
     "\tSDL_VERSION(&wminfo.version);\n"
     "\tif (window == NULL || glxContext == NULL || !SDL_GetWindowWMInfo(window, &wminfo) ||\n"
     "\t\twminfo.subsystem != SDL_SYSWM_X11)\n\t{\n"
     "\t\tCom_Printf(\"VR: no current GLX context on an X11 window - the window must exist before VR starts\\n\");\n"
     "\t\treturn false;\n\t}\n\n"
     "\tmemset(binding, 0, sizeof(*binding));\n"
     "\tbinding->type = XR_TYPE_GRAPHICS_BINDING_OPENGL_XLIB_KHR;\n"
     "\tbinding->xDisplay = wminfo.info.x11.display;\n"
     "\tbinding->glxDrawable = drawable;\n\tbinding->glxContext = glxContext;\n"
     "\treturn true;\n#else\n\tHGLRC context"),
    ("\tbinding->hDC = dc;\n\tbinding->hGLRC = context;\n\treturn true;\n}",
     "\tbinding->hDC = dc;\n\tbinding->hGLRC = context;\n\treturn true;\n#endif\n}"),
    ("\tXrGraphicsBindingOpenGLWin32KHR graphicsBinding;\n\tXrSessionCreateInfo",
     "\tq2xr_graphics_binding_t graphicsBinding;\n\tXrSessionCreateInfo"),
])
# every wglGetProcAddress("...") call in q2xr_LoadGL
p = os.path.join(root, "src/vr/vr_surface.c")
s = open(p).read()
n = s.count(")wglGetProcAddress(\"")
s = s.replace(")wglGetProcAddress(\"", ")Q2XR_GETPROC(\"")
open(p, "w").write(s)
print("GL entry points via Q2XR_GETPROC:", n)

# Team Beef's Qcommon_Init no longer runs the main loop; only the Windows main.c was updated to bring up the
# VR session and drive frames. Give the Unix main.c the same tail, or the engine just returns and exits.
patch("src/backends/unix/main.c", [
    ('#include "../../common/header/common.h"\n',
     '#include "../../common/header/common.h"\n#ifndef DEDICATED_ONLY\n#include "../../vr/vr_surface.h"\n#endif\n'),
    ("\t// Initialize the game.\n\t// Never returns.\n\tQcommon_Init(argc, argv);\n\n\treturn 0;\n}",
     "\t// Initialize the game. Returns now (Team Beef): the platform layer drives the frames.\n"
     "\tQcommon_Init(argc, argv);\n\n#ifndef DEDICATED_ONLY\n"
     "\t/* Phase two, as in backends/windows/main.c: the window and GL context exist now. */\n"
     "\tif (TBXR_InitialiseSession())\n\t{\n\t\twhile (1)\n\t\t{\n\t\t\tTBXR_FrameSetup();\n\t\t}\n\t}\n\n"
     "\tCom_Printf(\"Running without VR.\\n\");\n#endif\n\n"
     "\t/* Flatscreen, and the dedicated server. */\n\tQcommon_Mainloop();\n\n\treturn 0;\n}"),
])

# Steam Frame left-hand movement (SteamVR binding q2vr_frame_binding.json routes the physical inputs):
#   Frame left grip -> off-hand "trigger" action  = run (unchanged game logic, K_SHIFT)
#   Frame left trigger -> off-hand "squeeze" action = crouch (was two-handed weapon stabilisation)
#   Frame left bumper -> off-hand "b_click" action  = jump (B was only read on the right hand)
patch("src/vr/vr_surface.c", [
    ("\t\taimLocation.next = &velocity;\n",
     "\t\t/* Steam Frame: the left bumper is bound to b_click on the left hand (jump). */\n"
     "\t\tif (hand == 0 && q2xr_GetBoolean(bAction, hand).currentState)\n\t\t{\n"
     "\t\t\tstates[hand]->Buttons |= ovrButton_B;\n\t\t}\n\n"
     "\t\taimLocation.next = &velocity;\n"),
    # zink (GL on Vulkan): finish the eye's rendering before the compositor gets the image. Only the left
    # eye was implicitly flushed (the mirror window presents after it), so the right eye lagged and swam.
    ("\tXrSwapchainImageReleaseInfo releaseInfo = {XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO};\n\n"
     "\tQ2XR_CHECK_XR(xrReleaseSwapchainImage(fb->Handle, &releaseInfo));\n",
     "\tXrSwapchainImageReleaseInfo releaseInfo = {XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO};\n\n"
     "\tglFinish();  /* Steam Frame/zink: the image must be complete before the compositor reads it */\n"
     "\tQ2XR_CHECK_XR(xrReleaseSwapchainImage(fb->Handle, &releaseInfo));\n"),
    # one-time log of both eye poses/FOVs, to compare against the fixed-IPD stereo the renderer uses
    ("\t\t\t&viewCount, gApp.Views));\n",
     "\t\t\t&viewCount, gApp.Views));\n\n"
     "\t{\n\t\tstatic int q2xrViewsLogged;\n\t\tif (q2xrViewsLogged++ == 200)\n\t\t{\n"
     "\t\t\tfor (eye = 0; eye < NUM_EYES; ++eye)\n\t\t\t{\n"
     "\t\t\t\tconst XrView *v = &gApp.Views[eye];\n"
     "\t\t\t\tCom_Printf(\"VR: view %d pos %.4f %.4f %.4f ori %.4f %.4f %.4f %.4f fov %.4f %.4f %.4f %.4f\\n\", eye,\n"
     "\t\t\t\t\tv->pose.position.x, v->pose.position.y, v->pose.position.z,\n"
     "\t\t\t\t\tv->pose.orientation.x, v->pose.orientation.y, v->pose.orientation.z, v->pose.orientation.w,\n"
     "\t\t\t\t\tv->fov.angleLeft, v->fov.angleRight, v->fov.angleUp, v->fov.angleDown);\n"
     "\t\t\t}\n\t\t}\n\t}\n"),
])
patch("src/vr/teambeef/VrInputDefault.c", [
    ("        //Turn on weapon stabilisation?\n"
     "        if ((pOffTrackedRemoteNew->Buttons & ovrButton_GripTrigger) !=\n"
     "            (pOffTrackedRemoteOld->Buttons & ovrButton_GripTrigger)) {\n",
     "        /* Steam Frame: the off-hand grip action (Frame left trigger) crouches instead of\n"
     "           turning on two-handed weapon stabilisation. */\n"
     "        if ((pOffTrackedRemoteNew->Buttons & ovrButton_GripTrigger) !=\n"
     "            (pOffTrackedRemoteOld->Buttons & ovrButton_GripTrigger)) {\n"
     "            sendButtonAction(\"+movedown\", (pOffTrackedRemoteNew->Buttons & ovrButton_GripTrigger) != 0);\n"
     "        }\n"
     "        if (0) {\n"),
    ("            //Jump (B Button)\n"
     "            handleTrackedControllerButton(primaryButtonsNew,\n"
     "                                          primaryButtonsOld, primaryButton2, K_SPACE);\n",
     "            //Jump (B Button)\n"
     "            handleTrackedControllerButton(primaryButtonsNew,\n"
     "                                          primaryButtonsOld, primaryButton2, K_SPACE);\n"
     "            /* Steam Frame: off-hand B (left bumper) jumps too */\n"
     "            handleTrackedControllerButton(pOffTrackedRemoteNew->Buttons,\n"
     "                                          pOffTrackedRemoteOld->Buttons, ovrButton_B, K_SPACE);\n"),
])

patch("CMakeLists.txt", [
    ("\ttarget_link_libraries(quake2 ${yquake2LinkerFlags} ${yquake2ClientLinkerFlags}\n"
     "\t\t\t${yquake2SDLLinkerFlags} ${yquake2ZLibLinkerFlags})\n",
     "\ttarget_link_libraries(quake2 ${yquake2LinkerFlags} ${yquake2ClientLinkerFlags}\n"
     "\t\t\t${yquake2SDLLinkerFlags} ${yquake2ZLibLinkerFlags}\n"
     "\t\t\t${OPENXR_LOADER_LIBRARY} GL dl)  # Steam Frame: native OpenXR + GLX\n"
     "\ttarget_include_directories(quake2 PRIVATE ${OPENXR_INCLUDE_DIR})\n"),
])
