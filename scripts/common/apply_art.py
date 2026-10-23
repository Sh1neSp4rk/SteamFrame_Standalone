"""Apply library art from a folder through the Steam client (no restart):
<id>p.png -> capsule (portrait), <id>.png -> header (wide), <id>_hero.png -> hero, <id>_logo.png -> logo.
Usage: python3 apply_art.py <dir>"""
import base64, glob, os, re, sys
sys.path.insert(0, os.path.expanduser("~/PCVR/bin"))
import steam_shortcuts as s

KINDS = [(r"^(\d+)p\.png$", 0, "capsule"), (r"^(\d+)_hero\.png$", 1, "hero"),
         (r"^(\d+)_logo\.png$", 2, "logo"), (r"^(\d+)\.png$", 3, "header")]
for path in sorted(glob.glob(os.path.join(sys.argv[1], "*.png"))):
    name = os.path.basename(path)
    for pat, kind, label in KINDS:
        m = re.match(pat, name)
        if m:
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            r = s.evaluate(f'SteamClient.Apps.SetCustomArtworkForApp({m.group(1)}, "{b64}", "png", {kind}).then(()=>"ok")')
            print(m.group(1), label, r)
            break
