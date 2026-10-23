#!/bin/bash
# Run the Alpine Faction VR Inno installer silently inside Red Faction's prefix (it converts RF.exe to 1.20 NA).
D=~/PCVR/RedFactionVR; G=~/.local/share/Steam/steamapps/common/"Red Faction"; P=~/.local/share/Steam/steamapps/compatdata/20530/pfx
python3 - <<'EOF'
import os
p = os.path.expanduser('~/PCVR/RedFactionVR/rfvr-shortcut.sh'); s = open(p).read()
hook = '''if [ "$mode" = run ]; then
  # replace the launcher exe and its args with the command in $D/run.txt (one argument per line)
  args=(); for a in "$@"; do case "$a" in */AlpineFactionVR.exe) break;; esac; args+=("$a"); done
  mapfile -t cmd < "$D/run.txt"
  exec "${args[@]}" "${cmd[@]}"
fi
exec "$@"
'''
if 'mode" = run' not in s:
    s = s.replace('exec "$@"\n', hook, 1) if s.count('exec "$@"\n') == 1 else s.replace('fi\nexec "$@"\n', 'fi\n' + hook, 1)
    open(p, 'w').write(s); print('run hook added')
EOF
grep -c 'mode" = run' $D/rfvr-shortcut.sh
cp -f "$G/RF.exe" $D/RF.exe.steam-original 2>/dev/null; sha1sum "$G/RF.exe" | cut -c1-40
printf '%s\n' "$D/dl/AlpineFactionVR-1.1beta-VDXR-fix-setup.exe" '/VERYSILENT' '/SUPPRESSMSGBOXES' '/NORESTART' "/DIR=Z:\\home\\steamos\\.local\\share\\Steam\\steamapps\\common\\Red Faction" "/LOG=Z:\\home\\steamos\\PCVR\\RedFactionVR\\inno.log" > $D/run.txt
echo run > $D/mode; rm -f $D/inno.log
bash $D/rf_launch.sh 90 | grep -E '^t=(45|90)' | cut -c1-140
echo play > $D/mode
echo "=== inno log"; tail -30 $D/inno.log 2>/dev/null | tr -d '\r' | cut -c1-200
echo "=== RF.exe now"; sha1sum "$G/RF.exe" | cut -c1-40; ls -la --time-style=+%T "$G"/RF.exe "$G"/*.exe | cut -c25-
echo "=== msgbox"; grep -a -i 'msgbox' $(ls -t $D/logs/*.log | head -1) | head -3 | cut -c1-300
echo "=== new files in game dir"; ls -lat --time-style=+%T "$G" | head -8 | cut -c25-
