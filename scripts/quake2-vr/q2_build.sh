#!/bin/bash
# Native linux-arm64 build of Quake-II-PCVR on the Steam Frame (OpenXR via SteamVR's ARM64 loader, GLX).
# _GNU_SOURCE: teambeef/mathlib.c uses sincosf.
# -Bsymbolic: the quake2 executable exports R_SetMode etc.; without it ref_gl1.so's calls bind to the
# executable's copies (ELF interposition; Windows DLLs never do this) and R_SetMode spins forever.
set -e
Q="$HOME/PCVR/Quake2VR"
python3 -I "$Q/q2_port.py" "$Q/src"
cmake -S "$Q/src" -B "$Q/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DOPENXR_INCLUDE_DIR=/usr/include \
  -DOPENXR_LOADER_LIBRARY=/opt/steamvr/bin/linuxarm64/libopenxr_loader.so \
  "-DCMAKE_C_FLAGS=-fcommon -D_GNU_SOURCE" \
  "-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-Bsymbolic" "-DCMAKE_MODULE_LINKER_FLAGS=-Wl,-Bsymbolic" > "$Q/cmake.log" 2>&1 || { tail -20 "$Q/cmake.log"; exit 1; }
cmake --build "$Q/build" -j6 > "$Q/build.log" 2>&1 || true
grep -E -i 'error:|FAILED' "$Q/build.log" | head -30
grep -c 'Linking' "$Q/build.log"
ls -la "$Q/build/release"
file "$Q/build/release/quake2" 2>/dev/null || true
