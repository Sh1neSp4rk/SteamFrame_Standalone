#!/bin/bash
# Native linux-arm64 build of RealRTCWXR on the Steam Frame. System SDL2 (the bundled one is x86-64), the bundled
# codec/zlib/jpeg sources, no curl; OpenXR through SteamVR's ARM64 loader (rtcw_port.py adds the layer to the Makefile).
set -e
R="$HOME/PCVR/RealRTCWXR"
python3 -I "$R/rtcw_port.py" "$R/src"
cd "$R/src"
make -j6 BUILD_SERVER=0 BUILD_CLIENT=1 BUILD_GAME_SO=1 BUILD_RENDERER_REND2=1 \
  USE_INTERNAL_LIBS=0 USE_INTERNAL_OGG=1 USE_INTERNAL_VORBIS=1 USE_INTERNAL_OPUS=1 USE_INTERNAL_ZLIB=1 USE_INTERNAL_JPEG=1 \
  USE_CURL=0 USE_CODEC_OPUS=0 USE_VOIP=0 \
  CFLAGS="-std=gnu99 -fcommon -Wno-error -Wno-error=incompatible-pointer-types -Wno-error=int-conversion -Wno-error=implicit-function-declaration -Wno-error=implicit-int -Wno-error=return-mismatch" \
  > "$R/build.log" 2>&1 || true
grep -E -i 'error:|undefined reference|FAILED|\*\*\*|No rule' "$R/build.log" | head -30
ls -la "$R"/src/build/release-linux-aarch64/ 2>/dev/null | grep -v '^total'
