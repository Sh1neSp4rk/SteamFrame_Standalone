#!/bin/bash
# Build the native hudbridge (aarch64) next to ovrshim. Headers come from SteamVR's hellovr_vulkan sample.
set -e
cd "$(dirname "$0")"
H=/opt/steamvr/tools/hellovr_vulkan_linux/src/openvr/headers
VK=$(ls /usr/lib/libvulkan.so* 2>/dev/null | head -1)
clang++ -O2 -std=c++17 -Wno-unused-result -I"$H" hudbridge.cpp -o hudbridge /usr/lib/libopenvr_api.so "$VK" -Wl,-rpath,/usr/lib
echo "built $(pwd)/hudbridge"
