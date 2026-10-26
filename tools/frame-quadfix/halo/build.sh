#!/bin/bash
# Build the Halo MCC VR variant of frame_quadfix (frame_quadfix.dll, x86-64 Windows OpenXR API layer) with clang +
# lld-link and no Windows SDK. Runs on the Frame (clang 19 and the OpenXR headers are there) or any Linux box.
# Output: out/frame_quadfix.dll and out/frame_quadfix.json. The same DLL works under Proton on the Frame and on
# Windows (a streaming PC); it does nothing in any process other than MCC-Win64-Shipping.exe.
# Install it with scripts/halo-mcc/install_build.sh (Frame) or scripts/halo-mcc/windows/install-pc.ps1 (Windows).
set -e
cd "$(dirname "$0")"; mkdir -p out
python3 assemble.py .
# import libraries from .def stubs
implib() {   # implib <dll name> <function>...
    local lib=$1; shift
    { echo "LIBRARY $lib"; echo "EXPORTS"; for f in "$@"; do echo "    $f"; done; } > out/$lib.def
    for f in "$@"; do echo "void $f(void) {}"; done > out/${lib}_stub.c
    clang --target=x86_64-pc-windows-msvc -w -c out/${lib}_stub.c -o out/${lib}_stub.obj
    lld-link /nologo /dll /noentry /machine:x64 /def:out/$lib.def /out:out/$lib.dll out/${lib}_stub.obj >/dev/null
}
implib kernel32 GetModuleHandleA GetProcAddress VirtualProtect GetModuleFileNameA
implib msvcrt fopen fprintf fflush getenv sqrt memcpy memset fseek fread
clang --target=x86_64-pc-windows-msvc -O2 -ffreestanding -fno-stack-protector -fno-builtin -mno-stack-arg-probe \
  -Wall -I/usr/include -c framexr.c -o out/framexr.obj
lld-link /nologo /dll /machine:x64 /entry:DllMain /nodefaultlib /out:out/frame_quadfix.dll out/framexr.obj \
  out/msvcrt.lib out/kernel32.lib
cat > out/frame_quadfix.json <<'EOF'
{
    "file_format_version": "1.0.0",
    "api_layer": {
        "name": "XR_APILAYER_frame_quadfix",
        "library_path": ".\\frame_quadfix.dll",
        "api_version": "1.0",
        "implementation_version": "1",
        "description": "Steam Frame helpers for Halo MCC VR (Touch-only profile, View/D-pad bridge, quad fixes); inactive in other processes",
        "disable_environment": "DISABLE_FRAME_QUADFIX"
    }
}
EOF
file -b out/frame_quadfix.dll | cut -c1-60
