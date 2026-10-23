#!/bin/bash
# Steam launch wrapper for the native ARM64 Quake II VR build (Quake-II-PCVR, GLX/OpenXR port).
# Log: ~/PCVR/Quake2VR-game/q2vr-last.log.  Extra args pass through (e.g. +set game xatrix).
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11                                   # OpenXR binding is GLX (Xlib)
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE   # Steam's session caps Mesa at GL 4.3
exec stdbuf -oL -eL ./quake2 -portable "$@" > q2vr-last.log 2>&1
