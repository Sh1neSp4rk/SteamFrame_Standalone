#!/bin/bash
# Assemble the playable CSVR folder (~/PCVR/CSVR/game) from the native build + Steam's Counter-Strike data, and add
# the "Counter-Strike VR" Steam shortcut. Steam files are HARD-LINKED (no extra space, survive an uninstall); anything
# CSVR replaces is copied with --remove-destination so the Steam originals are never written to.
set -e
G=~/PCVR/CSVR/game; S=~/PCVR/CSVR/src; HL=~/.local/share/Steam/steamapps/common/Half-Life
[ -x $G/xash3d ] && [ -f $G/cstrike/cl_dlls/client_arm64.so ] || { echo "build first (cs_build_engine.sh, cs_build_game.sh)"; exit 1; }
[ -d $HL/cstrike ] || { echo "Steam Counter-Strike (app 10) not installed"; exit 1; }
cp -alrn $HL/valve/. $G/valve/
cp -alrn $HL/cstrike/. $G/cstrike/
# what the Quest app copies at every start: VR weapon/shield models and sprites (replace, never write through a link)
cp -r --remove-destination $S/3rdparty/cs16client-extras/models/. $G/cstrike/models/
cp -r --remove-destination $S/3rdparty/cs16client-extras/sprites/. $G/cstrike/sprites/
# YaPB configs (bots run with -dll dlls/yapb_arm64.so; yapb loads cs_arm64.so itself)
cp -r --remove-destination $S/3rdparty/yapb/cfg/addons $G/cstrike/
cat > $G/csvr-run.sh <<'EOF'
#!/bin/bash
# Steam launch wrapper for the native ARM64 CSVR build (Team Beef's Counter-Strike 1.6 VR on Xash3D FWGS, GLX/OpenXR).
# Log: ~/PCVR/CSVR/game/csvr-last.log (+ cstrike/engine.log). Extra args pass through.
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11                                   # the OpenXR binding is GLX (Xlib)
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE   # Steam's session caps Mesa at GL 4.3
export LD_LIBRARY_PATH="/opt/steamvr/bin/linuxarm64:$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"   # SteamVR's OpenXR loader
export XASH3D_GAME=cstrike
python3 ~/PCVR/CSVR/cs_name.py > /dev/null 2>&1 # player name from Steam (no keyboard in VR)
exec stdbuf -oL -eL ./xash3d -game cstrike -ref gl -dll dlls/yapb_arm64.so -console -log +exec frame_controls.cfg +exec frame_name.cfg "$@" > csvr-last.log 2>&1
EOF
chmod +x $G/csvr-run.sh
du -sh --apparent-size $G | cut -f1 | sed 's/^/apparent size: /'; du -sh $G | cut -f1 | sed 's/^/new disk use (links not counted twice with Steam): /'
python3 ~/PCVR/bin/steam_shortcuts.py list | grep -q '"Counter-Strike VR"' && echo "shortcut exists" || \
  python3 ~/PCVR/bin/steam_shortcuts.py add "Counter-Strike VR" $G/csvr-run.sh $G
python3 ~/PCVR/bin/steam_shortcuts.py list | python3 -c "import json,sys; print([a for a in json.load(sys.stdin) if a['name']=='Counter-Strike VR'])"
