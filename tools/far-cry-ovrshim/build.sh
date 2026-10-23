#!/bin/bash
# Build ovrshim (32-bit proxy openvr_api.dll) and install it in Far Cry's Bin32 (mod's original -> openvr_api_real.dll).
set -e
cd "$(dirname "$0")"; mkdir -p out
cat > out/ovrshim.def <<'EOF'
LIBRARY openvr_api
EXPORTS
    VR_GetGenericInterface
    LiquidVR
    VRControlPanel
    VRHeadsetView
    VRPaths
    VRVirtualDisplay
    VR_GetInitToken
    VR_GetRuntimePath
    VR_GetStringForHmdError
    VR_GetVRInitErrorAsEnglishDescription
    VR_GetVRInitErrorAsSymbol
    VR_InitInternal
    VR_InitInternal2
    VR_IsHmdPresent
    VR_IsInterfaceVersionValid
    VR_IsRuntimeInstalled
    VR_RuntimePath
    VR_ShutdownInternal
EOF
clang --target=i686-pc-windows-msvc -O2 -ffreestanding -fno-builtin -fno-stack-protector -mno-stack-arg-probe -Wall \
  -I/usr/include -c ovrshim.c -o out/ovrshim.obj
lld-link /nologo /dll /machine:x86 /safeseh:no /entry:DllMain /nodefaultlib /def:out/ovrshim.def /out:out/openvr_api.dll out/ovrshim.obj
file -b out/openvr_api.dll | cut -c1-60
objdump -p out/openvr_api.dll | sed -n '/Ordinal\/Name Pointer/,/^$/p' | head -22 | tr -s ' \t' ' ' | tr '\n' ' '; echo
B=~/.local/share/Steam/steamapps/common/FarCry/Bin32
if [ ! -f "$B/openvr_api_real.dll" ]; then mv "$B/openvr_api.dll" "$B/openvr_api_real.dll"; echo "Bin32/openvr_api_real.dll" >> ~/PCVR/FarCryVR/mod-files.txt; fi
cp -f out/openvr_api.dll "$B/openvr_api.dll"; echo installed
