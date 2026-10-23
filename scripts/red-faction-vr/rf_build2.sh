#!/bin/bash
# Build image with a newer MinGW (Debian trixie: GCC 14, needed for the mod's C++23 "deducing this"), then rebuild.
D=~/PCVR/RedFactionVR
cat > $D/container/Containerfile <<'EOF'
FROM docker.io/library/debian:trixie-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends mingw-w64 cmake ninja-build make git ca-certificates python3 && rm -rf /var/lib/apt/lists/*
EOF
podman build -t afvr-mingw14 $D/container 2>&1 | tail -2
podman run --rm localhost/afvr-mingw14 i686-w64-mingw32-g++-posix --version | head -1
rm -rf $D/src/build/CMakeCache.txt $D/src/build/CMakeFiles
podman run --rm -v $D/src:/src:Z localhost/afvr-mingw14 bash -c '
  cmake -S /src -B /src/build -G Ninja -DCMAKE_TOOLCHAIN_FILE=/src/cmake/mingw-ubuntu.cmake -DCMAKE_BUILD_TYPE=Release -DAF_ENABLE_OPENXR=ON -DCMAKE_CXX_FLAGS="-DWINAPI_PARTITION_SYSTEM=0" -DCMAKE_C_FLAGS="-DWINAPI_PARTITION_SYSTEM=0" > /src/build-cmake.log 2>&1 || { echo CMAKE FAILED; tail -30 /src/build-cmake.log; exit 1; }
  ninja -C /src/build -k 0 > /src/build.log 2>&1; rc=$?; echo "ninja rc=$rc"
  [ $rc -ne 0 ] && grep -E "error:" /src/build.log | sed -E "s/:[0-9]+:[0-9]+:/:/" | sort | uniq -c | sort -rn | head -20 | cut -c1-220
  find /src/build -iname "AlpineFaction*.dll" -o -iname "AlpineFaction*.exe" | head; exit $rc'
