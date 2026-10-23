#!/usr/bin/env python3
# License note: the replacement source fragments in this file derive from Team-Beef-Studios/CSVR's xash3d-fwgs fork (Xash3D FWGS, GPL-3.0),
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Port Team Beef's CSVR engine (Xash3D FWGS fork, OpenXR for Android/GLES) to the Steam Frame:
native linux-arm64, desktop OpenGL through GLX, SteamVR's OpenXR runtime. Idempotent: each patch is skipped when its
replacement is already present. Run from anywhere; edits ~/PCVR/CSVR/src/3rdparty/xash3d-fwgs in place."""
import pathlib, re, sys

E = pathlib.Path.home() / "PCVR/CSVR/src/3rdparty/xash3d-fwgs"
MARK = "Steam Frame"
failed = []

def patch(rel, pairs):
    p = E / rel
    s = p.read_text()
    changed = False
    for old, new in pairs:
        if new in s:
            continue
        n = s.count(old)
        if n != 1:
            failed.append(f"{rel}: expected 1 match, found {n}: {old[:70]!r}")
            continue
        s = s.replace(old, new); changed = True
    if changed:
        p.write_text(s); print("patched", rel)

# ---------------------------------------------------------------- VrBase.h
patch("engine/vr/VrBase.h", [
    ("#else\n#include <cstdio>\n#define ALOGE(...) printf(__VA_ARGS__)\n#define ALOGV(...) printf(__VA_ARGS__)\n#endif",
     "#else // Steam Frame: plain stdout logging\n#include <stdio.h>\n"
     "#define ALOGE(...) do { printf(\"OpenXR: \" __VA_ARGS__); printf(\"\\n\"); fflush(stdout); } while (0)\n"
     "#define ALOGV(...) do { if (getenv(\"CSVR_XR_VERBOSE\")) { printf(\"OpenXR: \" __VA_ARGS__); printf(\"\\n\"); } } while (0)\n"
     "#include <stdlib.h>\n#endif"),
    ("#define XR_USE_GRAPHICS_API_OPENGL_ES 1\n#endif\n",
     "#define XR_USE_GRAPHICS_API_OPENGL_ES 1\n#else\n"
     "// Steam Frame: desktop OpenGL; the Xlib session binding is only declared in VrBase.c\n"
     "#define XR_USE_GRAPHICS_API_OPENGL 1\n#endif\n"),
    ("#include <stdbool.h>\n#include <jni.h>\n",
     "#include <stdbool.h>\n#ifdef ANDROID\n#include <jni.h>\n#else\n"
     "// Steam Frame: the GL swapchain image struct has the same layout as the GLES one\n"
     "#define XrSwapchainImageOpenGLESKHR XrSwapchainImageOpenGLKHR\n"
     "#define XR_TYPE_SWAPCHAIN_IMAGE_OPENGL_ES_KHR XR_TYPE_SWAPCHAIN_IMAGE_OPENGL_KHR\n#endif\n"),
    ("typedef struct\n{\n\tEGLint\t\tMajorVersion;",
     "#ifdef ANDROID // Steam Frame: EGL only on Android\ntypedef struct\n{\n\tEGLint\t\tMajorVersion;"),
    ("\tEGLContext\tContext;\n} ovrEgl;\n", "\tEGLContext\tContext;\n} ovrEgl;\n#endif\n"),
])

# ---------------------------------------------------------------- VrBase.c
patch("engine/vr/VrBase.c", [
    ('#include "VrBase.h"\n',
     "#ifndef ANDROID // Steam Frame: GLX session binding\n#include <X11/Xlib.h>\n#include <GL/glx.h>\n"
     "#define XR_USE_PLATFORM_XLIB 1\n#endif\n#include \"VrBase.h\"\n"),
    ("#ifdef ANDROID\n\tif (XR_ExtensionSupported(XR_KHR_OPENGL_ES_ENABLE_EXTENSION_NAME",
     "#ifndef ANDROID // Steam Frame: desktop OpenGL\n"
     "\tif (XR_ExtensionSupported(XR_KHR_OPENGL_ENABLE_EXTENSION_NAME, runtimeExtProps, runtimeExtCount)) {\n"
     "\t\textensions[extensionsCount++] = XR_KHR_OPENGL_ENABLE_EXTENSION_NAME;\n"
     "\t} else {\n\t\tALOGE(\"OpenXR runtime does not support %s\", XR_KHR_OPENGL_ENABLE_EXTENSION_NAME);\n\t\texit(1);\n\t}\n"
     "\tALOGE(\"cylinder layers %s\", XR_ExtensionSupported(XR_KHR_COMPOSITION_LAYER_CYLINDER_EXTENSION_NAME, runtimeExtProps, runtimeExtCount) ? \"supported\" : \"NOT supported\");\n"
     "#endif\n"
     "#ifdef ANDROID\n\tif (XR_ExtensionSupported(XR_KHR_OPENGL_ES_ENABLE_EXTENSION_NAME"),
    ("\tappInfo.apiVersion = XR_CURRENT_API_VERSION;\n",
     "#ifdef ANDROID\n\tappInfo.apiVersion = XR_CURRENT_API_VERSION;\n#else\n"
     "\tappInfo.apiVersion = XR_API_VERSION_1_0; // Steam Frame: SteamVR's runtime is OpenXR 1.0\n#endif\n"),
    ("\tOXR(pfnGetOpenGLESGraphicsRequirementsKHR(vr_engine.appState.Instance, systemId, &graphicsRequirements));\n#endif\n",
     "\tOXR(pfnGetOpenGLESGraphicsRequirementsKHR(vr_engine.appState.Instance, systemId, &graphicsRequirements));\n#else\n"
     "\t// Steam Frame: the spec requires this call before xrCreateSession\n"
     "\tPFN_xrGetOpenGLGraphicsRequirementsKHR pfnGetOpenGLGraphicsRequirementsKHR = NULL;\n"
     "\tOXR(xrGetInstanceProcAddr(vr_engine.appState.Instance, \"xrGetOpenGLGraphicsRequirementsKHR\",\n"
     "\t\t\t(PFN_xrVoidFunction*)(&pfnGetOpenGLGraphicsRequirementsKHR)));\n"
     "\tXrGraphicsRequirementsOpenGLKHR graphicsRequirements = {XR_TYPE_GRAPHICS_REQUIREMENTS_OPENGL_KHR};\n"
     "\tif (pfnGetOpenGLGraphicsRequirementsKHR) pfnGetOpenGLGraphicsRequirementsKHR(vr_engine.appState.Instance, systemId, &graphicsRequirements);\n"
     "#endif\n"),
    ("\tsessionCreateInfo.next = &graphicsBindingGL;\n#endif\n\tsessionCreateInfo.type = XR_TYPE_SESSION_CREATE_INFO;",
     "\tsessionCreateInfo.next = &graphicsBindingGL;\n#else\n"
     "\t// Steam Frame: SDL's X11 window and GLX context, current on this thread (SDL_VIDEODRIVER=x11)\n"
     "\tXrGraphicsBindingOpenGLXlibKHR graphicsBindingGL = {XR_TYPE_GRAPHICS_BINDING_OPENGL_XLIB_KHR};\n"
     "\tgraphicsBindingGL.xDisplay = glXGetCurrentDisplay();\n"
     "\tgraphicsBindingGL.glxDrawable = glXGetCurrentDrawable();\n"
     "\tgraphicsBindingGL.glxContext = glXGetCurrentContext();\n"
     "\tif (!graphicsBindingGL.xDisplay || !graphicsBindingGL.glxContext) ALOGE(\"no current GLX context for the session\");\n"
     "\tsessionCreateInfo.next = &graphicsBindingGL;\n"
     "#endif\n\tsessionCreateInfo.type = XR_TYPE_SESSION_CREATE_INFO;"),
    ("\tengine->appState.RenderThreadTid = gettid();\n",
     "#ifdef ANDROID\n\tengine->appState.RenderThreadTid = gettid();\n#endif\n"),
    ("engine_t* VR_GetEngine( void ) {\n\treturn &vr_engine;\n}",
     "#ifndef ANDROID\n"
     "// Steam Frame: no Android_Init here, so the instance is created on first use (video init asks for the resolution\n"
     "// before the first frame). Same flags the Quest build uses by default.\n"
     "static void VR_FrameInit(void) {\n"
     "\tstatic int busy;\n\tif (vr_initialized || busy) return;\n\tbusy = 1;\n"
     "\tVR_SetPlatformFLag(VR_PLATFORM_CONTROLLER_QUEST, true);\n"
     "\tVR_SetPlatformFLag(VR_PLATFORM_VIEWPORT_SQUARE, true);\n"
     "\tVR_Init(NULL, \"Xash-FWGS\", 1);\n\tbusy = 0;\n}\n#endif\n"
     "engine_t* VR_GetEngine( void ) {\n#ifndef ANDROID\n\tVR_FrameInit();\n#endif\n\treturn &vr_engine;\n}"),
])

# ---------------------------------------------------------------- VrFramebuffer.c
patch("engine/vr/VrFramebuffer.c", [
    ("#include <GLES3/gl3.h>\n#include <GLES3/gl32.h>\n#include <GLES3/gl3ext.h>\n#include <GLES2/gl2ext.h>\n",
     "#ifdef ANDROID\n#include <GLES3/gl3.h>\n#include <GLES3/gl32.h>\n#include <GLES3/gl3ext.h>\n#include <GLES2/gl2ext.h>\n#else\n"
     "// Steam Frame: desktop GL (Mesa zink); extension entry points come from GLX\n"
     "#define GL_GLEXT_PROTOTYPES 1\n#include <GL/gl.h>\n#include <GL/glext.h>\n#include <GL/glx.h>\n"
     "#define eglGetProcAddress(n) glXGetProcAddressARB((const GLubyte*)(n))\n"
     "#ifndef GL_APIENTRYP\n#define GL_APIENTRYP APIENTRYP\n#endif\n#ifndef GL_APIENTRY\n#define GL_APIENTRY APIENTRY\n#endif\n#endif\n"),
    ("void ovrEgl_Clear( ovrEgl * egl )\n", "#ifdef ANDROID // Steam Frame: EGL only on Android\nvoid ovrEgl_Clear( ovrEgl * egl )\n"),
])
s = (E / "engine/vr/VrFramebuffer.c").read_text()
if "#endif // ovrEgl" not in s:
    i = s.index("void ovrEgl_Clear")
    j = s.index("/*\n====", i)
    s = s[:j] + "#endif // ovrEgl\n\n" + s[j:]
    (E / "engine/vr/VrFramebuffer.c").write_text(s)

s = (E / "engine/vr/VrFramebuffer.h").read_text()
if "Steam Frame" not in s:
    s = re.sub(r"(void ovrEgl_Clear\([^\n]*\n)(void ovrEgl_CreateContext\([^\n]*\n)",
               r"#ifdef ANDROID // Steam Frame: EGL only on Android\n\1\2#endif\n", s, count=1)
    assert "Steam Frame" in s, "VrFramebuffer.h ovrEgl prototypes not found"
    (E / "engine/vr/VrFramebuffer.h").write_text(s); print("patched engine/vr/VrFramebuffer.h")

# ---------------------------------------------------------------- VrRenderer.c: the menu canvas aspect
patch("engine/vr/VrRenderer.c", [
    ("bool VR_DidRecenter() {",
     "#ifndef ANDROID\n// Steam Frame: Android_Init sets the menu canvas aspect; do it on the first renderer init instead\n"
     "static int frame_aspect_set;\n#endif\nbool VR_DidRecenter() {"),
    ("\tint eyeW, eyeH;\n\tVR_GetResolution(engine, &eyeW, &eyeH);",
     "\tint eyeW, eyeH;\n#ifndef ANDROID\n\tif (!frame_aspect_set) { VR_SetConfigFloat(VR_CONFIG_CANVAS_ASPECT, 4.0f / 3.0f); frame_aspect_set = 1; }\n#endif\n"
     "\tVR_GetResolution(engine, &eyeW, &eyeH);"),
])

# ---------------------------------------------------------------- VrHaptics: external Android haptics service only
patch("engine/vr/VrHaptics.h", [
    ("#include <jni.h>\n", "#ifdef ANDROID\n#include <jni.h>\n#else\ntypedef void *jobject; // Steam Frame: no haptics service\n#endif\n"),
])
s = (E / "engine/vr/VrHaptics.c").read_text()
if "Steam Frame" not in s:
    s = ("#ifdef ANDROID\n" + s + "\n#else\n// Steam Frame: bHaptics-style external service is Android-only; controller rumble stays in VrInput.c\n"
         "#include \"VrHaptics.h\"\n"
         "void VR_Haptics_OnCreate(jobject context) {}\nvoid VR_Haptics_OnDestroy() {}\nvoid VR_Haptics_Disable() {}\n"
         "void VR_Haptics_Enable() {}\n"
         "void VR_Haptics_Event(const char *event, int position, int flags, int intensity, float angle, float yHeight) {}\n"
         "void VR_Haptics_UpdateEvent(const char *event, int intensity, float angle) {}\n"
         "void VR_Haptics_StopEvent(const char *event) {}\nvoid VR_Haptics_EndFrame() {}\n#endif\n")
    (E / "engine/vr/VrHaptics.c").write_text(s); print("patched engine/vr/VrHaptics.c")

# ---------------------------------------------------------------- host_vr.c: nothing needed (sdl_keyboard_requested lives in
# in_sdl.c); undo an earlier version of this script that defined it twice
p = E / "engine/common/host_vr.c"; s = p.read_text()
old = ("#ifdef ANDROID\nextern bool sdl_keyboard_requested;\n#else\n"
       "bool sdl_keyboard_requested = false; // Steam Frame: set by the Android keyboard bridge\n#endif\n")
if old in s:
    p.write_text(s.replace(old, "extern bool sdl_keyboard_requested;\n")); print("reverted engine/common/host_vr.c")

# ---------------------------------------------------------------- vid_sdl.c: one swap per eye would stall twice a frame
patch("engine/platform/sdl/vid_sdl.c", [
    ("\tSDL_GL_SwapWindow( host.hWnd );\n",
     "\t{ // Steam Frame: the renderer swaps once per eye; the desktop window is not shown in VR, so skip it\n"
     "\t\tstatic int swap = -1;\n\t\tif( swap < 0 ) swap = getenv( \"CSVR_DESKTOP_SWAP\" ) != NULL;\n"
     "\t\tif( swap ) SDL_GL_SwapWindow( host.hWnd );\n\t}\n"),
])

# ---------------------------------------------------------------- ref_common.c: VR forces the GLES3 renderer first; a failed
# load pops a blocking warning box. Desktop GL on the Frame.
patch("engine/client/ref_common.c", [
    ("\tsuccess = R_LoadRenderer( \"gles3compat\" ); //VR always uses GLESv3\n",
     "#ifdef ANDROID\n\tsuccess = R_LoadRenderer( \"gles3compat\" ); //VR always uses GLESv3\n#else\n"
     "\tsuccess = R_LoadRenderer( \"gl\" ); // Steam Frame: desktop OpenGL (zink), GLX for the OpenXR binding\n#endif\n"),
])

# ---------------------------------------------------------------- cl_game.c: CL_FindModelIndex reads cl.models[i+1] up to
# i = ARRAYSIZE-1, one past the end; on this build the next field is non-zero and gets dereferenced (crash at 0x2)
patch("engine/client/cl_game.c", [
    ("\tfor( i = 0; i < ARRAYSIZE(cl.models); i++ )\n\t{\n\t\tif( !cl.models[i+1] )\n\t\t\tcontinue;\n",
     "\tfor( i = 0; i < ARRAYSIZE(cl.models) - 1; i++ ) // Steam Frame: was one past the end\n\t{\n\t\tif( !cl.models[i+1] )\n\t\t\tcontinue;\n"),
])

# ---------------------------------------------------------------- VrRenderer.c: SteamVR on the Frame has no cylinder layers;
# show the menu/flat canvas as a quad with the arc's width, where the arc is (axis 5 m ahead + 12 m radius)
patch("engine/vr/VrBase.h", [
    ("\tXrCompositionLayerCylinderKHR Cylinder;\n",
     "\tXrCompositionLayerCylinderKHR Cylinder;\n\tXrCompositionLayerQuad Quad; // Steam Frame: no cylinder support in SteamVR\n"),
])
patch("engine/vr/VrBase.c", [
    ("static bool g_hasDisplayRefreshRateExt = false;\n",
     "static bool g_hasDisplayRefreshRateExt = false;\nbool vr_has_cylinder = false; // Steam Frame: else the flat canvas is a quad layer\n"),
    ("\tif (XR_ExtensionSupported(XR_KHR_COMPOSITION_LAYER_CYLINDER_EXTENSION_NAME, runtimeExtProps, runtimeExtCount)) {\n"
     "\t\textensions[extensionsCount++] = XR_KHR_COMPOSITION_LAYER_CYLINDER_EXTENSION_NAME;\n",
     "\tif (XR_ExtensionSupported(XR_KHR_COMPOSITION_LAYER_CYLINDER_EXTENSION_NAME, runtimeExtProps, runtimeExtCount)) {\n"
     "\t\tvr_has_cylinder = true;\n"
     "\t\textensions[extensionsCount++] = XR_KHR_COMPOSITION_LAYER_CYLINDER_EXTENSION_NAME;\n"),
])
patch("engine/vr/VrRenderer.c", [
    ("\t\t// Build the cylinder layer\n\t\tif (vrMode == VR_MODE_MONO_SCREEN) {\n",
     "\t\t// Build the cylinder layer\n"
     "\t\textern bool vr_has_cylinder;\n"
     "\t\tif (!vr_has_cylinder) {\n"
     "\t\t\t// Steam Frame: SteamVR has no XR_KHR_composition_layer_cylinder. Use a flat quad facing the player with the\n"
     "\t\t\t// cylinder's arc length (radius 12 * 90 deg) as its width, one layer for both eyes (per-eye quads are rejected).\n"
     "\t\t\tXrCompositionLayerQuad quad_layer = {};\n"
     "\t\t\tquad_layer.type = XR_TYPE_COMPOSITION_LAYER_QUAD;\n"
     "\t\t\tquad_layer.space = cylinder_layer.space;\n"
     "\t\t\tquad_layer.eyeVisibility = XR_EYE_VISIBILITY_BOTH;\n"
     "\t\t\tquad_layer.subImage = cylinder_layer.subImage;\n"
     "\t\t\tquad_layer.subImage.imageArrayIndex = 0;\n"
     "\t\t\tquad_layer.pose = cylinder_layer.pose;\n"
     "\t\t\tfloat qw = cylinder_layer.radius * cylinder_layer.centralAngle;\n"
     "\t\t\tfloat qa = cylinder_layer.aspectRatio > 0 ? cylinder_layer.aspectRatio : 4.0f / 3.0f;\n"
     "\t\t\tquad_layer.size.width = qw;\n\t\t\tquad_layer.size.height = qw / qa;\n"
     "\t\t\t// the cylinder's pose is its axis; the arc the player sees is radius metres further along the view direction\n"
     "\t\t\tquad_layer.pose.position.x = cylinder_layer.pose.position.x - sinf(menuYaw) * cylinder_layer.radius;\n"
     "\t\t\tquad_layer.pose.position.z = cylinder_layer.pose.position.z - cosf(menuYaw) * cylinder_layer.radius;\n"
     "\t\t\tlayerUnion[layerCount++].Quad = quad_layer;\n"
     "\t\t} else if (vrMode == VR_MODE_MONO_SCREEN) {\n"),
])

# ---------------------------------------------------------------- Frame-only inputs: the Touch action set has no bumpers or
# view button, and the standard Frame layout needs them. Three extra boolean actions (left out of the Touch suggestions;
# the Frame binding maps them), mapped to spare ovrButton bits and given console variables like the other buttons.
# Grips count as pressed at 80% (user rule) instead of 50%.
patch("engine/vr/VrInput.c", [
    ("XrAction menuAction;\n",
     "XrAction menuAction;\nXrAction bumperLeftAction, bumperRightAction, viewAction; // Steam Frame: bumpers + view\n"),
    ("\tvibrateRightFeedback = CreateAction(runningActionSet, XR_ACTION_TYPE_VIBRATION_OUTPUT, \"vibrate_right_feedback\", \"Vibrate Right Controller Feedback\", 0, NULL);\n",
     "\tvibrateRightFeedback = CreateAction(runningActionSet, XR_ACTION_TYPE_VIBRATION_OUTPUT, \"vibrate_right_feedback\", \"Vibrate Right Controller Feedback\", 0, NULL);\n"
     "\tbumperLeftAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"bumper_left\", \"Bumper left\", 0, NULL); // Steam Frame\n"
     "\tbumperRightAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"bumper_right\", \"Bumper right\", 0, NULL);\n"
     "\tviewAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"view_button\", \"View\", 0, NULL);\n"),
    ("\tif (GetActionStateBoolean(menuAction).currentState) lButtons |= ovrButton_Enter;\n",
     "\tif (GetActionStateBoolean(menuAction).currentState) lButtons |= ovrButton_Enter;\n"
     "\tif (GetActionStateBoolean(bumperLeftAction).currentState) lButtons |= ovrButton_LShoulder; // Steam Frame\n"
     "\tif (GetActionStateBoolean(viewAction).currentState) lButtons |= ovrButton_Back;\n"
     "\tif (GetActionStateBoolean(bumperRightAction).currentState) rButtonsFrame |= ovrButton_RShoulder;\n"),
    ("\tlButtons = 0;\n\tif (GetActionStateBoolean(menuAction)",
     "\tlButtons = 0;\n\tuint32_t rButtonsFrame = 0; // Steam Frame\n\tif (GetActionStateBoolean(menuAction)"),
    ("\tif (GetActionStateFloat(gripLeftAction).currentState > 0.5f) lButtons |= ovrButton_GripTrigger;\n",
     "\tif (GetActionStateFloat(gripLeftAction).currentState > 0.8f) lButtons |= ovrButton_GripTrigger; // Steam Frame: 80%\n"),
    ("\trButtons = 0;\n", "\trButtons = rButtonsFrame;\n"),
    ("\tif (GetActionStateFloat(gripRightAction).currentState > 0.5f) rButtons |= ovrButton_GripTrigger;\n",
     "\tif (GetActionStateFloat(gripRightAction).currentState > 0.8f) rButtons |= ovrButton_GripTrigger; // Steam Frame: 80%\n"),
])
patch("engine/common/host_vr.c", [
    ("CVAR_DEFINE_AUTO( vr_button_trigger_right, \"+attack\", FCVAR_ARCHIVE, \"Controller mapping\" );\n",
     "CVAR_DEFINE_AUTO( vr_button_trigger_right, \"+attack\", FCVAR_ARCHIVE, \"Controller mapping\" );\n"
     "CVAR_DEFINE_AUTO( vr_button_bumper_left, \"+jump\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"
     "CVAR_DEFINE_AUTO( vr_button_bumper_right, \"+attack2\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"
     "CVAR_DEFINE_AUTO( vr_button_view, \"+vr_scoreboard\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"),
    ("\tCvar_RegisterVariable( &vr_button_trigger_right );\n",
     "\tCvar_RegisterVariable( &vr_button_trigger_right );\n"
     "\tCvar_RegisterVariable( &vr_button_bumper_left ); // Steam Frame\n"
     "\tCvar_RegisterVariable( &vr_button_bumper_right );\n\tCvar_RegisterVariable( &vr_button_view );\n"),
    ("\tHost_VRButtonMap(ovrButton_GripTrigger, lbuttons, lastlbuttons, \"vr_button_grip_left\", alt);\n\tlastlbuttons = lbuttons;\n",
     "\tHost_VRButtonMap(ovrButton_GripTrigger, lbuttons, lastlbuttons, \"vr_button_grip_left\", alt);\n"
     "\tHost_VRButtonMap(ovrButton_LShoulder, lbuttons, lastlbuttons, \"vr_button_bumper_left\", false); // Steam Frame\n"
     "\tHost_VRButtonMap(ovrButton_Back, lbuttons, lastlbuttons, \"vr_button_view\", false);\n"
     "\tlastlbuttons = lbuttons;\n"),
    ("\tHost_VRButtonMap(ovrButton_GripTrigger, rbuttons, lastrbuttons, \"vr_button_grip_right\", alt);\n\tlastrbuttons = rbuttons;\n",
     "\tHost_VRButtonMap(ovrButton_GripTrigger, rbuttons, lastrbuttons, \"vr_button_grip_right\", alt);\n"
     "\tHost_VRButtonMap(ovrButton_RShoulder, rbuttons, lastrbuttons, \"vr_button_bumper_right\", false); // Steam Frame\n"
     "\tlastrbuttons = rbuttons;\n"),
])

# ---------------------------------------------------------------- d-pad actions + Touch suggestions for every Frame action.
# SteamVR only knows actions that appear in the app's suggested bindings, and drops a whole custom binding file that
# names an unknown action ("Loading 0 bindings"). The Touch suggestions below are only a fallback for non-Frame
# controllers; on the Frame the custom frame_controller binding replaces them.
patch("engine/vr/VrInput.c", [
    ("XrAction bumperLeftAction, bumperRightAction, viewAction; // Steam Frame: bumpers + view\n",
     "XrAction bumperLeftAction, bumperRightAction, viewAction; // Steam Frame: bumpers + view\n"
     "XrAction dpadUpAction, dpadDownAction, dpadLeftAction, dpadRightAction; // Steam Frame: left d-pad\n"
     "#define FRAME_DPAD_UP 0x00001000 // spare ovrButton bits (left hand)\n#define FRAME_DPAD_DOWN 0x00002000\n"
     "#define FRAME_DPAD_LEFT 0x00004000\n#define FRAME_DPAD_RIGHT 0x00008000\n"),
    ("\tviewAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"view_button\", \"View\", 0, NULL);\n",
     "\tviewAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"view_button\", \"View\", 0, NULL);\n"
     "\tdpadUpAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"dpad_up\", \"D-pad up\", 0, NULL);\n"
     "\tdpadDownAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"dpad_down\", \"D-pad down\", 0, NULL);\n"
     "\tdpadLeftAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"dpad_left\", \"D-pad left\", 0, NULL);\n"
     "\tdpadRightAction = CreateAction(runningActionSet, XR_ACTION_TYPE_BOOLEAN_INPUT, \"dpad_right\", \"D-pad right\", 0, NULL);\n"),
    ("\tbindings[currBinding++] = ActionSuggestedBinding(handPoseRightAction, \"/user/hand/right/input/aim/pose\");\n",
     "\tbindings[currBinding++] = ActionSuggestedBinding(handPoseRightAction, \"/user/hand/right/input/aim/pose\");\n"
     "\t// Steam Frame: make the Frame-only actions known to SteamVR (fallback paths for Touch-style controllers)\n"
     "\tbindings[currBinding++] = ActionSuggestedBinding(bumperLeftAction, \"/user/hand/left/input/x/click\");\n"
     "\tbindings[currBinding++] = ActionSuggestedBinding(bumperRightAction, \"/user/hand/right/input/a/click\");\n"
     "\tbindings[currBinding++] = ActionSuggestedBinding(viewAction, \"/user/hand/left/input/y/click\");\n"
     "\tbindings[currBinding++] = ActionSuggestedBinding(dpadUpAction, \"/user/hand/left/input/thumbstick/click\");\n"
     "\tbindings[currBinding++] = ActionSuggestedBinding(dpadDownAction, \"/user/hand/right/input/thumbstick/click\");\n"
     "\tbindings[currBinding++] = ActionSuggestedBinding(dpadLeftAction, \"/user/hand/left/input/menu/click\");\n"
     "\tbindings[currBinding++] = ActionSuggestedBinding(dpadRightAction, \"/user/hand/right/input/b/click\");\n"),
    ("\tif (GetActionStateBoolean(viewAction).currentState) lButtons |= ovrButton_Back;\n",
     "\tif (GetActionStateBoolean(viewAction).currentState) lButtons |= ovrButton_Back;\n"
     "\tif (GetActionStateBoolean(dpadUpAction).currentState) lButtons |= FRAME_DPAD_UP;\n"
     "\tif (GetActionStateBoolean(dpadDownAction).currentState) lButtons |= FRAME_DPAD_DOWN;\n"
     "\tif (GetActionStateBoolean(dpadLeftAction).currentState) lButtons |= FRAME_DPAD_LEFT;\n"
     "\tif (GetActionStateBoolean(dpadRightAction).currentState) lButtons |= FRAME_DPAD_RIGHT;\n"),
])
patch("engine/common/host_vr.c", [
    ("CVAR_DEFINE_AUTO( vr_button_view, \"+vr_scoreboard\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n",
     "CVAR_DEFINE_AUTO( vr_button_view, \"+vr_scoreboard\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"
     "CVAR_DEFINE_AUTO( vr_button_dpad_up, \"\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"
     "CVAR_DEFINE_AUTO( vr_button_dpad_down, \"\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"
     "CVAR_DEFINE_AUTO( vr_button_dpad_left, \"\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"
     "CVAR_DEFINE_AUTO( vr_button_dpad_right, \"\", FCVAR_ARCHIVE, \"Controller mapping (Steam Frame)\" );\n"),
    ("\tCvar_RegisterVariable( &vr_button_bumper_right );\n\tCvar_RegisterVariable( &vr_button_view );\n",
     "\tCvar_RegisterVariable( &vr_button_bumper_right );\n\tCvar_RegisterVariable( &vr_button_view );\n"
     "\tCvar_RegisterVariable( &vr_button_dpad_up );\n\tCvar_RegisterVariable( &vr_button_dpad_down );\n"
     "\tCvar_RegisterVariable( &vr_button_dpad_left );\n\tCvar_RegisterVariable( &vr_button_dpad_right );\n"),
    ("\tHost_VRButtonMap(ovrButton_Back, lbuttons, lastlbuttons, \"vr_button_view\", false);\n",
     "\tHost_VRButtonMap(ovrButton_Back, lbuttons, lastlbuttons, \"vr_button_view\", false);\n"
     "\tHost_VRButtonMap(0x00001000, lbuttons, lastlbuttons, \"vr_button_dpad_up\", false); // Steam Frame d-pad (VrInput.c bits)\n"
     "\tHost_VRButtonMap(0x00002000, lbuttons, lastlbuttons, \"vr_button_dpad_down\", false);\n"
     "\tHost_VRButtonMap(0x00004000, lbuttons, lastlbuttons, \"vr_button_dpad_left\", false);\n"
     "\tHost_VRButtonMap(0x00008000, lbuttons, lastlbuttons, \"vr_button_dpad_right\", false);\n"),
])

# ---------------------------------------------------------------- engine/wscript: link GL/X11 + SteamVR's loader off Android
patch("engine/wscript", [
    ("\t\t\tlib=['GLESv3', 'EGL', 'openxr_loader'],\n\t\t\tlibpath=['../3rdparty/openxr/lib/android/arm64-v8a']\n",
     "\t\t\t# Steam Frame: desktop GL + X11 and SteamVR's linuxarm64 OpenXR loader off Android\n"
     "\t\t\tlib=(['GLESv3', 'EGL', 'openxr_loader'] if bld.env.DEST_OS == 'android' else ['GL', 'X11', 'openxr_loader']),\n"
     "\t\t\tlibpath=(['../3rdparty/openxr/lib/android/arm64-v8a'] if bld.env.DEST_OS == 'android' else ['/opt/steamvr/bin/linuxarm64'])\n"),
])

if failed:
    print("FAILED:\n  " + "\n  ".join(failed)); sys.exit(1)
print("port patches applied")
