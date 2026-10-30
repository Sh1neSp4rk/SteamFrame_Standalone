#!/bin/bash
# Build frame_doompad.dll (x86-64 Windows OpenXR API layer) with clang + lld-link and no Windows SDK.
# Runs on the Frame (clang and the OpenXR headers are there) or any Linux box. Output: out/frame_doompad.{dll,json}
set -e
cd "$(dirname "$0")"; mkdir -p out
implib() {   # implib <dll name> <function>...
    local lib=$1; shift
    { echo "LIBRARY $lib"; echo "EXPORTS"; for f in "$@"; do echo "    $f"; done; } > out/$lib.def
    for f in "$@"; do echo "void $f(void) {}"; done > out/${lib}_stub.c
    clang --target=x86_64-pc-windows-msvc -w -c out/${lib}_stub.c -o out/${lib}_stub.obj
    lld-link /nologo /dll /noentry /machine:x64 /def:out/$lib.def /out:out/$lib.dll out/${lib}_stub.obj >/dev/null
}
implib kernel32 GetModuleHandleA VirtualProtect GetModuleFileNameA
implib user32 SendInput
implib msvcrt fopen fprintf fflush getenv memcpy memset
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -fno-builtin -mno-stack-arg-probe \
  -Wall -I/usr/include -c doompad.c -o out/doompad.obj
lld-link /nologo /dll /machine:x64 /entry:DllMain /nodefaultlib /out:out/frame_doompad.dll out/doompad.obj \
  out/msvcrt.lib out/kernel32.lib out/user32.lib
cat > out/frame_doompad.json <<'EOF'
{
    "file_format_version": "1.0.0",
    "api_layer": {
        "name": "XR_APILAYER_frame_doompad",
        "library_path": ".\\frame_doompad.dll",
        "api_version": "1.0",
        "implementation_version": "1",
        "description": "Steam Frame: full Xbox button set for KHARVOX (DOOM 2016 VR); inactive in other processes",
        "disable_environment": "DISABLE_FRAME_DOOMPAD"
    }
}
EOF
file -b out/frame_doompad.dll | cut -c1-60
