#!/bin/bash
# Native ARM64 build of JKXRL (Jedi Academy + Jedi Outcast, Vulkan + OpenXR) for the Steam Frame.
cd ~/PCVR/JKXR/src
[ -f ~/PCVR/JKXR/jk_port.py ] && { python3 ~/PCVR/JKXR/jk_port.py || exit 1; }
export PKG_CONFIG_PATH=$HOME/PCVR/JKXR/sdl3/lib/pkgconfig
BUILD=OpenJK/build-frame
if [ ! -f $BUILD/CMakeCache.txt ] || [ "$1" = reconf ]; then
  rm -rf $BUILD
  cmake -S OpenJK -B $BUILD -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$HOME/PCVR/JKXR/sdl3" \
    -DCMAKE_EXE_LINKER_FLAGS="-L/opt/steamvr/bin/linuxarm64 -Wl,-rpath,/opt/steamvr/bin/linuxarm64 -Wl,-rpath,$HOME/PCVR/JKXR/sdl3/lib" \
    -DCMAKE_SHARED_LINKER_FLAGS="-L/opt/steamvr/bin/linuxarm64 -Wl,-rpath,/opt/steamvr/bin/linuxarm64" \
    -DOPENXR_LOADER_LIBRARY=/opt/steamvr/bin/linuxarm64/libopenxr_loader.so \
    -DBuildMPEngine=OFF -DBuildMPRdVanilla=OFF -DBuildMPDed=OFF \
    -DBuildMPGame=OFF -DBuildMPCGame=OFF -DBuildMPUI=OFF \
    -DBuildSPEngine=ON -DBuildSPGame=ON -DBuildSPRdVanilla=OFF -DBuildSPRdVulkan=ON \
    -DBuildJK2SPEngine=ON -DBuildJK2SPGame=ON -DBuildJK2SPRdVanilla=OFF -DBuildJK2SPRdVulkan=ON \
    -DBuildTests=OFF > ~/PCVR/JKXR/configure.log 2>&1 || { grep -E -A4 'CMake Error' ~/PCVR/JKXR/configure.log | head -30; exit 1; }
  grep -E 'Architecture is|OpenXR|SDL3|Vulkan' ~/PCVR/JKXR/configure.log | head
fi
cmake --build $BUILD -j8 > ~/PCVR/JKXR/build.log 2>&1; rc=$?
grep -E 'error:|undefined reference|FAILED' ~/PCVR/JKXR/build.log | head -30
[ $rc = 0 ] || { tail -5 ~/PCVR/JKXR/build.log; exit 1; }
./make_z_vr_assets_pk3.sh > ~/PCVR/JKXR/pk3.log 2>&1 || { tail ~/PCVR/JKXR/pk3.log; exit 1; }
find $BUILD -maxdepth 4 -type f \( -name 'open*_sp.*' -o -name '*.so' \) -newer ~/PCVR/JKXR/configure.log | sed "s|$BUILD/||"
ls -la assets/*.pk3 | cut -c25-
