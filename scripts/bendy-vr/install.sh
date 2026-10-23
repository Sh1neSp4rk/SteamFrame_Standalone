#!/bin/bash
# Waits for Bendy's release-1.5 beta build to finish installing, then installs BendyVR 1.2.2
# by hand (what TeamBeefInstaller.exe does) and sets the Proton launch option for BepInEx.
# Log: ~/PCVR/BendyVR/install.log. Undo: ~/PCVR/BendyVR/uninstall.sh
set -e
S=~/.local/share/Steam
MAN=$S/steamapps/appmanifest_622650.acf
G="$S/steamapps/common/Bendy and the Ink Machine"
M=~/PCVR/BendyVR/extracted/BendyVRInstall/Mod
OLD_BUILD=23764460

for i in $(seq 1 360); do   # up to an hour
  flags=$(grep -m1 '"StateFlags"' "$MAN" | cut -d'"' -f4)
  build=$(grep -m1 '"buildid"' "$MAN" | cut -d'"' -f4)
  if [ "$flags" = 4 ] && [ "$build" != "$OLD_BUILD" ]; then break; fi
  [ $((i % 6)) = 1 ] && echo "$(date +%T) waiting: StateFlags=$flags buildid=$build $(grep -m1 '"BytesDownloaded"' "$MAN" | cut -d'"' -f4)/$(grep -m1 '"BytesToDownload"' "$MAN" | cut -d'"' -f4)"
  sleep 10
done
[ "$flags" = 4 ] && [ "$build" != "$OLD_BUILD" ] || { echo "timed out waiting for the beta build"; exit 1; }
echo "beta build $build installed"

echo "== game build check"
ls "$G"
[ -d "$G/Bendy and the Ink Machine_Data/Managed" ] && echo "Mono build (good)" || { echo "no Managed folder: not the Mono build"; exit 1; }
strings "$G/Bendy and the Ink Machine_Data/globalgamemanagers" | grep -m1 -E '^20[0-9]{2}\.[0-9]' || true

echo "== backing up files the mod replaces"
B=~/PCVR/BendyVR/backup-$build
mkdir -p "$B"
(cd "$M/CopyToGame" && find . -type f) | while read -r f; do
  if [ -e "$G/$f" ]; then mkdir -p "$B/$(dirname "$f")"; cp -a "$G/$f" "$B/$f"; echo "backed up $f"; fi
done

echo "== copying mod files"
cp -a "$M/CopyToGame/." "$G/"
rm -rf "$G/BepInEx"
cp -a "$M/BepInEx" "$G/BepInEx"
rm -f "$G/BepInEx/LogOutput.log"
rm -rf "$G/BepInEx/cache"
# The shipped config points at the developer's own drive; make it relative to the game folder.
printf '[UnityDoorstop]\nenabled=true\ntargetAssembly=BepInEx\\core\\BepInEx.Preloader.dll\nignoreDisableSwitch=true\n' \
  > "$G/doorstop_config.ini"
cat "$G/doorstop_config.ini"

echo "== launch option"
python3 ~/PCVR/bin/steam_eval.py 'SteamClient.Apps.SetAppLaunchOptions(622650, "WINEDLLOVERRIDES=\"winhttp=n,b\" %command%"), "set"'

cat > ~/PCVR/BendyVR/uninstall.sh <<EOF
#!/bin/bash
# Removes BendyVR from the Bendy install and restores replaced files.
G="$G"
rm -rf "\$G/BepInEx" "\$G/winhttp.dll" "\$G/doorstop_config.ini"
rm -f "\$G/Bendy and the Ink Machine_Data/Plugins/"{LIV_Bridge.dll,OVRPlugin.dll,openvr_api.dll,openvr_mod.cfg}
cp -a "$B/." "\$G/" 2>/dev/null || true
python3 ~/PCVR/bin/steam_eval.py 'SteamClient.Apps.SetAppLaunchOptions(622650, ""), "cleared"'
echo "BendyVR removed. Switch the beta back to None in Steam to return to the current build."
EOF
chmod +x ~/PCVR/BendyVR/uninstall.sh
echo "INSTALL-DONE"
