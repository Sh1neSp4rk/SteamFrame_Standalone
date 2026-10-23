#!/bin/bash
# License note: the replacement source fragments in this file derive from RippeR37/q3vr (ioquake3), GPL-2.0,
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
# q3vr on the Frame: zink/GLX under gamescope offers no single-buffered fbconfig -> GLXBadFBConfig.
# Request a double-buffered window (VR frames go to OpenXR swapchains; the window is only a mirror).
set -e
S="$HOME/PCVR/Q3VR/src"; G="$HOME/PCVR/Q3VR-game"
cd "$S"
grep -q 'SDL_GL_SetAttribute( SDL_GL_DOUBLEBUFFER, 0 );' code/sdl/sdl_glimp.c && \
  sed -i 's|SDL_GL_SetAttribute( SDL_GL_DOUBLEBUFFER, 0 );|SDL_GL_SetAttribute( SDL_GL_DOUBLEBUFFER, 1 ); /* Frame: zink GLX has no single-buffered fbconfig */|' code/sdl/sdl_glimp.c
git diff --stat
cmake --build ../build -j6 2>&1 | grep -E -i 'error|FAILED|Linking C executable' | head
cp -f ../build/Release/q3vr "$G/q3vr"
sed -i 's|exec ./q3vr +set fs_basepath "$PWD" +set fs_homepath "$PWD/home"|exec ./q3vr +set fs_basepath "$PWD" +set fs_homepath "$PWD/home" +set r_ext_multisample 0|' "$G/q3vr-run.sh"
grep exec "$G/q3vr-run.sh"
bash ~/PCVR/bin/kill_app.sh 3668573126 > /dev/null 2>&1; sleep 3
bash ~/PCVR/Q3VR/q3_test.sh 2>&1 | grep -v -E 'Gamescope WSI|pak[0-9a-zQ]*\.pk3|ld.so'
