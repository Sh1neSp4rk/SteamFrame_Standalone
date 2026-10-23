#!/bin/bash
# Native linux-arm64 build of q3vr (RippeR37/q3vr) for the Steam Frame.
# - skips vcpkg: an empty toolchain file + a hand-written OpenXRConfig.cmake that points at SteamVR's
#   ARM64 libopenxr_loader.so (the system libopenxr_loader.a is LTO-only) and the system OpenXR headers
# - system SDL2 instead of the bundled (x86) SDL binary; gnu17 for GCC 15
set -e
Q="$HOME/PCVR/Q3VR"
S="$Q/src"; B="$Q/build"; X="$Q/cmake-shim"
mkdir -p "$X/OpenXR" "$B"
: > "$X/no-vcpkg.cmake"
cat > "$X/OpenXR/OpenXRConfig.cmake" <<'EOF'
add_library(OpenXR::headers INTERFACE IMPORTED)
set_target_properties(OpenXR::headers PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "/usr/include")
add_library(OpenXR::openxr_loader SHARED IMPORTED)
set_target_properties(OpenXR::openxr_loader PROPERTIES
  IMPORTED_LOCATION "/opt/steamvr/bin/linuxarm64/libopenxr_loader.so"
  INTERFACE_LINK_LIBRARIES OpenXR::headers)
set(OpenXR_FOUND TRUE)
EOF
cmake -S "$S" -B "$B" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE="$X/no-vcpkg.cmake" -DOpenXR_DIR="$X/OpenXR" \
  -DUSE_INTERNAL_SDL=OFF -DCMAKE_C_FLAGS="-std=gnu17 -Wno-error" 2>&1 | tail -25
cmake --build "$B" -j6 2>&1 | grep -E -i 'error|warning: implicit|^\[[0-9]+/[0-9]+\] Linking|FAILED' | head -40
echo "--- output"; find "$B" -maxdepth 3 \( -name q3vr -o -name '*.so' \) -newer "$S/CMakeLists.txt" | head
file "$B"/Release/q3vr 2>/dev/null || find "$B" -name q3vr -type f -exec file {} \;
df -h ~ | tail -1
