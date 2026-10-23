#!/bin/bash
# Build ZMusic 1.1.12 for ARM64 into ~/PCVR/SelacoVR/zmusic/install (system libsndfile/mpg123, dynamic fluidsynth).
set -e
Z=~/PCVR/SelacoVR/zmusic
cmake -S $Z -B $Z/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$Z/install -DDYN_SNDFILE=OFF -DDYN_MPG123=OFF > $Z/cmake.log 2>&1 || { tail -30 $Z/cmake.log; exit 1; }
ninja -C $Z/build > $Z/build.log 2>&1 || { grep -E 'error|Error' $Z/build.log | head -20; exit 1; }
ninja -C $Z/build install > /dev/null
echo "zmusic built:"; ls $Z/install/lib* $Z/install/include | head; file -L $Z/install/lib/libzmusic.so | cut -d, -f2
