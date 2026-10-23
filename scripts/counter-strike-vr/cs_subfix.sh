#!/bin/bash
# Bring the engine's nested submodules to their pinned commits (shallow fetch by sha, full fetch as fallback).
cd ~/PCVR/CSVR/src/3rdparty/xash3d-fwgs
git submodule sync -q
git submodule status | while read -r st path rest; do
  sha=${st#[-+U ]}; sha=${st:1}; [ "${st:0:1}" = "-" ] || [ "${st:0:1}" = "+" ] || continue
  want=$(git ls-tree HEAD "$path" | awk '{print $3}')
  echo "== $path -> $want"
  git submodule update --init --depth 1 -- "$path" >/dev/null 2>&1 || {
    url=$(git config -f .gitmodules --get "submodule.$path.url"); [ -z "$url" ] && url=$(git config -f .gitmodules --get-regexp '\.path$' | awk -v p="$path" '$2==p {sub(/\.path$/,"",$1); print $1}' | xargs -I{} git config -f .gitmodules --get {}.url)
    rm -rf "$path"; mkdir -p "$path"
    (cd "$path" && git init -q && git remote add origin "$url" && { git fetch -q --depth 1 origin "$want" || git fetch -q origin; } && git checkout -q "$want") && echo "   fetched by sha" || echo "   FAILED"
  }
done
echo "=== status"; git submodule status | cut -c1-100
du -sh ~/PCVR/CSVR/src
