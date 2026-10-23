#!/usr/bin/env python3
"""Deep audit: for every VR shortcut, which Steam game install does it actually use, and how?
  path     = a script/config names steamapps/common/<game> (directly or via a variable assembled from it)
  symlink  = a file/dir in the port's folder is a symlink into steamapps/common/<game> (breaks if Steam uninstalls)
  hardlink = port files share inodes with steamapps/common/<game> (keeps working after uninstall, but frees no space)
  prefix   = runs in the Steam game's Proton prefix (Steam deletes that prefix on uninstall)
Run: python3 vr_audit2.py"""
import glob, os, re, struct, sys, time
home = os.path.expanduser('~'); steam = f'{home}/.local/share/Steam'; common = f'{steam}/steamapps/common'

def parse(b, i=0):
    d = {}
    while True:
        t = b[i]; i += 1
        if t == 8: return d, i
        j = b.index(b'\0', i); k = b[i:j].decode('utf-8', 'replace'); i = j + 1
        if t == 0: d[k], i = parse(b, i)
        elif t == 1: j = b.index(b'\0', i); d[k] = b[i:j].decode('utf-8', 'replace'); i = j + 1
        elif t == 2: d[k] = struct.unpack_from('<I', b, i)[0]; i += 4
        else: raise ValueError(t)

apps = {}
for m in glob.glob(f'{steam}/steamapps/appmanifest_*.acf'):
    t = open(m, errors='replace').read(); g = lambda k: (re.search(rf'"{k}"\s+"([^"]*)"', t) or [None, ''])[1]
    apps[g('appid')] = dict(name=g('name'), dir=g('installdir'), size=int(g('SizeOnDisk') or 0))
dirs = {a['dir'] for a in apps.values()}

sc = {}
for f in glob.glob(f'{steam}/userdata/*/config/shortcuts.vdf'):
    sc.update(parse(open(f, 'rb').read(), 0)[0].get('shortcuts', {}))

TEXT = re.compile(r'\.(sh|py|ini|cfg|txt|json|conf|desktop)$', re.I)
def roots_for(s):
    exe = (s.get('Exe') or s.get('exe') or '').strip('"'); sd = s.get('StartDir', '').strip('"'); lo = s.get('LaunchOptions', '')
    roots, texts = set(), [exe, sd, lo]
    scripts = re.findall(r'(/home/\S+?\.sh)', lo) + ([exe] if exe.endswith('.sh') else [])
    seen = set()
    while scripts:
        w = scripts.pop()
        if w in seen or not os.path.isfile(w): continue
        seen.add(w); t = open(w, errors='replace').read(); texts.append(t)
        roots.add(os.path.dirname(w))
        for m in re.findall(r'(?:\$HOME|~|/home/steamos)(/[^\s"\'$]+\.sh)', t): scripts.append(home + m)
        for m in re.findall(r'D=["\']?(?:\$HOME|~|/home/steamos)(/[^\s"\']+)', t): roots.add(home + m)
    for p in (exe, sd):
        if p.startswith(f'{home}/PCVR/') or '/compatdata/' in p: roots.add(os.path.dirname(p) if os.path.isfile(p) else p)
    # keep port roots at ~/PCVR/<Port> granularity
    norm = set()
    for r in roots:
        m = re.match(rf'({re.escape(home)}/PCVR/[^/]+)', r)
        if m: norm.add(m.group(1))
        elif '/compatdata/' in r: norm.add(r)
        elif r.startswith(home + '/') and not r.startswith(common): norm.add(r)
    return norm, '\n'.join(texts)

results = {}
link_inodes = {}   # (dev, ino) -> set(shortcut names)
for s in sc.values():
    name = s.get('AppName') or s.get('appname') or '?'
    roots, text = roots_for(s)
    deps = {}
    for r in roots:
        for dp, dn, fn in os.walk(r, followlinks=False):
            if '/compatdata/' in dp and ('/windows/' in dp or '/users/' in dp or '/ProgramData' in dp or 'Program Files' in dp): continue
            for e in dn + fn:
                p = os.path.join(dp, e)
                try: st = os.lstat(p)
                except OSError: continue
                if os.path.islink(p):
                    tgt = os.path.realpath(p)
                    if tgt.startswith(common + '/'): deps.setdefault(tgt[len(common)+1:].split('/')[0], set()).add('symlink')
                elif e in fn and st.st_nlink > 1:
                    link_inodes.setdefault((st.st_dev, st.st_ino), set()).add(name)
                if e in fn and TEXT.search(e) and st.st_size < 2_000_000:
                    try: text += '\n' + open(p, errors='replace').read()
                    except OSError: pass
    for d in dirs:
        if re.search(r'common/["\']?' + re.escape(d) + r'(["\'/]|$)', text, re.M) or re.search(r'common\\\\?' + re.escape(d.replace(' ', r'\ ')), text):
            deps.setdefault(d, set()).add('path')
    for a in re.findall(r'compatdata/(\d+)', text):
        if a in apps: deps.setdefault(apps[a]['dir'], set()).add('prefix')
    results[name] = (deps, roots)

# hard links: scan Steam game folders for inodes that port files share
t0 = time.time(); want = set(link_inodes)
if want:
    for d in sorted(dirs):
        for dp, dn, fn in os.walk(os.path.join(common, d)):
            for f in fn:
                try: st = os.lstat(os.path.join(dp, f))
                except OSError: continue
                k = (st.st_dev, st.st_ino)
                if k in want:
                    for n in link_inodes[k]: results[n][0].setdefault(d, set()).add('hardlink')
print(f'(inode scan {time.time()-t0:.0f}s over {len(dirs)} Steam folders)\n')

byname = {a['dir']: (aid, a) for aid, a in apps.items()}
print('=== VR shortcuts -> Steam game they use (how)')
for name in sorted(results, key=str.lower):
    deps, roots = results[name]
    if not deps and not re.search(r'vr\b', name, re.I): continue
    s = '; '.join(f"{byname.get(d, ('?', {'name': d}))[1]['name']} [{'+'.join(sorted(k))}]" for d, k in sorted(deps.items())) or 'none found'
    print(f'{name:34s} {s}')
print('\n=== Steam games used by a VR shortcut')
used = {}
for name, (deps, _) in results.items():
    for d, k in deps.items(): used.setdefault(d, []).append(f"{name} [{'+'.join(sorted(k))}]")
for d, lst in sorted(used.items(), key=lambda x: -byname.get(x[0], ('', {'size': 0}))[1]['size']):
    aid, a = byname.get(d, ('?', {'name': d, 'size': 0}))
    print(f"{a['size']/1e9:5.1f} GB {aid:>8s} {a['name'][:32]:32s} <- {'; '.join(sorted(lst))}")
