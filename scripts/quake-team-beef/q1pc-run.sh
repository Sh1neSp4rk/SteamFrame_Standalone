#!/bin/bash
# Steam launch wrapper for the native ARM64 Quake-PCVR build (Team Beef's QuakeQuest on DarkPlaces, GLX/OpenXR).
# Log: ~/PCVR/QuakePCVR-game/q1pc-last.log. Extra args pass through (e.g. -game hipnotic, -novr).
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11                                   # the OpenXR binding is GLX (Xlib)
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE   # Steam's session caps Mesa at GL 4.3
exec stdbuf -oL -eL ./darkplaces-sdl -basedir . -nohome "$@" > q1pc-last.log 2>&1
