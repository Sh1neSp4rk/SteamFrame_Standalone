#!/bin/bash
# Steam launch wrapper for the native ARM64 QuakeVR build (v1.1.0-beta3). Log: ~/PCVR/QuakeVR-game/quakevr-last.log
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11 SDL_VIDEO_X11_FORCE_EGL=0          # SteamVR needs the GLX binding
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE     # Steam's session caps Mesa at GL 4.3
export QVR_GLSAFE_OFF=${QVR_GLSAFE_OFF:-2}   # bindless off (zink crash)
export QVR_XR_SYNC=${QVR_XR_SYNC:-2}   # 1 glFlush, 2 glFinish before each image release (zink)
[ -f "$PWD/env.test" ] && . "$PWD/env.test"   # test env vars (q1_profile.sh)
QVR_EXTRA=""   # test args (q1_profile.sh, q1_sweep.sh)
exec stdbuf -oL -eL ./ironwail -basedir "$PWD" -game quakevr -noglsafe +vr_backend openxr $QVR_EXTRA "$@" > quakevr-last.log 2>&1
