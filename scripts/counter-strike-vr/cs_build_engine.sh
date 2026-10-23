#!/bin/bash
# Build the CSVR engine (Xash3D FWGS fork) natively for the Steam Frame and install into ~/PCVR/CSVR/game.
cd ~/PCVR/CSVR/src/3rdparty/xash3d-fwgs
python3 ~/PCVR/CSVR/cs_port.py || exit 1
OUT=~/PCVR/CSVR/game
if [ ! -f build/config.log ] || [ "$1" = reconf ]; then
  CFLAGS=-std=gnu17 ./waf configure -T release -8 --disable-soft --disable-vgui --disable-werror --prefix="$OUT" > ~/PCVR/CSVR/engine-configure.log 2>&1 || { tail -30 ~/PCVR/CSVR/engine-configure.log; exit 1; }
  grep -E "Checking for|not found|: no" ~/PCVR/CSVR/engine-configure.log | grep -v -E ': yes|: ok' | tail -15
fi
./waf build -j8 > ~/PCVR/CSVR/engine-build.log 2>&1; rc=$?
grep -E 'error|Error|undefined reference' ~/PCVR/CSVR/engine-build.log | head -40
[ $rc = 0 ] || { tail -15 ~/PCVR/CSVR/engine-build.log; exit 1; }
./waf install --destdir=/ > ~/PCVR/CSVR/engine-install.log 2>&1 || { tail -15 ~/PCVR/CSVR/engine-install.log; exit 1; }
ls -la "$OUT" | head -30
