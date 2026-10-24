#!/bin/bash
# Author's confirmed headset setup: WorldUnitsPerMetre=300, interaction + walking direction from the headset.
G=$(ls -d ~/.local/share/Steam/steamapps/common/Deus*)
I="$G/DeusExHRVR.ini"
[ -f "$I.bak-wupm100" ] || cp "$I" "$I.bak-wupm100"
sed -i -E 's/^WorldUnitsPerMetre=.*/WorldUnitsPerMetre=300/; s/^InteractionAim=.*/InteractionAim=Headset/; s/^MovementDirection=.*/MovementDirection=Headset/' "$I"
grep -E '^(WorldUnitsPerMetre|InteractionAim|MovementDirection)=' "$I"
