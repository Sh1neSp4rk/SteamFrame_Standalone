#!/usr/bin/env python3
"""Set Deus Ex HR DC's graphics registry for VR or flat before each launch (called by flatvr-launch.sh deusex).
The game rewrites these on every options save, and DeusExHRVR needs DX11 + StereoMode 1 + VSync off + no AA; flat play
wants the game's own values back (from DeusExHRVR-backup/graphics-registry-before.txt). Edits the prefix's user.reg
inside [Software\\Eidos\\Deus Ex: HRDC\\Graphics] only. usage: dx_mode.py vr|flat"""
import os, re, sys, time

mode = sys.argv[1]
H = os.path.expanduser("~")
REG = f"{H}/.local/share/Steam/steamapps/compatdata/238010/pfx/user.reg"
BACKUP = f"{H}/.local/share/Steam/steamapps/common/Deus Ex Human Revolution Director's Cut/DeusExHRVR-backup/graphics-registry-before.txt"
VR = {"EnableDirectX11": 1, "StereoMode": 1, "EnableVSync": 0, "AntiAliasingMode": 0}
flat = {"EnableDirectX11": 1, "StereoMode": 0, "EnableVSync": 1, "AntiAliasingMode": 5}
try:
    for line in open(BACKUP):
        k, _, v = line.strip().partition("=")
        if k in flat and v:
            flat[k] = int(v, 16)
except OSError:
    pass
want = VR if mode == "vr" else flat

lines = open(REG, encoding="utf-8", errors="surrogateescape").read().split("\n")
head = "[Software\\\\Eidos\\\\Deus Ex: HRDC\\\\Graphics]"
try:
    start = next(i for i, l in enumerate(lines) if l.startswith(head))
except StopIteration:
    print("graphics key not found; game never ran?"); sys.exit(0)
end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
seen = set(); changed = []
for i in range(start + 1, end):
    m = re.match(r'^"([^"]+)"=dword:([0-9a-fA-F]{8})$', lines[i])
    if m and m.group(1) in want:
        seen.add(m.group(1))
        new = f'"{m.group(1)}"=dword:{want[m.group(1)]:08x}'
        if lines[i] != new:
            lines[i] = new; changed.append(m.group(1))
missing = [k for k in want if k not in seen]
blank = end - 1 if lines[end - 1] == "" else end
for k in missing:
    lines.insert(blank, f'"{k}"=dword:{want[k]:08x}'); changed.append(k + "(added)")
if changed:
    tmp = REG + ".tmp"
    open(tmp, "w", encoding="utf-8", errors="surrogateescape").write("\n".join(lines))
    os.replace(tmp, REG)
print(f"{time.strftime('%F %T')} deusex graphics -> {mode}: " + (", ".join(changed) if changed else "already set"))
