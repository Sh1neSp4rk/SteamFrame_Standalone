#!/bin/bash
# Builds ~/PCVR/D3BFGVR-game: the native binary, base/ = links to the Steam game's base files plus the
# engine's own base/ files from the repo, and "Fully Possessed" = the mod's assets. Steam folder untouched.
set -e
S=~/.local/share/Steam
STEAMBASE="$S/steamapps/common/DOOM 3 BFG Edition/base"
R=~/PCVR/D3BFGVR
D=~/PCVR/D3BFGVR-game
mkdir -p "$D/base"
cp -f "$R/build/Doom3BFGVR" "$D/"
for f in "$STEAMBASE"/*; do ln -sfn "$f" "$D/base/$(basename "$f")"; done
for f in "$R/base"/*; do ln -sfn "$f" "$D/base/$(basename "$f")"; done   # renderprogs etc. (wins over Steam's default.cfg)
ln -sfn "$R/vr_assets/Fully Possessed" "$D/Fully Possessed"
cat > "$D/d3bfgvr-run.sh" <<'EOF'
#!/bin/bash
# Steam launch wrapper for the native ARM64 Doom 3 BFG VR (Fully Possessed). Log: d3bfgvr-last.log
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11
exec ./Doom3BFGVR +set fs_basepath "$PWD" "$@" > d3bfgvr-last.log 2>&1
EOF
chmod +x "$D/d3bfgvr-run.sh"
ls -la "$D" | cut -c1-150
ls "$D/base" | tr '\n' ' '; echo
python3 ~/PCVR/bin/steam_shortcuts.py list | grep -q 'Doom 3 BFG VR' || \
  python3 ~/PCVR/bin/steam_shortcuts.py add 'Doom 3 BFG VR' "$D/d3bfgvr-run.sh" "$D"
python3 ~/PCVR/bin/steam_shortcuts.py list
