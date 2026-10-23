#!/bin/bash
# Installs DeusExHRVR 0.3.0 into DXHR:DC (238010) the way install.ps1 does, plus Frame fixes:
# x86-64 VC runtimes next to the 64-bit host (the prefix's are ARM64). Backs up everything it changes.
set -e
S=~/.local/share/Steam
G="$S/steamapps/common/Deus Ex Human Revolution Director's Cut"
PFX=$S/steamapps/compatdata/238010/pfx
X=~/PCVR/DeusExHRVR/extracted/DeusExHRVR
B="$G/DeusExHRVR-backup"
pgrep -f 'DXHRDC.exe' >/dev/null && { echo "game is running; close it first"; exit 1; }

echo "== payload"; (cd "$X/dist" && find . -type f | sort)
mkdir -p "$B"
(cd "$X/dist" && find . -type f) | while read -r f; do
  if [ -e "$G/$f" ]; then mkdir -p "$B/$(dirname "$f")"; cp -an "$G/$f" "$B/$f"; echo "backed up $f"; fi
done
cp -a "$X/dist/." "$G/"
cp -n "$X/DeusExHRVR.ini.example" "$G/DeusExHRVR.ini"

# 64-bit host: x86-64 MS runtimes beside it (14.51 from another game's prefix).
SRC=$S/steamapps/compatdata/2672470/pfx/drive_c/windows/system32
for f in msvcp140.dll vcruntime140.dll vcruntime140_1.dll; do cp -f "$SRC/$f" "$G/DeusExHRVR/$f"; done
file "$G/DeusExHRVR/"*.dll | sed 's/.*DeusExHRVR\///' | cut -c1-70
echo "== 32-bit runtimes in syswow64"; for f in vcruntime140 msvcp140 msvcp140_2; do printf '%s: ' $f; file "$PFX/drive_c/windows/syswow64/$f.dll" | sed 's/.*: //' | cut -c1-40; done

# Registry: same four values install.ps1 sets, after saving the originals.
python3 -I - "$PFX/user.reg" "$B/graphics-registry-before.txt" <<'PY'
import re, shutil, sys
reg, save = sys.argv[1], sys.argv[2]
key = '[Software\\\\Eidos\\\\Deus Ex: HRDC\\\\Graphics]'
want = {'EnableDirectX11': 1, 'StereoMode': 1, 'EnableVSync': 0, 'AntiAliasingMode': 0}
shutil.copy2(reg, reg + '.bak-deusexhrvr')
t = open(reg, encoding='utf-8', errors='surrogateescape').read()
i = t.find(key)
if i < 0: sys.exit('Graphics key not found: launch the game once first')
end = t.find('\n\n', i); end = len(t) if end < 0 else end
block = t[i:end]
before = []
for name, val in want.items():
    m = re.search(r'^"%s"=dword:([0-9a-f]{8})$' % name, block, re.M)
    before.append(f'{name}={m.group(1) if m else "(absent)"}')
    line = f'"{name}"=dword:{val:08x}'
    block = block.replace(m.group(0), line) if m else block + '\n' + line
open(save, 'w').write('\n'.join(before) + '\n')
open(reg, 'w', encoding='utf-8', errors='surrogateescape').write(t[:i] + block + t[end:])
print('registry set; before:', ', '.join(before))
PY

cat > ~/PCVR/DeusExHRVR/uninstall.sh <<EOF
#!/bin/bash
# Removes DeusExHRVR from DXHR:DC and restores the backed-up files and graphics settings.
G="$G"
rm -f "\$G"/{d3d11.dll,atidxx32.dll,atiadlxy.dll,DeusExHRVR.ini,DeusExHRVR-weapons.ini,DeusExHRVR-camera.log,DeusExHRVR-bob.csv}
rm -rf "\$G/DeusExHRVR" "\$G/DeusExHRVR-captures"
cp -a "\$G/DeusExHRVR-backup/." "\$G/" 2>/dev/null; rm -f "\$G/graphics-registry-before.txt"
cp -f "$PFX/user.reg.bak-deusexhrvr" "$PFX/user.reg"
rm -rf "\$G/DeusExHRVR-backup"
python3 ~/PCVR/bin/steam_eval.py 'SteamClient.Apps.SetAppLaunchOptions(238010, ""), "cleared"'
echo "DeusExHRVR removed"
EOF
chmod +x ~/PCVR/DeusExHRVR/uninstall.sh
echo "INSTALL-DONE"
