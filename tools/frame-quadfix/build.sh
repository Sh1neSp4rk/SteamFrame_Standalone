#!/bin/bash
# Build frame_quadfix.dll (x86-64 Windows OpenXR API layer) with clang + lld-link, no SDK; register it as an implicit
# layer in the "Unreal Revived VR" prefix (HKLM, read even though Wine runs elevated), install next to the game.
set -e
cd "$(dirname "$0")"; mkdir -p out
cat > out/msvcrt.def <<'EOF'
LIBRARY msvcrt
EXPORTS
    fopen
    fprintf
    fflush
    getenv
    sqrt
    memcpy
    memset
EOF
for f in $(sed -n 's/^    //p' out/msvcrt.def); do echo "void $f(void) {}"; done > out/msvcrt_stub.c
clang --target=x86_64-pc-windows-msvc -w -c out/msvcrt_stub.c -o out/msvcrt_stub.obj
lld-link /nologo /dll /noentry /machine:x64 /def:out/msvcrt.def /out:out/msvcrt.dll out/msvcrt_stub.obj >/dev/null
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -fno-builtin -mno-stack-arg-probe \
  -Wall -I/usr/include -c quadfix.c -o out/quadfix.obj
lld-link /nologo /dll /machine:x64 /entry:DllMain /nodefaultlib /out:out/frame_quadfix.dll out/quadfix.obj out/msvcrt.lib
cat > out/frame_quadfix.json <<'EOF'
{
    "file_format_version": "1.0.0",
    "api_layer": {
        "name": "XR_APILAYER_frame_quadfix",
        "library_path": ".\\frame_quadfix.dll",
        "api_version": "1.0",
        "implementation_version": "1",
        "description": "Steam Frame: per-eye quad layers -> one quad for both eyes",
        "disable_environment": "DISABLE_FRAME_QUADFIX"
    }
}
EOF
file -b out/frame_quadfix.dll | cut -c1-60
D=~/PCVR/UnrealRevivedVR; id=$(cat $D/appid.txt); X=~/.local/share/Steam/steamapps/compatdata/$id/pfx
S="$X/drive_c/Games/Unreal Revived/System64"
python3 ~/PCVR/bin/steam_shortcuts.py stop $id >/dev/null 2>&1; pkill -f '[U]nrealRevived(VR)?\.exe' 2>/dev/null; sleep 5
pgrep -a -f "compatdata/$id" | grep -q wineserver && { echo "wineserver still up"; exit 1; }
cp -f out/frame_quadfix.dll out/frame_quadfix.json "$S/"
cp -n $X/system.reg $X/system.reg.orig
python3 - "$X/system.reg" <<'EOF'
import sys, time
p = sys.argv[1]; s = open(p, encoding='utf-8', errors='surrogateescape').read()
key = r'[Software\\Khronos\\OpenXR\\1\\ApiLayers\\Implicit]'
val = r'"C:\\Games\\Unreal Revived\\System64\\frame_quadfix.json"=dword:00000000'
if val in s: print('implicit layer already registered')
else:
    if key in s:
        i = s.index(key); j = s.index('\n', i); s = s[:j+1] + val + '\n' + s[j+1:]
    else:
        s = s.rstrip('\n') + '\n\n%s %d\n%s\n' % (key, int(time.time()), val)
    open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s); print('implicit layer registered')
EOF
grep -n -A2 'ApiLayers\\\\Implicit\]' $X/system.reg | head -4
