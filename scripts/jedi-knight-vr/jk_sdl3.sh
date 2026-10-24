#!/bin/bash
# Build SDL 3.4.18 into ~/PCVR/JKXR/sdl3 (private prefix; the system stays untouched).
cd ~/PCVR/JKXR/sdl3-src
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$HOME/PCVR/JKXR/sdl3 \
  -DSDL_SHARED=ON -DSDL_STATIC=OFF -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF -DSDL_X11=ON -DSDL_WAYLAND=ON -DSDL_X11_XSCRNSAVER=OFF \
  > ../sdl3-configure.log 2>&1 || { tail -30 ../sdl3-configure.log; exit 1; }
grep -E 'SDL_(X11|WAYLAND|VULKAN|PIPEWIRE|PULSEAUDIO|ALSA|HIDAPI)[^_]' ../sdl3-configure.log | head -12
cmake --build build -j8 > ../sdl3-build.log 2>&1 || { grep -E 'error' ../sdl3-build.log | head; exit 1; }
cmake --install build > /dev/null && ls ~/PCVR/JKXR/sdl3/lib*/ | head
