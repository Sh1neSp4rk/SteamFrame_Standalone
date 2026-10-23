#!/bin/bash
# Points F.E.A.R. (21090) at Proton Experimental ARM64 + the FEAR VR wrapper, then runs the mod's Setup once.
D="$HOME/PCVR/FEARVR"
E="python3 $HOME/PCVR/bin/steam_eval.py"
G="$HOME/.local/share/Steam/steamapps/common/FEAR Ultimate Shooter Edition"
chmod +x "$D/fearvr-launch.sh"
sha256sum "$G/FEAR.exe"
$E 'SteamClient.Apps.SpecifyCompatTool(21090, "proton-experimental-arm64")'
$E "SteamClient.Apps.SetAppLaunchOptions(21090, \"$D/fearvr-launch.sh %command%\")"
echo setup > "$D/mode"
rm -f "$D/setup-result.json"
steam steam://launch/21090/option0 > /dev/null 2>&1 &
for i in $(seq 1 90); do
  [ -s "$D/setup-result.json" ] && break
  sleep 2
done
sleep 3
echo "--- launch"; cat "$D/last-launch.txt"
echo "--- result"; cat "$D/setup-result.json" 2>/dev/null || echo "(no result file)"
echo "--- game dir now"; ls "$G" | grep -i -E 'vr|dxwrapper|d3d9|dinput8|dsound|fear-vr|bridge'
pgrep -a -f 'Setup.exe|FEARVR-Installer' | grep -v pgrep | cut -c1-150
