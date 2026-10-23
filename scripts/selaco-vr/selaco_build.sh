#!/bin/bash
# Configure + build SelacoVR natively (ARM64, OpenVR dynamic, system SDL2/OpenAL, our ZMusic).
S=~/PCVR/SelacoVR
python3 $S/selaco_port.py || exit 1
Z=$S/zmusic/install
if [ ! -f $S/build/build.ninja ]; then
cmake -S $S/src -B $S/build -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_OPENVR=ON -DDYN_OPENVR=ON -DOPENVR_SDK_PATH=$S/openvr \
  -DZMUSIC_INCLUDE_DIR=$Z/include -DZMUSIC_LIBRARIES=$Z/lib/libzmusic.so \
  -DHAVE_VULKAN=ON -DHAVE_GLES2=ON > $S/cmake.log 2>&1 || { echo CMAKE FAILED; grep -v -E '^--' $S/cmake.log | tail -30; exit 1; }
fi
grep -E 'OPENVR|openvr|ZMusic|SDL2|Backtrace' $S/cmake.log | head
ninja -C $S/build -j6 ${1:-} > $S/build.log 2>&1; rc=$?
echo "ninja rc=$rc"
if [ $rc -ne 0 ]; then grep -E 'error|Error|FAILED' $S/build.log | grep -v -E 'Werror|-Wno-error' | head -25 | cut -c1-240; fi
ls -la $S/build/selaco* $S/build/*.pk3 2>/dev/null | cut -c25-
