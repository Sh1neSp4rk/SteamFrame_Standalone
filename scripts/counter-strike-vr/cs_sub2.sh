#!/bin/bash
# Nested submodules below the engine's own submodules (mainui/miniutl etc.), pinned commits.
cd ~/PCVR/CSVR/src/3rdparty/xash3d-fwgs
for top in $(git submodule status | awk '{print $2}'); do
  [ -f "$top/.gitmodules" ] || continue
  (cd "$top" && git submodule status 2>/dev/null | while read -r st path rest; do
     [ "${st:0:1}" = "-" ] || continue
     want=$(git ls-tree HEAD "$path" | awk '{print $3}')
     url=$(git config -f .gitmodules --get-regexp '\.path$' | awk -v p="$path" '$2==p {sub(/\.path$/,"",$1); print $1}' | xargs -I{} git config -f .gitmodules --get {}.url)
     rm -rf "$path"; mkdir -p "$path"
     (cd "$path" && git init -q && git remote add origin "$url" && { git fetch -q --depth 1 origin "$want" || git fetch -q origin; } && git checkout -q "$want") \
       && echo "$top/$path @ ${want:0:8} ok" || echo "$top/$path FAILED ($url)"
   done)
done
ls 3rdparty/mainui/miniutl | head -5
