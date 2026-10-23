#!/bin/bash
# Native ARM64 build of Doom 3 BFG VR (Fully Possessed) on the Frame. Log: ~/PCVR/D3BFGVR/build.log
# usage: build.sh [clean]
cd ~/PCVR/D3BFGVR
[ "$1" = clean ] && rm -rf build
mkdir -p build && cd build
# The SDK only gets linux64 on the link path; give the linker the ARM64 one too.
ln -sfn linuxarm64 ../neo/libs/OpenVR/lib/linux64-frame 2>/dev/null
{
# FFMPEG=OFF: Cinematic.cpp uses the pre-4.0 FFmpeg API (cutscenes are skipped without it).
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DSDL2=ON -DONATIVE=OFF -DFFMPEG=OFF \
  -DCMAKE_C_FLAGS="-fpermissive -w" \
  -DCMAKE_CXX_FLAGS="-std=gnu++14 -fpermissive -w -fno-strict-aliasing" \
  -DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG -std=gnu++14 -fpermissive -w -fno-strict-aliasing" \
  -DCMAKE_EXE_LINKER_FLAGS="-L$HOME/PCVR/D3BFGVR/neo/libs/OpenVR/lib/linuxarm64 -Wl,-rpath,\$ORIGIN" \
  ../neo && ninja -k 0 -j"$(nproc)"
} > ../build.log 2>&1
echo "exit=$?"
grep -E 'error:|FAILED:|undefined reference|No such file' ../build.log | sed 's|.*/neo/||' | sort | uniq -c | sort -rn | head -40
ls -la Doom3BFGVR RBDoom3BFG 2>/dev/null
