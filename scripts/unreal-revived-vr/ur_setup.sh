#!/bin/bash
# Unreal Revived VR: download + verify the 0.9.0 installer, shortcut with its own Proton prefix (run/cmd hooks),
# hard-link mirror of the Steam Unreal Gold at C:\Unreal in that prefix (the installer's first detection spot).
set -e
D=~/PCVR/UnrealRevivedVR; mkdir -p "$D/dl" "$D/logs"; cd "$D/dl"
B=https://github.com/kwstasg/Unreal-Revived/releases/download/UnrealRevived-Setup-0.9.0
[ -s UnrealRevived-Setup-0.9.0.exe ] || curl -sS -L -o UnrealRevived-Setup-0.9.0.exe $B/UnrealRevived-Setup-0.9.0.exe
curl -sS -L -o UnrealRevived-Setup-0.9.0.exe.sha256 $B/UnrealRevived-Setup-0.9.0.exe.sha256
ls -la UnrealRevived-Setup-0.9.0.exe | cut -c25-; cat UnrealRevived-Setup-0.9.0.exe.sha256; echo
want=$(grep -o -E '[0-9a-fA-F]{64}' UnrealRevived-Setup-0.9.0.exe.sha256 | head -1 | tr A-F a-f); got=$(sha256sum UnrealRevived-Setup-0.9.0.exe | cut -d' ' -f1)
[ "$want" = "$got" ] && echo "sha256 OK $got" || { echo "sha256 MISMATCH want $want got $got"; exit 1; }
echo "=== installer type"; file -b UnrealRevived-Setup-0.9.0.exe | cut -c1-100
python3 - UnrealRevived-Setup-0.9.0.exe <<'EOF'
import sys
b = open(sys.argv[1], 'rb').read()
for sig, name in [(b'Inno Setup', 'Inno Setup'), (b'Nullsoft', 'NSIS'), (b'WixBundle', 'WiX bundle'), (b'InstallShield', 'InstallShield'), (b'7-Zip', '7z SFX')]:
    i = b.find(sig)
    if i >= 0: print(' ', name, 'at', i, b[i:i+60].split(b'\0')[0][:60])
EOF
cat > $D/urvr-shortcut.sh <<'EOF'
#!/bin/bash
# "Unreal Revived VR" shortcut wrapper: own Proton prefix (compatdata/<shortcut id>); Unreal Revived installed inside it.
# touch ~/PCVR/UnrealRevivedVR/debug for a Proton log; env.test is sourced if present.
# mode file: play (default) | run (replace the exe+args with $D/run.txt, one argument per line) | cmd (cmd.exe /c $D/cmd.txt)
D="$HOME/PCVR/UnrealRevivedVR"
export STEAM_COMPAT_DATA_PATH="$HOME/.local/share/Steam/steamapps/compatdata/$(cat "$D/appid.txt")"
[ -f "$D/env.test" ] && source "$D/env.test"
[ -e "$D/debug" ] && export PROTON_LOG=1 PROTON_LOG_DIR="$D/logs" WINEDEBUG="${WINEDEBUG:-+loaddll}"
mkdir -p "$D/logs"; echo "$(date) args: $*" >> "$D/last-launch.txt"
mode=$(cat "$D/mode" 2>/dev/null || echo play)
if [ "$mode" != play ]; then
  args=(); for a in "$@"; do case "$a" in *.exe|*.EXE) break;; esac; args+=("$a"); done
  if [ "$mode" = cmd ]; then exec "${args[@]}" "c:\\windows\\system32\\cmd.exe" /c "$(cat "$D/cmd.txt")"; fi
  mapfile -t cmd < "$D/run.txt"; exec "${args[@]}" "${cmd[@]}"
fi
exec "$@"
EOF
chmod +x $D/urvr-shortcut.sh; touch $D/debug
id=$(python3 ~/PCVR/bin/steam_shortcuts.py list | python3 -c 'import json,sys;print(next((a["appid"] for a in json.load(sys.stdin) if a["name"]=="Unreal Revived VR"),""))')
[ -n "$id" ] || id=$(python3 ~/PCVR/bin/steam_shortcuts.py add "Unreal Revived VR" "$D/dl/UnrealRevived-Setup-0.9.0.exe" "$D/dl" | tail -1)
echo "shortcut id: $id"; echo $id > $D/appid.txt
mkdir -p ~/.local/share/Steam/steamapps/compatdata/$id
python3 $HOME/PCVR/bin/steam_eval.py "SteamClient.Apps.SpecifyCompatTool($id, \"proton-experimental-arm64\"); SteamClient.Apps.SetShortcutLaunchOptions($id, \"$D/urvr-shortcut.sh %command%\"); 'ok'" | head -1
# first run creates the prefix: run a no-op cmd
echo 'echo prefix-ready' > $D/cmd.txt; echo cmd > $D/mode
gid=$(python3 ~/PCVR/bin/steam_shortcuts.py gameid $id); (steam "steam://rungameid/$gid" >/dev/null 2>&1 &)
P=~/.local/share/Steam/steamapps/compatdata/$id/pfx/drive_c
for i in $(seq 1 24); do sleep 5; [ -d "$P/windows" ] && [ -z "$(pgrep -f '[c]md.exe')" ] && break; done; sleep 5; echo play > $D/mode
ls $P | tr '\n' ' '; echo
# hard-link mirror of Steam's Unreal Gold at C:\Unreal (same filesystem, no extra space)
S=~/.local/share/Steam/steamapps/common/"Unreal Gold"
rm -rf "$P/Unreal"; cp -al "$S" "$P/Unreal"
ls "$P/Unreal" | tr '\n' ' '; echo; ls "$P/Unreal/System" | grep -i -E '^unreal(\.exe|\.ini)$|^Core|^Engine\.u$' | tr '\n' ' '; echo
du -sh "$S" | cut -f1
