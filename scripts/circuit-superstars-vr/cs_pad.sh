#!/bin/bash
# Give Circuit Superstars VR a virtual gamepad fed by the Frame controllers: FrameVR_CS plugin (SteamVR actions -> ViGEm
# API) + framepad (ViGEmClient.dll stand-in -> shared memory -> uinput_pad Linux pad -> Wine -> Rewired), the Frame
# binding, relaunch. usage: cs_pad.sh [seconds]
D=~/PCVR/CircuitSuperstarsVR; G=~/.local/share/Steam/steamapps/common/"Circuit Superstars"; F=~/PCVR/DuskHDVR
pkill -f '[c]ircuit-superstars.exe' 2>/dev/null; sleep 2
cp -f "$F/extracted/BepInEx/plugins/Nefarius.ViGEm.Client.dll" "$G/BepInEx/plugins/"
cp -f "$F/framepad/out/ViGEmClient.dll" "$G/BepInEx/plugins/"
cp -f "$F/framepad/out/xinput1_3.dll" "$G/"
cp -f "$D/FrameVR_CS.dll" "$G/BepInEx/plugins/"
ls "$G/BepInEx/plugins" "$G/xinput1_3.dll"
python3 - <<'EOF'
import os
p = os.path.expanduser('~/PCVR/CircuitSuperstarsVR/csvr-shortcut.sh'); s = open(p).read()
if 'uinput_pad' not in s:
    s = s.replace('export WINEDLLOVERRIDES="winhttp=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"',
        'export WINEDLLOVERRIDES="winhttp=n,b;xinput1_3=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"\n'
        '# framepad: the plugin\'s virtual Xbox pad -> shared memory -> an idle Linux uinput pad the game can see (exits with the launch)\n'
        'SHM="$STEAM_COMPAT_DATA_PATH/pfx/drive_c/users/steamuser/framepad.shm"\n'
        'UP="$HOME/PCVR/DuskHDVR/framepad/out/uinput_pad"\n'
        '[ -x "$UP" ] && setsid "$UP" $$ "$SHM" > "$D/uinput_pad.log" 2>&1 < /dev/null &\n')
    open(p, 'w').write(s); print('wrapper: framepad + xinput override added')
EOF
grep -n -E 'WINEDLLOVERRIDES|uinput_pad' $D/csvr-shortcut.sh | cut -c1-120
python3 $D/cs_frame_controls.py
bash $D/cs_launch.sh ${1:-75} 2>&1 | grep -E "^t=${1:-75}"
echo "--- plugin / pad lines"; L="$G/BepInEx/LogOutput.log"; tr -d '\000' < "$L" | grep -a -i -E 'FrameVR|vigem|pad|xinput|error' | grep -v -E 'Game Manager' | head -10 | cut -c1-170
cat $D/uinput_pad.log 2>/dev/null | tail -3
P=~/.local/share/Steam/steamapps/compatdata/1097130/pfx/drive_c/users/steamuser; ls -la --time-style=+%T $P/framepad.* 2>/dev/null | cut -c25-; tail -2 $P/framepad.log 2>/dev/null
echo "--- game: pads"; grep -i -E 'Assigned XInput|Joystick connected' "$P/AppData/LocalLow/Square Enix Ltd/circuit-superstars/Player.log" | tail -4 | cut -c1-140
echo "--- vrserver binding"; grep -a 'binding file' ~/.local/share/Steam/logs/vrserver.txt | grep -i circuit | tail -1 | cut -c1-200
