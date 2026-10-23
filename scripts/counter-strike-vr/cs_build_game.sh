#!/bin/bash
# Build CSVR's client, menu, ReGameDLL server and YaPB bots natively and install into ~/PCVR/CSVR/game.
cd ~/PCVR/CSVR/src
python3 ~/PCVR/CSVR/cs_port_client.py || exit 1
OUT=~/PCVR/CSVR/game
if [ ! -f build/CMakeCache.txt ] || [ "$1" = reconf ]; then
  rm -rf build
  CFLAGS=-std=gnu17 cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT" > ~/PCVR/CSVR/game-configure.log 2>&1 \
    || { grep -i -E 'error|warning' -A3 ~/PCVR/CSVR/game-configure.log | head -40; exit 1; }
  grep -E '^-- (Library|Install|Target|Build|Using|Found)' ~/PCVR/CSVR/game-configure.log | head -20
fi
cmake --build build -j8 > ~/PCVR/CSVR/game-build.log 2>&1; rc=$?
grep -E 'error:|Error |undefined reference|FAILED' ~/PCVR/CSVR/game-build.log | head -30
[ $rc = 0 ] || { tail -10 ~/PCVR/CSVR/game-build.log; exit 1; }
cmake --install build > ~/PCVR/CSVR/game-install.log 2>&1 || { tail -15 ~/PCVR/CSVR/game-install.log; exit 1; }
grep -E 'Installing' ~/PCVR/CSVR/game-install.log | sed "s|$OUT/||" | head -40
