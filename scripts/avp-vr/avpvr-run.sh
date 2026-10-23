#!/bin/bash
# Steam launch wrapper for the native ARM64 AvP VR build. Log: ~/PCVR/AVPVR-game/avpvr-last.log
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11   # the OpenXR binding is GLX, so SDL must use X11
export LD_LIBRARY_PATH="$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec ./avpvr_arm64 "$@" > avpvr-last.log 2>&1
