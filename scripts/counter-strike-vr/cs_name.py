#!/usr/bin/env python3
"""Write cstrike/frame_name.cfg with the player name, so the multiplayer menu never asks for one (there is no text
keyboard inside OpenXR on the Frame; the Quest build uses Android's). Name = cstrike/frame_name.txt if present,
else the most recent Steam account's persona name, else "Player". Called by csvr-run.sh at every launch."""
import os, re

G = os.path.expanduser("~/PCVR/CSVR/game/cstrike")
name = ""
override = os.path.join(G, "frame_name.txt")
if os.path.exists(override):
    name = open(override, encoding="utf-8", errors="ignore").read().strip()
if not name:
    try:
        v = open(os.path.expanduser("~/.local/share/Steam/config/loginusers.vdf"), encoding="utf-8", errors="ignore").read()
        best = None
        for block in re.findall(r'"\d{17}"\s*\{(.*?)\}', v, re.S):
            pn = re.search(r'"PersonaName"\s*"([^"]*)"', block)
            recent = re.search(r'"MostRecent"\s*"1"', block)
            if pn and (recent or best is None):
                best = pn.group(1)
        name = best or ""
    except OSError:
        pass
name = re.sub(r'[";\\\n\r]', "", name).strip()[:31] or "Player"
if name.lower() == "player":
    name = "FramePlayer"     # mainui treats the stock "Player" as unset and prompts again
open(os.path.join(G, "frame_name.cfg"), "w", encoding="utf-8").write(f'name "{name}"\n')
print("name:", name)
