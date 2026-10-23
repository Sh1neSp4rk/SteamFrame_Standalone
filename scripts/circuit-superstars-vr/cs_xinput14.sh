#!/bin/bash
# Rewired loads Wine's xinput1_4 (where Steam Input's pad is controller 0 and ours is #2); Unity's native layer uses
# xinput1_3 (our shim). Serve the framepad shim under every XInput name so only our pad exists for the game.
D=~/PCVR/CircuitSuperstarsVR; G=~/.local/share/Steam/steamapps/common/"Circuit Superstars"
pkill -f '[c]ircuit-superstars.exe' 2>/dev/null; sleep 2
for n in xinput1_4 xinput9_1_0 xinput1_2 xinput1_1; do cp -f ~/PCVR/DuskHDVR/framepad/out/xinput1_3.dll "$G/$n.dll"; done
sed -i 's/xinput1_3=n,b\${WINEDLLOVERRIDES/xinput1_3=n,b;xinput1_4=n,b;xinput9_1_0=n,b;xinput1_2=n,b;xinput1_1=n,b${WINEDLLOVERRIDES/' $D/csvr-shortcut.sh
grep -n WINEDLLOVERRIDES $D/csvr-shortcut.sh | cut -c1-150
bash $D/cs_launch.sh ${1:-75} 2>&1 | grep -E "^t=${1:-75}"
P=~/.local/share/Steam/steamapps/compatdata/1097130/pfx/drive_c/users/steamuser
echo "--- game: pads"; grep -i -E 'Assigned XInput|Joystick connected' "$P/AppData/LocalLow/Square Enix Ltd/circuit-superstars/Player.log" | tail -4 | cut -c1-140
echo "--- shim"; tail -2 $P/framepad.log
echo "--- plugin"; tr -d '\000' < "$G/BepInEx/LogOutput.log" | grep -a 'FrameVR' | head -3 | cut -c1-140
