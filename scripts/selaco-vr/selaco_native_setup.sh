#!/bin/bash
# Assemble the native SelacoVR game folder from the ARM64 build and write its run script.
set -e
S=~/PCVR/SelacoVR; G=$S/game; B=$S/build
mkdir -p $G/windows-build
# park the Windows build (it does not run under Proton/FEX)
for f in Selaco.exe openvr_api.dll zmusic.dll openal32.dll libsndfile-1.dll SelacoVR.bat Selaco.bat; do [ -e $G/$f ] && mv $G/$f $G/windows-build/; done
mv $G/*.dll $G/windows-build/ 2>/dev/null || true
cp -f $B/Selaco $B/qzdoom.pk3 $B/brightmaps.pk3 $B/lights.pk3 $G/
rm -rf $G/soundfonts $G/fm_banks; cp -r $B/soundfonts $B/fm_banks $G/
cp -f $S/zmusic/install/lib/libzmusic.so* $G/
cp -f /opt/steamvr/bin/linuxarm64/libopenvr_api.so $G/
cat > $G/selacovr-run.sh <<'EOF'
#!/bin/bash
# Native ARM64 SelacoVR (OpenVR via SteamVR). Extra args pass through. ~/PCVR/SelacoVR/env.test is sourced if present.
cd "$(dirname "$0")"
export LD_LIBRARY_PATH="$PWD:$LD_LIBRARY_PATH"
export SDL_VIDEODRIVER=x11
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE
[ -f ../env.test ] && source ../env.test
exec ./Selaco +logfile selaco.log +vid_preferbackend 0 +vid_vsync false +vr_mode 10 +vid_fullscreen 0 +vid_defwidth 1400 +vid_defheight 1400 "$@" > selaco-stdout.log 2>&1
EOF
chmod +x $G/selacovr-run.sh $G/Selaco
echo "--- game dir"; ls $G
echo "--- shortcut tool usage"; python3 ~/PCVR/bin/steam_shortcuts.py 2>&1 | head -15
grep -n -E 'def |SetShortcut|elif cmd|if cmd' ~/PCVR/bin/steam_shortcuts.py | head -30
echo "--- current shortcut"; python3 ~/PCVR/bin/steam_shortcuts.py show $(cat $S/appid.txt) 2>&1 | head -12
