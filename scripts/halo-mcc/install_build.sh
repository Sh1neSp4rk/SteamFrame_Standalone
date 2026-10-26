#!/bin/bash
# Installs a from-source HaloMCCVR.dll (+ assets) over the 0.5.1 mod, keeping the 0.5.1 launcher and the user's cfg,
# plus the Halo build of the frame_quadfix layer (~/PCVR/HaloMCCVR/frame-quadfix = tools/frame-quadfix from the repo).
# Stage the DLL first: copy HaloMCCVR.dll (and assets/fonts) from the Windows build to /tmp/mccbuild/.
set -e
G="$HOME/.local/share/Steam/steamapps/common/Halo The Master Chief Collection/Halo_MCC_VR"
if pgrep -f "[M]CC-Win64-Shipping|[H]aloMCCVRLauncher" >/dev/null; then echo "MCC running: not installed"; exit 1; fi
B=~/PCVR/HaloMCCVR/bak/mod-0.5.1
if [ ! -d $B ]; then mkdir -p $B; cp -a "$G"/HaloMCCVR.dll "$G"/MANUAL-README.txt "$G"/RELEASE-NOTES.md "$G"/THIRD-PARTY-LICENSES.txt "$G"/LICENSE "$G"/halomccvr.cfg $B/; echo "0.5.1 backed up to $B"; fi
cp -f /tmp/mccbuild/HaloMCCVR.dll "$G/HaloMCCVR.dll"
mkdir -p "$G/assets/fonts"; cp -f /tmp/mccbuild/assets/fonts/* "$G/assets/fonts/" 2>/dev/null || true
for f in MANUAL-README.txt THIRD-PARTY-LICENSES.txt LICENSE; do [ -f /tmp/mccbuild/$f ] && cp -f /tmp/mccbuild/$f "$G/"; done
cp -f ~/PCVR/HaloMCCVR/frame-quadfix/halo/out/frame_quadfix.dll ~/PCVR/HaloMCCVR/frame-quadfix/halo/out/frame_quadfix.json "$G/"
sha256sum "$G/HaloMCCVR.dll" "$G/frame_quadfix.dll" | cut -c1-16; echo installed
