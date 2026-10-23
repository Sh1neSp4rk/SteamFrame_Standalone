#!/bin/bash
# Steam launch wrapper for the native ARM64 q3vr build. Log: ~/PCVR/Q3VR-game/q3vr-last.log
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11   # the OpenXR binding is GLX (XrGraphicsBindingOpenGLXlibKHR)
# Steam's session caps Mesa at GL 4.3 for games; q3vr creates a 4.6 core context (zink offers 4.6).
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE
exec ./q3vr +set fs_basepath "$PWD" +set fs_homepath "$PWD/home" +set r_ext_multisample 0 "$@" > q3vr-last.log 2>&1
