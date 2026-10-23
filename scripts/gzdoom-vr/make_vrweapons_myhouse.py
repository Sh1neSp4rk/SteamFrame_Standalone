#!/usr/bin/env python3
"""Build VRWeapons-MyHouse.pk3: a MODELDEF overlay that gives MyHouse's "Smooth*" weapon classes the same
3D HUD models WeaponsForVR.pk3 defines for the stock Doom weapons.

WeaponsForVR binds models to the stock class names (Pistol, Shotgun, ...). myhouse.pk3 replaces those with
SmoothPistol etc. (different class names AND different sprite names), so the models never attach.
This script reads both files and writes a MODELDEF with one static-pose block per Smooth weapon (ready pose
for the gun sprites, first flash pose for the muzzle-flash sprites). Load it after myhouse.pk3.
"""
import os, re, sys, zipfile

G = os.path.expanduser("~/PCVR/GZDoomVR")
OUT = os.path.join(G, "VRWeapons-MyHouse.pk3")

# ---- 1. parse WeaponsForVR MODELDEF into blocks ------------------------------------------------
md = zipfile.ZipFile(os.path.join(G, "WeaponsForVR.pk3")).read("Modeldef.Doom.Weapons.def").decode("utf-8", "ignore")
blocks = []  # (classname, header_lines, [(sprite, frameletter, modelindex, modelframe)])
for m in re.finditer(r"(?is)model\s+(\w+)\s*\{(.*?)\}", md):
    cls, body = m.group(1), m.group(2)
    header, frames = [], []
    for line in body.splitlines():
        for part in re.split(r"\t+|\s{3,}", line.strip()):
            part = part.strip()
            if not part:
                continue
            fm = re.match(r"(?i)frameindex\s+(\w{4})\s+(\S)\s+(\d+)\s+(\d+)", part)
            if fm:
                frames.append((fm.group(1).upper(), fm.group(2).upper(), int(fm.group(3)), int(fm.group(4))))
            elif not part.lower().startswith("frameindex"):
                header.append(part)
    blocks.append((cls.upper(), header, frames))

def block_for(cls, sprite, frame):
    """The WeaponsForVR block (header, frame pairs) that renders stock class `cls` sprite+frame."""
    for bcls, header, frames in blocks:
        if bcls == cls.upper():
            pairs = [(mi, mf) for (s, f, mi, mf) in frames if s == sprite and f == frame]
            if pairs:
                return header, pairs
    return None

# ---- 2. parse myhouse DECORATE: Smooth* weapons, sprites per state label -----------------------
dec = zipfile.ZipFile(os.path.join(G, "myhouse.pk3")).read("DECORATE").decode("utf-8", "ignore")
weapons = {}  # SmoothName -> {"base": StockName, "main": {spr: set(frames)}, "flash": {spr: set(frames)}}
for m in re.finditer(r"(?im)^\s*actor\s+(Smooth\w+)\s*:\s*(\w+)\s+replaces\s+(\w+)", dec):
    name, parent, replaced = m.group(1), m.group(2), m.group(3)
    if parent.lower() == "custominventory":
        continue
    start = dec.find("{", m.end())
    depth, i = 0, start
    while i < len(dec):
        if dec[i] == "{":
            depth += 1
        elif dec[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    body = dec[start:i + 1]
    label, main, flash = "", {}, {}
    for line in body.splitlines():
        s = line.strip()
        lm = re.match(r"^(\w+):\s*$", s)
        if lm:
            label = lm.group(1).lower()
            continue
        sm = re.match(r"^([A-Z0-9]{4})\s+([A-Z\[\]]+)\s+-?\d+", s)
        if sm and sm.group(1) not in ("TNT1",):
            target = flash if "flash" in label else main
            target.setdefault(sm.group(1), set()).update(ch for ch in sm.group(2) if ch.isalpha())
    weapons[name] = {"base": parent, "main": main, "flash": flash}

# stock sprite names used by WeaponsForVR for the ready pose and the first flash pose
STOCK = {
    "Fist":           (("PUNG", "A"), None),
    "Chainsaw":       (("SAWG", "A"), None),
    "Pistol":         (("PISG", "A"), ("PISF", "A")),
    "Shotgun":        (("SHTG", "A"), ("SHTF", "A")),
    "SuperShotgun":   (("SHT2", "A"), None),
    "Chaingun":       (("CHGG", "A"), ("CHGF", "A")),
    "RocketLauncher": (("MISG", "A"), ("MISF", "A")),
    "PlasmaRifle":    (("PLSG", "A"), ("PLSF", "A")),
    "BFG9000":        (("BFGG", "A"), ("BFGF", "A")),
}

out = ["// Generated: WeaponsForVR models re-declared for the Smooth* weapon classes bundled in myhouse.pk3.",
       "// Static ready pose for the gun sprites, first flash pose for the muzzle-flash sprites. Load after myhouse.pk3.", ""]
report = []
for name, w in weapons.items():
    base = w["base"]
    if base not in STOCK:
        report.append(f"skip {name}: base {base} unknown")
        continue
    ready, flashref = STOCK[base]
    for kind, ref, sprites in (("main", ready, w["main"]), ("flash", flashref, w["flash"])):
        if not sprites:
            continue
        if ref is None:
            # no stock flash block (fist/chainsaw/SSG): render those frames with the ready model
            ref = ready
        found = block_for(base, ref[0], ref[1])
        if not found:
            report.append(f"{name}: no WeaponsForVR block for {base} {ref}")
            continue
        header, pairs = found
        out.append(f"Model {name}")
        out.append("{")
        for h in header:
            out.append("   " + h)
        for spr, frs in sorted(sprites.items()):
            for fr in sorted(frs):
                for mi, mf in pairs:
                    out.append(f"   FrameIndex {spr} {fr} {mi} {mf}")
        out.append("}")
        out.append("")
        report.append(f"{name} ({kind}): {', '.join(s + '[' + ''.join(sorted(f)) + ']' for s, f in sorted(sprites.items()))} -> {base} {ref[0]} {ref[1]} ({len(pairs)} model slot(s))")

text = "\n".join(out) + "\n"
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("MODELDEF.txt", text)
print("\n".join(report))
print(f"\nwrote {OUT} ({len(text)} chars of MODELDEF, {text.count('Model ')} blocks)")
if "--show" in sys.argv:
    print(text)
