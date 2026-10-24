#!/bin/bash
# Shallow clones for the native JKXRL build (user-approved 2026-10-23).
set -e
mkdir -p ~/PCVR/JKXR && cd ~/PCVR/JKXR
[ -d src ] || git clone -q --depth 1 https://github.com/Patola/JKXRL.git src
[ -d sdl3-src ] || git clone -q --depth 1 --branch release-3.4.18 https://github.com/libsdl-org/SDL.git sdl3-src
(cd src && echo "JKXRL $(git rev-parse --short HEAD) $(git log -1 --format=%cd --date=short)"; git submodule status 2>/dev/null | head)
(cd sdl3-src && echo "SDL $(git describe --tags 2>/dev/null || git rev-parse --short HEAD)")
du -sh src sdl3-src
ls src src/OpenJK | head -40
