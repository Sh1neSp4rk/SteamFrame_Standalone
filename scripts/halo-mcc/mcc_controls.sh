#!/bin/bash
# Installs the Frame binding for Halo MCC VR over SteamVR's generated Touch defaults (read-only, backups kept),
# turns off the mod's scope lens (an extra full world render per frame), and registers the frame_quadfix layer
# (Touch-only profile filter) in MCC's prefix. The layer step needs MCC closed (wineserver writes system.reg).
set -e
H=~/PCVR/HaloMCCVR; mkdir -p $H/bak
G="$HOME/.local/share/Steam/steamapps/common/Halo The Master Chief Collection"
X=~/.config/openvr/config/openxr
python3 $H/mcc_binding.py $H/mcc_frame_binding.json
for f in $X/steam.app.976730_oculus_touch_*_binding.json; do
  [ -f "$H/bak/$(basename $f)" ] || cp "$f" "$H/bak/"
  chmod 644 "$f"; cp $H/mcc_frame_binding.json "$f"; chmod 444 "$f"
done
ls -la $X/steam.app.976730_oculus_touch_* | awk '{print $1, $NF}'
sed -i -E 's/^scope_enabled = 1/scope_enabled = 0/' "$G/Halo_MCC_VR/halomccvr.cfg"
grep -E '^scope_enabled' "$G/Halo_MCC_VR/halomccvr.cfg"
# layer files next to the mod (never while MCC runs: Wine has the DLL mapped)
if pgrep -f '[M]CC-Win64-Shipping|[H]aloMCCVRLauncher' >/dev/null; then echo "MCC running: layer install deferred"; exit 0; fi
# Halo build of the layer (tools/frame-quadfix/halo from the repo, copied to ~/PCVR/HaloMCCVR/frame-quadfix)
bash ~/PCVR/HaloMCCVR/frame-quadfix/halo/build.sh >/dev/null
cp -f ~/PCVR/HaloMCCVR/frame-quadfix/halo/out/frame_quadfix.dll ~/PCVR/HaloMCCVR/frame-quadfix/halo/out/frame_quadfix.json "$G/Halo_MCC_VR/"
REG=~/.local/share/Steam/steamapps/compatdata/976730/pfx/system.reg
[ -f $H/bak/system.reg ] || cp $REG $H/bak/system.reg
KEY='[Software\\Khronos\\OpenXR\\1\\ApiLayers\\Implicit]'
VAL='"S:\\steamapps\\common\\Halo The Master Chief Collection\\Halo_MCC_VR\\frame_quadfix.json"=dword:00000000'
python3 - "$REG" "$KEY" "$VAL" <<'PY'
import sys
reg, key, val = sys.argv[1:]
s = open(reg, encoding="utf-8", errors="surrogateescape").read()
if val in s: print("layer already registered"); sys.exit()
i = s.find(key)
if i < 0:
    s = s.rstrip("\n") + "\n\n" + key + " 1761400000\n#time=1dc4600000000000\n" + val + "\n"
else:
    j = s.find("\n", i); s = s[:j+1] + val + "\n" + s[j+1:]
open(reg, "w", encoding="utf-8", errors="surrogateescape").write(s); print("layer registered")
PY
grep -A3 -F "$KEY" $REG
