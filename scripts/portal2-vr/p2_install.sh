#!/bin/bash
# Installs portal2vr-roomscale V0.2.2 over Portal 2 (620) on the Frame, backing up every file it overwrites.
set -e
D="$HOME/PCVR/Portal2VR"
S="$D/x/Simple_P2VR_install_v2_roomscale/P2VR_install"
G="$HOME/.local/share/Steam/steamapps/common/Portal 2"
B="$D/backup-original"
E="python3 $HOME/PCVR/bin/steam_eval.py"
bash ~/PCVR/bin/kill_app.sh 620 > /dev/null 2>&1 || true
cd "$S"
n=0
while IFS= read -r f; do
  f="${f#./}"
  if [ -e "$G/$f" ] && [ ! -e "$B/$f" ]; then mkdir -p "$B/$(dirname "$f")"; cp -p "$G/$f" "$B/$f"; n=$((n+1)); fi
  mkdir -p "$G/$(dirname "$f")"; cp -f "$f" "$G/$f"
done < <(find . -type f)
echo "installed mod files; backed up $n originals to $B"
# The mod's note: the first load hangs building a sound cache; pre-seed it (UpdateSoundCache.cmd does this copy)
mkdir -p "$G/portal2_dlc3/maps/soundcache"
cp -f "$G/portal2/maps/soundcache/_master.cache" "$G/portal2_dlc3/maps/soundcache/" && echo "sound cache seeded"
$E 'SteamClient.Apps.SpecifyCompatTool(620, "proton-experimental-arm64")'
OPTS='-insecure -dx9 -window -novid +mat_motion_blur_percent_of_screen_max 0 +mat_queue_mode 0 +mat_vsync 0 +mat_antialias 0 +mat_grain_scale_override 0 +snd_surround_speakers 5'
$E "SteamClient.Apps.SetAppLaunchOptions(620, \"PROTON_LOG=1 WINEDLLOVERRIDES=d3d9=n,b %command% $OPTS\")"
/opt/steamvr/bin/linuxarm64/vrcmd --set-settings-int steam.app.620/resolutionOverride 1440 | tail -1
grep -A4 'InstalledDepots' ~/.local/share/Steam/steamapps/appmanifest_620.acf | head -6
