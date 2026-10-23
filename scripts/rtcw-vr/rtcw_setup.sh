#!/bin/bash
# RealRTCW XR game folder on the Frame: the native binary, renderer and game modules from the build, RealRTCW's data
# (Steam app 1379630) and the original RTCW paks (9010) hard-linked into Main, and the VR assets pk3 zipped from the
# repo's z_zzzRealRTCWXR folder (what make_z_vr_assets_pk3.bat does on Windows).
set -e
S=~/PCVR/RealRTCWXR/src
B=$S/build/release-linux-aarch64
G=~/PCVR/RealRTCWXR-game
RR=~/.local/share/Steam/steamapps/common/RealRTCW
RT="$HOME/.local/share/Steam/steamapps/common/Return to Castle Wolfenstein"
# the engine's base game dir is lowercase "main" (Windows didn't care; Linux does)
mkdir -p "$G/main"; [ -d "$G/Main" ] && [ ! -L "$G/Main" ] && { mv -f "$G"/Main/* "$G/main/" 2>/dev/null; rmdir "$G/Main"; }
ln -sfn main "$G/Main"
# binaries
for f in "$B"/RealRTCW* "$B"/renderer_sp_*.so; do [ -f "$f" ] && ln -f "$f" "$G/$(basename "$f")"; done
for f in "$B"/main/*.so; do [ -f "$f" ] && ln -f "$f" "$G/Main/$(basename "$f")"; done
# RealRTCW data (pk3 + cfg), then the original game's single-player paks. Old links first: a Steam update replaces
# the files (new inodes), and a branch switch can drop pk3s that must not keep loading.
rm -f "$G"/main/*.pk3 "$G"/main/*.cfg
for f in "$RR"/Main/*.pk3 "$RR"/Main/*.cfg; do [ -f "$f" ] && ln -f "$f" "$G/Main/$(basename "$f")"; done
for f in "$RT"/Main/pak0.pk3 "$RT"/Main/sp_pak1.pk3 "$RT"/Main/sp_pak2.pk3 "$RT"/Main/sp_pak3.pk3 "$RT"/Main/sp_pak4.pk3; do
  [ -f "$f" ] && ln -f "$f" "$G/Main/$(basename "$f")"
done
# VR assets pk3
python3 -I - "$S/z_zzzRealRTCWXR" "$G/Main/z_zzzRealRTCWXR.pk3" <<'EOF'
import os, sys, zipfile
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for d, _, files in os.walk(src):
        for f in files:
            p = os.path.join(d, f)
            z.write(p, os.path.relpath(p, src))
print("wrote", dst, os.path.getsize(dst), "bytes")
EOF
cat > "$G/rtcwxr-run.sh" <<'EOF'
#!/bin/bash
# Steam launch wrapper for the native ARM64 RealRTCW XR build (Team Beef's OpenXR RealRTCW, GLX/OpenXR port).
# Log: ~/PCVR/RealRTCWXR-game/rtcwxr-last.log. Extra args pass through.
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11                                   # the OpenXR binding is GLX (Xlib)
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE   # Steam's session caps Mesa at GL 4.3
[ -f "$PWD/env.test" ] && . "$PWD/env.test"   # test env vars (RTCWXR_DEBUG_INPUT=1 traces input to the log)
BIN=$(ls RealRTCW.* 2>/dev/null | grep -v '\.so$' | head -1)
if [ -f gdb.test ]; then  # debugging: backtrace into rtcwxr-gdb.log (ptrace attach is blocked; run under gdb instead)
  exec gdb -batch -ex run -ex bt -ex quit --args "./$BIN" +set fs_basepath "$PWD" +set fs_homepath "$PWD/home" "$@" > rtcwxr-gdb.log 2>&1
fi
exec stdbuf -oL -eL "./$BIN" +set fs_basepath "$PWD" +set fs_homepath "$PWD/home" "$@" > rtcwxr-last.log 2>&1
EOF
chmod +x "$G/rtcwxr-run.sh"
echo "--- folder"; ls -la "$G" | grep -v '^total'; ls "$G/Main" | wc -l; du -sh "$G"; df -h /home | tail -1
