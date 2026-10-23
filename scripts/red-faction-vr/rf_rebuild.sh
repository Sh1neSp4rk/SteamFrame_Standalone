#!/bin/bash
# Re-patch, incremental rebuild in the GCC 14 container, install the DLL, regenerate the binding, relaunch.
D=~/PCVR/RedFactionVR; G=~/.local/share/Steam/steamapps/common/"Red Faction"
python3 $D/rf_patch.py || exit 1
podman run --rm -v $D/src:/src:Z localhost/afvr-mingw14 bash -c 'ninja -C /src/build AlpineFaction > /src/build.log 2>&1; rc=$?; echo "ninja rc=$rc"; [ $rc -ne 0 ] && grep -E "error:" /src/build.log | head -12 | cut -c1-220; ls -la --time-style=+%T /src/build/bin/AlpineFaction.dll | cut -c25-'
bash $D/rf_install_dll.sh 2>&1 | grep -v -E 'Runtime adapter|feature level|Session state|refresh'
grep -a -E 'Recenter|recenter' "$G/logs/AlpineFaction.log" | tail -2 | cut -c1-140
