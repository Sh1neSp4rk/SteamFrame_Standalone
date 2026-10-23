"""Inventory for VR artwork: non-Steam shortcuts (exe, start dir, launch options, art present) and Steam apps
with non-empty launch options (localconfig.vdf), plus which Steam library art is cached for each.
Run on the Frame: python3 -I art_inventory.py"""
import glob, json, os, re, struct, subprocess

HOME = os.path.expanduser("~")
STEAM = f"{HOME}/.local/share/Steam"
ud = glob.glob(f"{STEAM}/userdata/*/config")[0]
grid = f"{ud}/grid"

def read_binary_vdf(data, i=0):
    out = {}
    while True:
        t = data[i]; i += 1
        if t == 8: return out, i
        j = data.index(b"\0", i); key = data[i:j].decode("utf-8", "replace"); i = j + 1
        if t == 0: out[key], i = read_binary_vdf(data, i)
        elif t == 1: j = data.index(b"\0", i); out[key] = data[i:j].decode("utf-8", "replace"); i = j + 1
        elif t == 2: out[key] = struct.unpack_from("<I", data, i)[0]; i += 4
        else: raise ValueError(t)

sc, _ = read_binary_vdf(open(f"{ud}/shortcuts.vdf", "rb").read())
print("=== non-Steam shortcuts")
for k, s in sc.get("shortcuts", {}).items():
    aid = s.get("appid", 0) & 0xFFFFFFFF
    art = sorted(os.path.basename(p).replace(str(aid), "*") for p in glob.glob(f"{grid}/{aid}*"))
    print(json.dumps({"appid": aid, "name": s.get("AppName"), "exe": s.get("Exe"), "opts": s.get("LaunchOptions", "")[:90],
                      "vr": s.get("OpenVR"), "art": art}))

print("=== Steam apps with launch options")
lc = open(f"{ud}/localconfig.vdf", encoding="utf-8", errors="replace").read()
apps = lc[lc.find('"apps"'):]
for m in re.finditer(r'\n\t\t\t\t\t"(\d+)"\n\t\t\t\t\t\{(.*?)\n\t\t\t\t\t\}', apps, re.S):
    aid, body = m.group(1), m.group(2)
    lo = re.search(r'"LaunchOptions"\s+"(.*)"', body)
    if lo and lo.group(1).strip():
        name = ""
        for lib in (STEAM, "/run/media/steamos/External-00"):
            f = f"{lib}/steamapps/appmanifest_{aid}.acf"
            if os.path.exists(f):
                name = re.search(r'"name"\s+"(.*)"', open(f).read()).group(1)
        cache = sorted(os.path.basename(p) for p in glob.glob(f"{STEAM}/appcache/librarycache/{aid}/*"))
        art = sorted(os.path.basename(p) for p in glob.glob(f"{grid}/{aid}*"))
        print(json.dumps({"appid": aid, "name": name, "opts": lo.group(1)[:110], "custom_art": art, "cache": cache[:8]}))
