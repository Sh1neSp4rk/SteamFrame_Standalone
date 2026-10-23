#!/bin/bash
# Quake-PCVR game folder on the Frame: the native binary, then the port's own setup.py (expansions, music, menu art,
# episode strings) against Steam's Quake. Big paks are hard-linked first so setup.py finds them and copies nothing.
set -e
S=~/PCVR/QuakePCVR/src
G=~/PCVR/QuakePCVR-game
Q=~/.local/share/Steam/steamapps/common/Quake
mkdir -p "$G/id1"
ln -f "$S/darkplaces-sdl" "$G/darkplaces-sdl"
ln -f "$Q/Id1/PAK0.PAK" "$G/id1/pak0.pak"
ln -f "$Q/Id1/PAK1.PAK" "$G/id1/pak1.pak"
for d in hipnotic rogue dopa mg1 ctf; do
  if [ -f "$Q/rerelease/$d/pak0.pak" ]; then mkdir -p "$G/$d"; ln -f "$Q/rerelease/$d/pak0.pak" "$G/$d/pak0.pak"; fi
done
cd "$G"
QQ_QUAKEDIR="$Q" python3 -I "$S/tools/setup.py" "$G" "$Q" 2>&1 | tail -25
cat > "$G/q1pc-run.sh" <<'EOF'
#!/bin/bash
# Steam launch wrapper for the native ARM64 Quake-PCVR build (Team Beef's QuakeQuest on DarkPlaces, GLX/OpenXR).
# Log: ~/PCVR/QuakePCVR-game/q1pc-last.log. Extra args pass through (e.g. -game hipnotic, -novr).
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11                                   # the OpenXR binding is GLX (Xlib)
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE   # Steam's session caps Mesa at GL 4.3
exec stdbuf -oL -eL ./darkplaces-sdl -basedir . -nohome "$@" > q1pc-last.log 2>&1
EOF
chmod +x "$G/q1pc-run.sh"
echo "--- folder"; ls -la "$G" | grep -v '^total'; du -sh "$G"; df -h /home | tail -1
