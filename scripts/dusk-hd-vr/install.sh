#!/bin/bash
# Installs Dusk_HD_VR 1.0.0 into DUSK's "DLC/DUSK HD" folder for Proton on the Frame, with framepad
# standing in for the ViGEmBus driver, and sets a launch wrapper that starts the HD exe.
set -e
S=~/.local/share/Steam
H="$S/steamapps/common/Dusk/DLC/DUSK HD"
D=~/PCVR/DuskHDVR
X=$D/extracted
[ -f "$H/Dusk.exe" ] || { echo "DUSK HD not found"; exit 1; }
cp -a "$X/." "$H/"
cp -n "$H/BepInEx/plugins/ViGEmClient.dll" "$D/ViGEmClient.dll.orig" 2>/dev/null || true
cp -f "$D/framepad/out/ViGEmClient.dll" "$H/BepInEx/plugins/ViGEmClient.dll"
cp -f "$D/framepad/out/xinput1_3.dll" "$H/xinput1_3.dll"
echo "installed into $H"; ls "$H" | tr '\n' ' '; echo

cat > $D/duskhdvr-launch.sh <<'EOF'
#!/bin/bash
# Steam launch wrapper for Dusk_HD_VR on the Frame: starts DLC/DUSK HD/Dusk.exe instead of classic DUSK,
# loads BepInEx (winhttp) and framepad's xinput1_3 (the virtual pad the mod feeds). Log: last-launch.txt
export WINEDLLOVERRIDES="winhttp=n,b;xinput1_3=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
args=("${@/common\/Dusk\/Dusk.exe/common/Dusk/DLC/DUSK HD/Dusk.exe}")
echo "$(date) ${args[*]}" > "$HOME/PCVR/DuskHDVR/last-launch.txt"
exec "${args[@]}"
EOF
chmod +x $D/duskhdvr-launch.sh
python3 ~/PCVR/bin/steam_eval.py "SteamClient.Apps.SetAppLaunchOptions(519860, '/home/steamos/PCVR/DuskHDVR/duskhdvr-launch.sh %command%'), 'launch option set'"

cat > $D/uninstall.sh <<EOF
#!/bin/bash
# Removes Dusk_HD_VR from DUSK HD (files that came from the zip, plus framepad) and clears the launch option.
H="$H"
cd "$X" && find . -type f | while read -r f; do rm -f "\$H/\$f"; done
rm -rf "\$H/BepInEx" "\$H/xinput1_3.dll" "\$H/winhttp.dll" "\$H/doorstop_config.ini"
python3 ~/PCVR/bin/steam_eval.py 'SteamClient.Apps.SetAppLaunchOptions(519860, ""), "cleared"'
echo "Dusk_HD_VR removed (DUSK stays on Proton; switch back to native in Properties > Compatibility)"
EOF
chmod +x $D/uninstall.sh
