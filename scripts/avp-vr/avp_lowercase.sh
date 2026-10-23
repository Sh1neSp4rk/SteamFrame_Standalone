#!/bin/bash
# Replaces the folder-level links in ~/PCVR/AVPVR-game with real lowercase folders whose
# files are lowercase-named symlinks to the Steam install, which stays untouched.
set -e
G="$HOME/.local/share/Steam/steamapps/common/Aliens versus Predator Classic"
D=~/PCVR/AVPVR-game
cd "$D"
for a in FMVs avp_huds avp_rifs fastfile language.txt default.cfg; do
  [ -L "$a" ] && rm "$a"
done
cd "$G"
find FMVs avp_huds avp_rifs fastfile Text -type f | while read -r f; do
  lc=$(printf '%s' "$f" | tr '[:upper:]' '[:lower:]')
  mkdir -p "$D/$(dirname "$lc")"
  ln -sfn "$G/$f" "$D/$lc"
done
ln -sfn "$G/language.txt" "$D/language.txt"
ln -sfn "$G/default.cfg" "$D/default.cfg"
cd "$D"
echo "files linked: $(find fmvs avp_huds avp_rifs fastfile text -type l | wc -l)"
ls
