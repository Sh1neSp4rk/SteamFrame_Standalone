#!/bin/bash
G="$HOME/.local/share/Steam/steamapps/common/Left 4 Dead 2"
E="python3 $HOME/PCVR/bin/steam_eval.py"
grep -E '"StateFlags"|"buildid"' ~/.local/share/Steam/steamapps/appmanifest_550.acf
ls "$G" | head -20
f="$G/left4dead2.exe"
[ -f "$f" ] || { echo "NO left4dead2.exe - not the Windows build"; exit 1; }
python3 -I -c 'import struct,sys;d=open(sys.argv[1],"rb").read(4096);o=struct.unpack_from("<I",d,0x3c)[0];print("exe machine",hex(struct.unpack_from("<H",d,o+4)[0]))' "$f"
ls "$G"/*.dll 2>/dev/null | head
python3 -I ~/PCVR/L4D2VR/l4d2vr_install.py "$G" || exit 1
ls -la "$G/d3d9.dll" "$G/openvr_api.dll" "$G/VR/SteamVRActionManifest/"
$E 'SteamClient.Apps.SetAppLaunchOptions(550, "WINEDLLOVERRIDES=\"d3d9=n,b\" %command% -insecure -dx9 -window -w 1280 -h 720 +mat_motion_blur_percent_of_screen_max 0 +crosshair 0 +mat_queue_mode 0 +mat_vsync 0 +mat_antialias 0 +mat_grain_scale_override 0")'
pgrep -a -f 'hl2.exe|left4dead2' | grep -v -E 'pgrep|bash' | head -3
