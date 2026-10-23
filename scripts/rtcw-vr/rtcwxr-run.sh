#!/bin/bash
# Steam launch wrapper for the native ARM64 RealRTCW XR build (Team Beef's OpenXR RealRTCW, GLX/OpenXR port).
# Log: ~/PCVR/RealRTCWXR-game/rtcwxr-last.log. Extra args pass through.
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11                                   # the OpenXR binding is GLX (Xlib)
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE   # Steam's session caps Mesa at GL 4.3
[ -f "$PWD/env.test" ] && . "$PWD/env.test"   # test env vars (RTCWXR_DEBUG_INPUT=1 traces input to the log)
BIN=$(ls RealRTCW.* 2>/dev/null | grep -v '\.so$' | head -1)
if [ -f gdb.test ]; then  # debugging: backtrace into rtcwxr-gdb.log (ptrace attach is blocked; run under gdb instead)
  exec gdb -batch -ex run -ex bt -ex quit --args "./$BIN" +set fs_basepath "$PWD" +set fs_homepath "$PWD/home" "$@" > rtcwxr-gdb.log 2>&1
fi
exec stdbuf -oL -eL "./$BIN" +set fs_basepath "$PWD" +set fs_homepath "$PWD/home" "$@" > rtcwxr-last.log 2>&1
