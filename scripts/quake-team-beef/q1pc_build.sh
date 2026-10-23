#!/bin/bash
# Native linux-arm64 build of Quake-PCVR (Team Beef's QuakeQuest, DarkPlaces) on the Steam Frame: SDL2 video and
# sound, OpenXR through SteamVR's ARM64 loader, the GLX binding (q1pc_port.py). DarkPlaces builds in-tree.
# -std=gnu99: qtypes.h defines true/false, keywords in GCC 15's default C23. -fcommon: old duplicate globals.
set -e
Q="$HOME/PCVR/QuakePCVR"
python3 -I "$Q/q1pc_port.py" "$Q/src"
cd "$Q/src"
XRLIB=/opt/steamvr/bin/linuxarm64
make sdl-release -j6 \
  DP_MAKE_TARGET=linux DP_SOUND_API=SDL SDL_CONFIG=sdl2-config \
  CFLAGS_EXTRA="-std=gnu99 -fcommon -Wno-error" CFLAGS_SSE= CFLAGS_SSE2= \
  LDFLAGS_LINUXSDL="\$(LDFLAGS_UNIXCOMMON) -lrt -ldl \$(LDFLAGS_UNIXSDL) $XRLIB/libopenxr_loader.so -Wl,-rpath,$XRLIB -lGL -lX11" \
  > "$Q/build.log" 2>&1 || true
grep -E -i 'error:|undefined reference|FAILED|\*\*\*' "$Q/build.log" | head -30
ls -la "$Q/src/darkplaces-sdl" 2>/dev/null && file "$Q/src/darkplaces-sdl"
