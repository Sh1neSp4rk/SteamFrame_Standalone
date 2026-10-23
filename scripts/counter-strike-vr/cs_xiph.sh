#!/bin/bash
# gitlab.xiph.org is down (502): fetch the same pinned commits from Xiph's GitHub mirrors.
cd ~/PCVR/CSVR/src/3rdparty/xash3d-fwgs
for pair in "3rdparty/libogg/libogg ogg" "3rdparty/opusfile/opusfile opusfile" "3rdparty/vorbis/vorbis-src vorbis"; do
  set -- $pair; path=$1; repo=$2
  want=$(git ls-tree HEAD "$path" | awk '{print $3}')
  rm -rf "$path"; mkdir -p "$path"
  (cd "$path" && git init -q && git remote add origin "https://github.com/xiph/$repo.git" &&
   { git fetch -q --depth 1 origin "$want" || git fetch -q origin; } && git checkout -q "$want") && echo "$path: $want ok" || echo "$path: FAILED"
done
git submodule status | grep -E 'ogg|opusfile|vorbis'
