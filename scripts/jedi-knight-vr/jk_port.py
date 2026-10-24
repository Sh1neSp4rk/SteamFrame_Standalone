#!/usr/bin/env python3
# License note: the replacement source fragments in this file derive from Patola/JKXRL (Team Beef JKXR, OpenJK; GPL-2.0),
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Steam Frame patches for JKXRL (Patola's Linux fork of Team Beef's JKXR; Vulkan + OpenXR). Idempotent; edits
~/PCVR/JKXR/src/OpenJK in place. Called by jk_build.sh before every build."""
import pathlib, sys

S = pathlib.Path.home() / "PCVR/JKXR/src/OpenJK"
failed = []

def patch(rel, pairs):
    p = S / rel
    s = p.read_text()
    changed = False
    for old, new in pairs:
        if new in s:
            continue
        n = s.count(old)
        if n != 1:
            failed.append(f"{rel}: expected 1 match, found {n}: {old[:70]!r}"); continue
        s = s.replace(old, new); changed = True
    if changed:
        p.write_text(s); print("patched", rel)

patch("code/rd-vulkan/vk_backend.cpp", [
    # 1. Menu/cinematic panel: the quad was blended by the menu art's own alpha, so dark menu colours with low alpha
    #    showed the world through them on SteamVR ("green screen" look). Opaque unless JKXR_SCREEN_ALPHA=1.
    ("\t\tscreenLayer.layerFlags = XR_COMPOSITION_LAYER_BLEND_TEXTURE_SOURCE_ALPHA_BIT;\n",
     "\t\t// Steam Frame: opaque panel; SteamVR honours the menu art's alpha and parts of the menus turned see-through\n"
     "\t\tscreenLayer.layerFlags = getenv( \"JKXR_SCREEN_ALPHA\" ) ? XR_COMPOSITION_LAYER_BLEND_TEXTURE_SOURCE_ALPHA_BIT : 0;\n"),
    # 2. Render resolution: every eye buffer uses the runtime's recommended size (1728x1728 on the Frame, ~6 Mpx for
    #    both eyes). JKXR_RES_SCALE (0.4..1.5) scales it once, here, so all swapchains/framebuffers follow.
    ("\treturn VK_CheckXr( xrEnumerateViewConfigurationViews(\n\t\tvk.xrInstance,\n\t\tvk.xrSystemId,\n"
     "\t\tXR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO,\n\t\tARRAY_LEN( vk.viewConfiguration ),\n\t\t&viewCount,\n"
     "\t\tvk.viewConfiguration ), \"xrEnumerateViewConfigurationViews\" );\n}",
     "\tif ( !VK_CheckXr( xrEnumerateViewConfigurationViews(\n\t\tvk.xrInstance,\n\t\tvk.xrSystemId,\n"
     "\t\tXR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO,\n\t\tARRAY_LEN( vk.viewConfiguration ),\n\t\t&viewCount,\n"
     "\t\tvk.viewConfiguration ), \"xrEnumerateViewConfigurationViews\" ) )\n\t{\n\t\treturn false;\n\t}\n"
     "\t// Steam Frame: render-resolution scale (JKXR_RES_SCALE), applied to the recommended per-eye size\n"
     "\tconst char *scaleEnv = getenv( \"JKXR_RES_SCALE\" );\n"
     "\tconst float scale = scaleEnv ? (float)atof( scaleEnv ) : 1.0f;\n"
     "\tif ( scale >= 0.4f && scale <= 1.5f && scale != 1.0f )\n\t{\n"
     "\t\tfor ( XrViewConfigurationView &view : vk.viewConfiguration )\n\t\t{\n"
     "\t\t\tuint32_t w = (uint32_t)( view.recommendedImageRectWidth * scale ) & ~1u;\n"
     "\t\t\tuint32_t h = (uint32_t)( view.recommendedImageRectHeight * scale ) & ~1u;\n"
     "\t\t\tif ( w > view.maxImageRectWidth ) w = view.maxImageRectWidth;\n"
     "\t\t\tif ( h > view.maxImageRectHeight ) h = view.maxImageRectHeight;\n"
     "\t\t\tview.recommendedImageRectWidth = w;\n\t\t\tview.recommendedImageRectHeight = h;\n\t\t}\n\t}\n"
     "\tri.Printf( PRINT_ALL, \"rd-vulkan: eye buffer %ux%u (JKXR_RES_SCALE %.2f)\\n\",\n"
     "\t\tvk.viewConfiguration[0].recommendedImageRectWidth, vk.viewConfiguration[0].recommendedImageRectHeight, scale );\n"
     "\treturn true;\n}"),
    # 3. Diagnostic: JKXR_NO_MDI=1 forces the renderer's non-indirect world path (multi-draw indirect on the Adreno
    #    driver is a performance suspect).
    ("\tvk.multiDrawIndirect = availableFeatures.multiDrawIndirect == VK_TRUE;\n",
     "\tvk.multiDrawIndirect = availableFeatures.multiDrawIndirect == VK_TRUE && !getenv( \"JKXR_NO_MDI\" ); // Steam Frame switch\n"),
    # 4. Frame-only inputs as extra OpenXR actions (bumpers, d-pad, view, the right hand's X/Y), reported to the client
    #    on spare bits; the client rebuilds JKXR's Touch-style state from them (cl_main.cpp, vr_frame_layout).
    ("static bool VK_CreateControllerActions()\n{",
     "// Steam Frame: Frame-only inputs (bits must match CL_FrameLayoutTranslate in cl_main.cpp)\n"
     "static XrAction frameBumperAction, frameDpadUpAction, frameDpadDownAction, frameDpadLeftAction,\n"
     "\tframeDpadRightAction, frameViewAction, frameXAction, frameYAction;\n"
     "#define JKXR_FRAME_BUMPER     0x00001000u\n#define JKXR_FRAME_DPAD_UP    0x00002000u\n"
     "#define JKXR_FRAME_DPAD_DOWN  0x00004000u\n#define JKXR_FRAME_DPAD_LEFT  0x00008000u\n"
     "#define JKXR_FRAME_DPAD_RIGHT 0x00010000u\n#define JKXR_FRAME_VIEW       0x00020000u\n"
     "#define JKXR_FRAME_X          0x00040000u\n#define JKXR_FRAME_Y          0x00080000u\n\n"
     "static bool VK_CreateControllerActions()\n{"),
    ("\tstd::vector<XrActionSuggestedBinding> touch;\n",
     "\t// Steam Frame: extra boolean actions. They also get Touch suggestions below: SteamVR only knows suggested\n"
     "\t// actions, and drops a custom binding file that names an unknown one.\n"
     "\tif ( !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_bumper\", \"Bumper\", &frameBumperAction ) ||\n"
     "\t\t !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_dpad_up\", \"D-pad Up\", &frameDpadUpAction ) ||\n"
     "\t\t !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_dpad_down\", \"D-pad Down\", &frameDpadDownAction ) ||\n"
     "\t\t !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_dpad_left\", \"D-pad Left\", &frameDpadLeftAction ) ||\n"
     "\t\t !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_dpad_right\", \"D-pad Right\", &frameDpadRightAction ) ||\n"
     "\t\t !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_view\", \"View\", &frameViewAction ) ||\n"
     "\t\t !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_x\", \"Frame X\", &frameXAction ) ||\n"
     "\t\t !VK_CreateControllerAction( XR_ACTION_TYPE_BOOLEAN_INPUT, \"frame_y\", \"Frame Y\", &frameYAction ) )\n"
     "\t{\n\t\treturn false;\n\t}\n\n"
     "\tstd::vector<XrActionSuggestedBinding> touch;\n"),
    ("\t\t{ vk.hapticAction, \"/user/hand/right/output/haptic\" },\n\t};\n\tfor ( const auto &binding : touchBindings )",
     "\t\t{ vk.hapticAction, \"/user/hand/right/output/haptic\" },\n"
     "\t\t// Steam Frame: fallback suggestions so SteamVR learns the Frame-only actions\n"
     "\t\t{ frameBumperAction, \"/user/hand/left/input/x/click\" },\n"
     "\t\t{ frameBumperAction, \"/user/hand/right/input/a/click\" },\n"
     "\t\t{ frameDpadUpAction, \"/user/hand/left/input/y/click\" },\n"
     "\t\t{ frameDpadDownAction, \"/user/hand/left/input/x/click\" },\n"
     "\t\t{ frameDpadLeftAction, \"/user/hand/left/input/thumbstick/click\" },\n"
     "\t\t{ frameDpadRightAction, \"/user/hand/right/input/thumbstick/click\" },\n"
     "\t\t{ frameViewAction, \"/user/hand/left/input/menu/click\" },\n"
     "\t\t{ frameXAction, \"/user/hand/right/input/a/click\" },\n"
     "\t\t{ frameYAction, \"/user/hand/right/input/b/click\" },\n"
     "\t};\n\tfor ( const auto &binding : touchBindings )"),
    # one suggested profile only: SteamVR honours a custom Frame binding only when the input context has one profile
    ("\tVK_SuggestControllerBindings( \"/interaction_profiles/khr/simple_controller\", simple );\n",
     "\tif ( getenv( \"JKXR_SIMPLE_PROFILE\" ) ) // Steam Frame: single profile (Touch) unless asked\n"
     "\t\tVK_SuggestControllerBindings( \"/interaction_profiles/khr/simple_controller\", simple );\n"),
    ("\t\tif ( VK_GetControllerBoolean( vk.thumbrestTouchAction, hand ) )\n\t\t{\n"
     "\t\t\tstate.touches |= VR_CONTROLLER_TOUCH_THUMBREST;\n\t\t}\n\t}\n",
     "\t\tif ( VK_GetControllerBoolean( vk.thumbrestTouchAction, hand ) )\n\t\t{\n"
     "\t\t\tstate.touches |= VR_CONTROLLER_TOUCH_THUMBREST;\n\t\t}\n"
     "\t\t// Steam Frame: raw Frame-only inputs on spare bits (translated in cl_main.cpp)\n"
     "\t\tif ( VK_GetControllerBoolean( frameBumperAction, hand ) ) state.buttons |= JKXR_FRAME_BUMPER;\n"
     "\t\tif ( VK_GetControllerBoolean( frameDpadUpAction, hand ) ) state.buttons |= JKXR_FRAME_DPAD_UP;\n"
     "\t\tif ( VK_GetControllerBoolean( frameDpadDownAction, hand ) ) state.buttons |= JKXR_FRAME_DPAD_DOWN;\n"
     "\t\tif ( VK_GetControllerBoolean( frameDpadLeftAction, hand ) ) state.buttons |= JKXR_FRAME_DPAD_LEFT;\n"
     "\t\tif ( VK_GetControllerBoolean( frameDpadRightAction, hand ) ) state.buttons |= JKXR_FRAME_DPAD_RIGHT;\n"
     "\t\tif ( VK_GetControllerBoolean( frameViewAction, hand ) ) state.buttons |= JKXR_FRAME_VIEW;\n"
     "\t\tif ( VK_GetControllerBoolean( frameXAction, hand ) ) state.buttons |= JKXR_FRAME_X;\n"
     "\t\tif ( VK_GetControllerBoolean( frameYAction, hand ) ) state.buttons |= JKXR_FRAME_Y;\n"
     "\t}\n"),
])

# 5. Client: rebuild JKXR's Touch-style controller state from the Frame's inputs (standard Frame layout). Off with
#    vr_frame_layout 0, and only for the default right-handed scheme (vr_control_scheme 0).
patch("code/client/cl_main.cpp", [
    ("static void CL_TBXR_UpdateControllers(\n",
     "// ---- Steam Frame layout ------------------------------------------------------------------------------------\n"
     "// Frame inputs -> JKXR's Touch semantics (right-handed):\n"
     "//   R trigger fire/saber, R bumper alt-fire (B: saber on/off), L bumper jump (A), R A use (stick click),\n"
     "//   R grip 80% weapon wheel, L grip 80% use Force (off-hand trigger: keeps the Force gestures), R B Force wheel\n"
     "//   (off-hand grip; pick with the left stick), L trigger crouch (left stick click), R Y console/back (Y),\n"
     "//   R menu menu. Commands: R X saber style, R stick click next item, L stick click use item, view datapad,\n"
     "//   d-pad up/down quick save/load, left/right previous/next Force power.\n"
     "#define JKXR_FRAME_BUMPER     0x00001000u\n#define JKXR_FRAME_DPAD_UP    0x00002000u\n"
     "#define JKXR_FRAME_DPAD_DOWN  0x00004000u\n#define JKXR_FRAME_DPAD_LEFT  0x00008000u\n"
     "#define JKXR_FRAME_DPAD_RIGHT 0x00010000u\n#define JKXR_FRAME_VIEW       0x00020000u\n"
     "#define JKXR_FRAME_X          0x00040000u\n#define JKXR_FRAME_Y          0x00080000u\n"
     "static qboolean CL_FrameLayoutTranslate( const vrControllerState_t *L, const vrControllerState_t *R,\n"
     "\tvrControllerState_t *oL, vrControllerState_t *oR )\n{\n"
     "\tstatic cvar_t *layout = Cvar_Get( \"vr_frame_layout\", \"1\", CVAR_ARCHIVE );\n"
     "\tstatic cvar_t *scheme = Cvar_Get( \"vr_control_scheme\", \"0\", CVAR_ARCHIVE );\n"
     "\tif ( !layout->integer || scheme->integer != 0 )\n\t\treturn qfalse;\n"
     "\tconst uint32_t lb = L->buttons, rb = R->buttons;\n"
     "\t*oL = *L;\n\t*oR = *R;\n\toL->buttons = 0;\n\toR->buttons = 0;\n"
     "\t// right hand (dominant)\n"
     "\tif ( rb & VR_CONTROLLER_BUTTON_TRIGGER ) oR->buttons |= VR_CONTROLLER_BUTTON_TRIGGER;\n"
     "\tif ( rb & JKXR_FRAME_BUMPER ) oR->buttons |= VR_CONTROLLER_BUTTON_B;\n"
     "\tif ( lb & JKXR_FRAME_BUMPER ) oR->buttons |= VR_CONTROLLER_BUTTON_A;\n"
     "\tif ( rb & VR_CONTROLLER_BUTTON_A ) oR->buttons |= VR_CONTROLLER_BUTTON_RIGHT_THUMB | VR_CONTROLLER_BUTTON_JOYSTICK;\n"
     "\tif ( rb & VR_CONTROLLER_BUTTON_MENU ) oR->buttons |= VR_CONTROLLER_BUTTON_MENU;\n"
     "\toR->gripTrigger = R->gripTrigger >= 0.8f ? 1.0f : 0.0f;\n"
     "\t// left hand (off hand)\n"
     "\tconst bool force = L->gripTrigger >= 0.8f;\n"
     "\tif ( force ) oL->buttons |= VR_CONTROLLER_BUTTON_TRIGGER;\n"
     "\toL->indexTrigger = force ? 1.0f : 0.0f;\n"
     "\toL->gripTrigger = ( rb & VR_CONTROLLER_BUTTON_B ) ? 1.0f : 0.0f;\n"
     "\tif ( lb & VR_CONTROLLER_BUTTON_TRIGGER ) oL->buttons |= VR_CONTROLLER_BUTTON_LEFT_THUMB | VR_CONTROLLER_BUTTON_JOYSTICK;\n"
     "\tif ( rb & JKXR_FRAME_Y ) oL->buttons |= VR_CONTROLLER_BUTTON_Y;\n"
     "\t// one-shot commands, in game only; the Frame d-pad repeats while held, so each fires at most once a second\n"
     "\tstruct frameCmd_t { uint32_t bit; bool right; const char *cmd; };\n"
     "\tstatic const frameCmd_t cmds[] = {\n"
     "\t\t{ JKXR_FRAME_X, true, \"saberAttackCycle\\n\" },\n"
     "\t\t{ VR_CONTROLLER_BUTTON_RIGHT_THUMB, true, \"invnext\\n\" },\n"
     "\t\t{ VR_CONTROLLER_BUTTON_LEFT_THUMB, false, \"invuse\\n\" },\n"
     "\t\t{ JKXR_FRAME_VIEW, false, \"datapad\\n\" },\n"
     "\t\t{ JKXR_FRAME_DPAD_UP, false, \"save quick\\n\" },\n"
     "\t\t{ JKXR_FRAME_DPAD_DOWN, false, \"load quick\\n\" },\n"
     "\t\t{ JKXR_FRAME_DPAD_LEFT, false, \"forceprev\\n\" },\n"
     "\t\t{ JKXR_FRAME_DPAD_RIGHT, false, \"forcenext\\n\" },\n\t};\n"
     "\tstatic uint32_t lastL = 0, lastR = 0;\n\tstatic int lastFire[8] = {};\n"
     "\tconst bool inGame = cls.state == CA_ACTIVE && !( Key_GetCatcher() & ( KEYCATCH_UI | KEYCATCH_CONSOLE ) );\n"
     "\tconst int now = Sys_Milliseconds();\n"
     "\tfor ( int i = 0; i < (int)ARRAY_LEN( cmds ); ++i )\n\t{\n"
     "\t\tconst uint32_t cur = cmds[i].right ? rb : lb, last = cmds[i].right ? lastR : lastL;\n"
     "\t\tif ( inGame && ( cur & cmds[i].bit ) && !( last & cmds[i].bit ) && now - lastFire[i] > 1000 )\n\t\t{\n"
     "\t\t\tCbuf_AddText( cmds[i].cmd );\n\t\t\tlastFire[i] = now;\n\t\t}\n\t}\n"
     "\tlastL = lb;\n\tlastR = rb;\n\treturn qtrue;\n}\n\n"
     "static void CL_TBXR_UpdateControllers(\n"),
    ("\tstatic bool leftGripEngaged = false;\n\tstatic bool rightGripEngaged = false;\n",
     "\t// Steam Frame: standard Frame layout (vr_frame_layout)\n"
     "\tstatic vrControllerState_t frameLeft, frameRight;\n"
     "\tif ( CL_FrameLayoutTranslate( left, right, &frameLeft, &frameRight ) )\n\t{\n"
     "\t\tleft = &frameLeft;\n\t\tright = &frameRight;\n\t}\n"
     "\tstatic bool leftGripEngaged = false;\n\tstatic bool rightGripEngaged = false;\n"),
])

if failed:
    print("FAILED:\n  " + "\n  ".join(failed)); sys.exit(1)
print("port patches applied")
