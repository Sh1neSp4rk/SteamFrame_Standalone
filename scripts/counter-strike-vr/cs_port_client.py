#!/usr/bin/env python3
# License note: the replacement source fragments in this file derive from Team-Beef-Studios/CSVR's cs16-client (GPL-3.0),
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""Steam Frame fixes for CSVR's client (cl_dll) on desktop Linux. Idempotent."""
import pathlib, sys

S = pathlib.Path.home() / "PCVR/CSVR/src"
failed = []

def patch(rel, pairs):
    p = S / rel
    s = p.read_text()
    changed = False
    for old, new in pairs:
        if new in s:
            continue
        n = s.count(old)
        if n != 1:
            failed.append(f"{rel}: expected 1 match, found {n}: {old[:70]!r}"); continue
        s = s.replace(old, new); changed = True
    if changed:
        p.write_text(s); print("patched", rel)

patch("cl_dll/StudioModelRenderer.cpp", [
    # C++ headers before cl_util.h's min/max/fabs macros (the NDK's libc++ happened to tolerate the order)
    ("#include <assert.h>\n#include \"hud.h\"\n",
     "#include <assert.h>\n// Steam Frame: standard headers before cl_util.h defines min/max/fabs as macros\n"
     "#include <climits>\n#include <fstream>\n#include <string>\n#include <vector>\n#include <algorithm>\n#include \"hud.h\"\n"),
    # weapon calibration file: Android's fixed /sdcard path -> the game folder (the engine runs from there)
    ("\tchar* calibrationFile = \"/sdcard/xash/cstrike/models/vr_weapons.cfg\";\n",
     "\tconst char* calibrationFile = \"cstrike/models/vr_weapons.cfg\"; // Steam Frame: relative to the game folder\n"),
])

if failed:
    print("FAILED:\n  " + "\n  ".join(failed)); sys.exit(1)
print("client patches applied")
