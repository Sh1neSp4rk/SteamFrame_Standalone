#!/bin/bash
# Native ARM64 PCVR build of AVP VR on the Frame. Log: ~/PCVR/AVPVR/build-arm64vr.log
set -e
cd ~/PCVR/AVPVR
mkdir -p source/extern/OpenXR/lib/linux/arm64
cp -f /opt/steamvr/bin/linuxarm64/libopenxr_loader.so source/extern/OpenXR/lib/linux/arm64/
exec > >(tee build-arm64vr.log) 2>&1
cmake -S source -B .build-linux/arm64vr -G Ninja \
  -DAVP_ENABLE_LINUX=ON -DCMAKE_BUILD_TYPE=Release -DAVP_ENABLE_PCVR=ON \
  -DCMAKE_C_FLAGS="-std=gnu17 -fpermissive"  # GCC 15: C23 default breaks K&R () prototypes; 14+ made old pointer warnings errors
cmake --build .build-linux/arm64vr -j"$(nproc)"
echo "== outputs"
find .build-linux/arm64vr build/linux -maxdepth 3 -name 'avpvr*' -type f 2>/dev/null | xargs -r file
