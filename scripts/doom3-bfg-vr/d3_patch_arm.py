# License note: the replacement source fragments in this file derive from NPi2Loup/DOOM-3-BFG-VR (RBDoom3BFG), GPL-3.0,
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Frame/ARM64 build patches for NPi2Loup/DOOM-3-BFG-VR (idempotent): SSE flags and intrinsics only on x86."""
import sys

neo = sys.argv[1]


def patch(rel, old, new):
    p = f"{neo}/{rel}"
    t = open(p, encoding="utf-8", errors="surrogateescape").read()
    # Already applied: the whole replacement, or (when a later patch edited inside it) its first
    # "Frame patch" comment line, is present.
    marker = next((l.strip() for l in new.split("\n") if "Frame patch" in l), None)
    if new in t or (marker and marker in t):
        return
    if old not in t:
        sys.exit(f"pattern not found in {rel}: {old[:60]!r}")
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(t.replace(old, new, 1))
    print("patched", rel)


patch("CMakeLists.txt",
      "\tadd_definitions(-mmmx -msse -msse2)",
      "\tif(CMAKE_SYSTEM_PROCESSOR MATCHES \"x86|AMD64|i.86\")  # Frame patch: x86-only SIMD flags\n"
      "\t\tadd_definitions(-mmmx -msse -msse2)\n"
      "\tendif()\n"
      "\t# Frame patch: GCC 15 defaults to C++17, where this code's throw() specs are errors. Set here\n"
      "\t# (not CMAKE_CXX_FLAGS) because the hand-rolled precompiled-header commands only see DEFINITIONS.\n"
      "\tadd_definitions(-std=gnu++14 -fpermissive -w)\n"
      "\t# Frame patch: x86 code assumes signed char; ARM's default unsigned char garbles GUI text.\n"
      "\tadd_definitions(-fsigned-char)")
patch("idlib/sys/sys_defines.h",
      "#elif defined(__x86_64__)\n#define CPUSTRING\t\t\t\t\t\t\"x86_86\"\n#endif",
      "#elif defined(__x86_64__)\n#define CPUSTRING\t\t\t\t\t\t\"x86_86\"\n"
      "#elif defined(__aarch64__)  // Frame patch\n#define CPUSTRING\t\t\t\t\t\t\"arm64\"\n#endif")
patch("vr/Vr.cpp",
      "\t\tstatic vr::EVRCompositorError error = vr::VRCompositor()->SetSkyboxOverride(textures, 1);",
      "\t\t// Frame patch: SetSkyboxOverride with OpenGL textures crashes inside the Frame's ARM64 vrclient\n"
      "\t\t// (and Proton can't convert it either). It only sets the backdrop SteamVR shows during stalls,\n"
      "\t\t// so skip it unless D3BFGVR_SKYBOX is set.\n"
      "\t\tstatic vr::EVRCompositorError error = getenv( \"D3BFGVR_SKYBOX\" ) ?\n"
      "\t\t\tvr::VRCompositor()->SetSkyboxOverride( textures, 1 ) : vr::VRCompositorError_None;")
patch("vr/Vr.cpp",
      "\tvr::VRCompositor()->WaitGetPoses( m_rTrackedDevicePose, vr::k_unMaxTrackedDeviceCount, NULL, 0 );\n\t\n",
      "\t{\n"
      "\t\t// Frame patch: log why poses come back invalid (rate-limited).\n"
      "\t\tvr::EVRCompositorError poseErr = vr::VRCompositor()->WaitGetPoses( m_rTrackedDevicePose, vr::k_unMaxTrackedDeviceCount, NULL, 0 );\n"
      "\t\tstatic int poseLogCount = 0;\n"
      "\t\tif ( ( poseErr != vr::VRCompositorError_None || !m_rTrackedDevicePose[vr::k_unTrackedDeviceIndex_Hmd].bPoseIsValid ) && poseLogCount++ % 300 == 0 )\n"
      "\t\t\tcommon->Printf( \"Frame: WaitGetPoses err=%d hmdValid=%d tracking=%d sceneFocus=%d activity=%d\\n\", (int)poseErr,\n"
      "\t\t\t\t(int)m_rTrackedDevicePose[vr::k_unTrackedDeviceIndex_Hmd].bPoseIsValid, (int)m_rTrackedDevicePose[vr::k_unTrackedDeviceIndex_Hmd].eTrackingResult,\n"
      "\t\t\t\t(int)( vr::VRCompositor()->CanRenderScene() ), (int)vr::VRSystem()->GetTrackedDeviceActivityLevel( vr::k_unTrackedDeviceIndex_Hmd ) );\n"
      "\t}\n\t\n")
patch("vr/Vr_Gl.cpp",
      "\t\tvr::VRCompositor()->Submit( vr::Eye_Left, &leftEyeTexture );",
      "\t\t{\n"
      "\t\t\t// Frame patch: log Submit errors (rate-limited).\n"
      "\t\t\tstatic int submitLogCount = 0;\n"
      "\t\t\tvr::EVRCompositorError submitErr = vr::VRCompositor()->Submit( vr::Eye_Left, &leftEyeTexture );\n"
      "\t\t\tif ( submitErr != vr::VRCompositorError_None && submitLogCount++ % 300 == 0 )\n"
      "\t\t\t\tcommon->Printf( \"Frame: Submit(left) err=%d\\n\", (int)submitErr );\n"
      "\t\t}")
patch("framework/Common.cpp",
      "\t\t\t\t// queue system events ready for polling\n\t\t\t\tSys_GetEvent();\n",
      "\t\t\t\t// queue system events ready for polling\n"
      "\t\t\t\t// Frame patch: on Linux the VR controller buttons come back from Sys_GetEvent() as key\n"
      "\t\t\t\t// events, which this loop used to discard, so no button could pass the face-forward screen.\n"
      "\t\t\t\tsysEvent_t splashEvent = Sys_GetEvent();\n"
      "\t\t\t\tif ( splashEvent.evType == SE_KEY && splashEvent.evValue2 != 0 )\n"
      "\t\t\t\t{\n"
      "\t\t\t\t\tcommon->Printf( \"Frame: face-forward screen passed by key %d\\n\", splashEvent.evValue );\n"
      "\t\t\t\t\tcentered++;\n"
      "\t\t\t\t}\n")
patch("vr/Vr.cpp",
      "\t\tstatic int poseLogCount = 0;\n",
      "\t\tstatic int poseLogCount = 0;\n"
      "\t\tstatic int lastHmdValid = -1;\n"
      "\t\tconst int hmdValidNow = (int)m_rTrackedDevicePose[vr::k_unTrackedDeviceIndex_Hmd].bPoseIsValid;\n"
      "\t\tif ( hmdValidNow != lastHmdValid )\n"
      "\t\t{\n"
      "\t\t\tcommon->Printf( \"Frame: t=%d ms HMD pose %s (tracking=%d activity=%d)\\n\", Sys_Milliseconds(), hmdValidNow ? \"VALID\" : \"invalid\",\n"
      "\t\t\t\t(int)m_rTrackedDevicePose[vr::k_unTrackedDeviceIndex_Hmd].eTrackingResult, (int)vr::VRSystem()->GetTrackedDeviceActivityLevel( vr::k_unTrackedDeviceIndex_Hmd ) );\n"
      "\t\t\tlastHmdValid = hmdValidNow;\n"
      "\t\t}\n")
patch("vr/Vr_Gl.cpp",
      "\t\t\tvr::EVRCompositorError submitErr = vr::VRCompositor()->Submit( vr::Eye_Left, &leftEyeTexture );",
      "\t\t\t// Frame patch: pass explicit full-texture bounds; the Frame's SteamVR logged garbage bounds\n"
      "\t\t\t// (\"Invalid texture bounds\") for every frame with the default argument and showed nothing.\n"
      "\t\t\tstatic const vr::VRTextureBounds_t fullBounds = { 0.0f, 0.0f, 1.0f, 1.0f };\n"
      "\t\t\tvr::EVRCompositorError submitErr = vr::VRCompositor()->Submit( vr::Eye_Left, &leftEyeTexture, &fullBounds, vr::Submit_Default );")
patch("vr/Vr_Gl.cpp",
      "\t\tvr::VRCompositor()->Submit( vr::Eye_Right, &rightEyeTexture );",
      "\t\t{\n"
      "\t\t\tstatic const vr::VRTextureBounds_t fullBounds = { 0.0f, 0.0f, 1.0f, 1.0f };  // Frame patch, see left eye\n"
      "\t\t\tvr::VRCompositor()->Submit( vr::Eye_Right, &rightEyeTexture, &fullBounds, vr::Submit_Default );\n"
      "\t\t}")
patch("framework/Common.cpp",
      "\t\t\t\tsysEvent_t splashEvent = Sys_GetEvent();\n",
      "\t\t\t\tsysEvent_t splashEvent = Sys_GetEvent();\n"
      "\t\t\t\t// Frame patch: also pass the screen on any VR controller button or trigger, read straight\n"
      "\t\t\t\t// from OpenVR, and log what the controllers report (once a second).\n"
      "\t\t\t\tif ( commonVr->hasHMD && !commonVr->hasOculusRift )\n"
      "\t\t\t\t{\n"
      "\t\t\t\t\tstatic int splashLog = 0;\n"
      "\t\t\t\t\tfor ( vr::TrackedDeviceIndex_t dev = 1; dev < vr::k_unMaxTrackedDeviceCount; dev++ )\n"
      "\t\t\t\t\t{\n"
      "\t\t\t\t\t\tif ( commonVr->m_pHMD->GetTrackedDeviceClass( dev ) != vr::TrackedDeviceClass_Controller ) continue;\n"
      "\t\t\t\t\t\tvr::VRControllerState_t st;\n"
      "\t\t\t\t\t\tbool ok = commonVr->m_pHMD->GetControllerState( dev, &st, sizeof( st ) );\n"
      "\t\t\t\t\t\tif ( splashLog % 72 == 0 )\n"
      "\t\t\t\t\t\t\tcommon->Printf( \"Frame: splash controller %u ok=%d pressed=%llx trigger=%.2f (L=%u R=%u)\\n\", dev, (int)ok,\n"
      "\t\t\t\t\t\t\t\t(unsigned long long)st.ulButtonPressed, st.rAxis[1].x, commonVr->leftControllerDeviceNo, commonVr->rightControllerDeviceNo );\n"
      "\t\t\t\t\t\tif ( ok && ( st.ulButtonPressed != 0 || st.rAxis[1].x > 0.6f ) )\n"
      "\t\t\t\t\t\t{\n"
      "\t\t\t\t\t\t\tcommon->Printf( \"Frame: face-forward screen passed by controller %u\\n\", dev );\n"
      "\t\t\t\t\t\t\tcentered++;\n"
      "\t\t\t\t\t\t}\n"
      "\t\t\t\t\t}\n"
      "\t\t\t\t\tsplashLog++;\n"
      "\t\t\t\t}\n")
patch("sys/sdl/sdl_events.cpp",
      "            rGood = commonVr->m_pHMD->GetControllerState( commonVr->rightControllerDeviceNo, &currentStateR, sizeof( currentStateR ) );\n",
      "            rGood = commonVr->m_pHMD->GetControllerState( commonVr->rightControllerDeviceNo, &currentStateR, sizeof( currentStateR ) );\n"
      "            {\n"
      "                // Frame patch: log controller state changes (rate-limited) to see in-game input.\n"
      "                static uint64_t lastL = ~0ull, lastR = ~0ull;\n"
      "                static int stateLog = 0;\n"
      "                if ( ( currentStateL.ulButtonPressed != lastL || currentStateR.ulButtonPressed != lastR ) && stateLog++ < 200 )\n"
      "                    common->Printf( \"Frame: controllers L=%u ok=%d %llx  R=%u ok=%d %llx\\n\", commonVr->leftControllerDeviceNo, (int)lGood,\n"
      "                        (unsigned long long)currentStateL.ulButtonPressed, commonVr->rightControllerDeviceNo, (int)rGood, (unsigned long long)currentStateR.ulButtonPressed );\n"
      "                lastL = currentStateL.ulButtonPressed; lastR = currentStateR.ulButtonPressed;\n"
      "            }\n")
patch("sys/sdl/sdl_events.cpp",
      "bool isvrevent = false;\nstatic sysEvent_t vrevent;\n",
      "bool isvrevent = false;\nstatic sysEvent_t vrevent;\n"
      "// Frame patch: queue VR button events instead of one slot (several presses per frame were lost).\n"
      "static idList<sysEvent_t> vreventQueue;\n")
patch("sys/sdl/sdl_events.cpp",
      "    if (isvrevent) {\n        isvrevent = false;\n",
      "    if ( vreventQueue.Num() > 0 )  // Frame patch: drain the VR button queue first\n"
      "    {\n"
      "        sysEvent_t queued = vreventQueue[0];\n"
      "        vreventQueue.RemoveIndex( 0 );\n"
      "        return queued;\n"
      "    }\n"
      "    if (isvrevent) {\n        isvrevent = false;\n")
patch("sys/sdl/sdl_events.cpp",
      "        vrevent.inputDevice = inputDeviceNum;\n        isvrevent = true;\n",
      "        vrevent.inputDevice = inputDeviceNum;\n"
      "        // Frame patch: queue it for menus/GUIs (Sys_GetEvent), and also add it to the polled keyboard\n"
      "        // list, which is what in-game movement/firing (idUsercmdGen) reads. On Linux VR buttons only\n"
      "        // reached the event path, so menus worked but the player could not move or shoot.\n"
      "        vreventQueue.Append( vrevent );\n"
      "        kbd_polls.Append( kbd_poll_t( key, value ) );\n")
patch("d3xp/Player.cpp",
      "#ifdef _WIN32 //TODO: FIX\n"
      "\t\t\t\tvoid Sys_QueEvent( sysEventType_t type, int value, int value2, int ptrLength, void *ptr, int inputDeviceNum );\n"
      "\t\t\t\tSys_QueEvent( SE_KEY, K_ESCAPE, 1, 0, NULL, 0 );\n"
      "#endif\n",
      "\t\t\t\t// Frame patch: was Windows-only (\"TODO: FIX\"), so no button could open the menu on Linux.\n"
      "\t\t\t\tvoid Sys_QueVrKey( int key );\n"
      "\t\t\t\tSys_QueVrKey( K_ESCAPE );\n")
patch("sys/sdl/sdl_events.cpp",
      "void PushButton( int inputDeviceNum, int key, bool value )\n",
      "// Frame patch: queue a full key press (down + up) on the VR event path, e.g. Escape for the menu.\n"
      "void Sys_QueVrKey( int key )\n"
      "{\n"
      "    sysEvent_t ev = {};\n"
      "    ev.evType = SE_KEY;\n"
      "    ev.evValue = key;\n"
      "    ev.evValue2 = 1;\n"
      "    vreventQueue.Append( ev );\n"
      "    ev.evValue2 = 0;\n"
      "    vreventQueue.Append( ev );\n"
      "}\n\n"
      "void PushButton( int inputDeviceNum, int key, bool value )\n")
patch("sys/sdl/sdl_events.cpp",
      "void PostInputEvent( int inputDeviceNum, int event, int value, int range )\n{\n",
      "// Frame patch: stick directions as keys with hysteresis (press past 60%, release under 30%). The\n"
      "// single 50% threshold re-fired snap turn and weapon switch whenever the stick wobbled near it.\n"
      "static void PushAxisButtons( int inputDeviceNum, int negKey, int posKey, int value, int range )\n"
      "{\n"
      "    const int on = range * 6 / 5, off = range * 3 / 5;\n"
      "    PushButton( inputDeviceNum, negKey, buttonStates[negKey] ? ( value < -off ) : ( value < -on ) );\n"
      "    PushButton( inputDeviceNum, posKey, buttonStates[posKey] ? ( value > off ) : ( value > on ) );\n"
      "}\n\n"
      "void PostInputEvent( int inputDeviceNum, int event, int value, int range )\n{\n")
for side, axis, neg, pos in (("LEFT", "X", "LEFT", "RIGHT"), ("LEFT", "Y", "UP", "DOWN"),
                             ("RIGHT", "X", "LEFT", "RIGHT"), ("RIGHT", "Y", "UP", "DOWN")):
    patch("sys/sdl/sdl_events.cpp",
          f"        PushButton( inputDeviceNum, K_STEAMVR_{side}_PAD_{neg}, (value < -range) );\n"
          f"        PushButton( inputDeviceNum, K_STEAMVR_{side}_PAD_{pos}, (value > range) );\n",
          f"        PushAxisButtons( inputDeviceNum, K_STEAMVR_{side}_PAD_{neg}, K_STEAMVR_{side}_PAD_{pos}, value, range );  // Frame patch: hysteresis\n")
patch("idlib/sys/sys_intrinsics.h",
      "#define USE_INTRINSICS",
      "#if defined(__x86_64__) || defined(__i386__) || defined(_M_X64) || defined(_M_IX86)  // Frame patch\n"
      "#define USE_INTRINSICS\n"
      "#endif")
