#!/bin/bash
# Native linux-arm64 build of Quake VR (vittorioromeo/quakevr v1.1.0-beta3) for the Steam Frame.
# clang (gcc can't build Zancle); OpenXR via a pkg-config shim pointing at SteamVR's ARM64 loader (the system
# libopenxr_loader.a is LTO-only) and the repo's own OpenXR 1.1.63 headers (the system's 1.1.40 lacks
# XR_META_body_tracking_full_body, used by vr_bodytrack_xr.cpp).
set -e
Q="$HOME/PCVR/QuakeVR"
PC="$Q/pkgconfig"; mkdir -p "$PC"
cat > "$PC/openxr.pc" <<'EOF'
prefix=/usr
includedir=/home/steamos/PCVR/QuakeVR/src/Windows/OpenXR/include
libdir=/opt/steamvr/bin/linuxarm64
Name: openxr
Description: OpenXR loader (SteamVR ARM64 libopenxr_loader.so, Steam Frame)
Version: 1.1.0
Libs: -L${libdir} -lopenxr_loader -Wl,-rpath,${libdir}
Cflags: -I${includedir}
EOF
command -v clang clang++ ld.lld | head -3
export PKG_CONFIG_PATH="$PC"
python3 -I "$Q/q1_port.py" "$Q/src"     # SSE/AVX -> SIMDe on ARM
cmake -S "$Q/src" -B "$Q/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DQVR_ZANCLE_DEBUG=OFF \
  "-DCMAKE_CXX_FLAGS=-I$Q/simde -I$Q/src/Windows/OpenXR/include" \
  "-DCMAKE_C_FLAGS=-I$Q/src/Windows/OpenXR/include" > "$Q/cmake.log" 2>&1 \
  || { tail -30 "$Q/cmake.log"; exit 1; }
grep -E 'Quake VR:|OpenXR' "$Q/cmake.log"
cmake --build "$Q/build" -j6 > "$Q/build.log" 2>&1 || true
grep -E 'error:|FAILED' "$Q/build.log" | head -30
tail -2 "$Q/build.log"
find "$Q/build" -maxdepth 2 -name ironwail -type f -exec file {} \;
df -h ~ | tail -1
